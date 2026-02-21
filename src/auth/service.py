"""Authentication service with business logic."""
import logging
import secrets
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.repository import AuthRepository
from src.audit_logs.utils import create_audit_log, mask_sensitive_value
from src.auth.utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    generate_invitation_token,
    generate_password_reset_token,
)
from src.auth.exceptions import (
    InvalidCredentialsError,
    InactiveUserError,
    InactiveRoleError,
    InvitationNotFoundError,
    InvitationExpiredError,
    InvitationAlreadyAcceptedError,
    InvitationNotAcceptedError,
    PasswordAlreadySetError,
    ResetTokenNotFoundError,
    ResetTokenExpiredError,
    PasswordValidationError,
    InvalidRequestError,
)
from src.auth.schemas import (
    LoginRequest,
    SetPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    LoginResponse,
    UserInfo,
    InvitationValidateResponse,
    InvitationAcceptResponse,
    SetPasswordResponse,
    ResetPasswordResponse,
    UserContextResponse,
    RoleInfo,
)
from src.auth.config import auth_settings
from src.auth.constants import STATUS_ACTIVE, STATUS_INVITED, TOKEN_TYPE_BEARER
from src.auth.exceptions import InvalidTokenError
from src.user.models import User
from src.roles.models import Role
from src.utils import generate_etag
from src.email_sender.service import EmailService


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = AuthRepository(session)
        self.session = session
        self.email_service = EmailService()

    
    async def google_auth_user(
        self,
        email: str,
        google_id: str
    ) -> User:

        # Get existing user
        user = await self.repository.get_user_by_email(email)

        if not user:
            raise InvalidCredentialsError()

        # User must be active
        if user.status != STATUS_ACTIVE:
            raise InactiveUserError()

        # Role must be active
        if not user.role or user.role.status != STATUS_ACTIVE:
            raise InactiveRoleError()

        # Google ID binding logic
        if user.google_id is None:
            # First time Google login → bind account
            user.google_id = google_id
            user.auth_provider = "google"
            # Flush changes (no commit - service controls commit)
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)

        elif user.google_id != google_id:
            # Someone trying to login with wrong Google account
            raise InvalidCredentialsError()

        return user

    async def create_google_login_token(self, user: User) -> dict:
        """Create JWT token for Google-authenticated user.
        
        Args:
            user: User model with role relationship loaded
            
        Returns:
            Dictionary with access_token, token_type, and expires_in
        """
        if not user.role:
            raise Exception("Role not loaded")

        jti = f"jwt_{secrets.token_urlsafe(16)}"

        token_data = {
            "sub": str(user.id),
            "role_id": str(user.role_id),
            "role": user.role.slug if user.role else None,
        }

        access_token = create_access_token(
            data=token_data,
            jti=jti,
        )

        return {
            "access_token": access_token,
            "token_type": TOKEN_TYPE_BEARER,
            "expires_in": auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    
    async def google_login(
        self,
        email: str,
        google_id: str,
        request: Optional[Request] = None,
    ) -> dict:
        """Handle Google authentication and return tokens.
        
        Args:
            email: User email from Google token
            google_id: Google user ID (sub claim)
            request: FastAPI Request object for audit logs
            
        Returns:
            Dictionary with access_token, token_type, and expires_in
            
        Raises:
            InvalidCredentialsError: If user not found or Google account mismatch
            InactiveUserError: If user is not active
            InactiveRoleError: If user's role is not active
        """
        # Authenticate and bind Google account
        user = await self.google_auth_user(email, google_id)
        
        # Create tokens
        tokens = await self.create_google_login_token(user)
        
        # Create audit log for Google authentication (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=user.id,
                action="google_login",
                entity_type="user",
                entity_id=str(user.id),
                old_values=None,
                new_values={
                    "email": email,
                    "google_id": google_id,
                    "token_type": tokens.get("token_type"),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
                description=f"Google authentication successful for user '{email}'",
                request=request,
            )
        except Exception as e:
            # Log error but don't fail the authentication
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for Google login: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both user update (if any) and audit log
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            # Don't fail authentication if commit fails - tokens are already created
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to commit audit log for Google login", exc_info=True)
        
        return tokens
    
    async def generate_oauth2_token(
        self,
        username: str,
        password: str,
        request: Optional[Request] = None,
    ) -> dict:
        """Generate OAuth2-compatible token for Swagger UI.
        
        Handles authentication, token generation, audit logging, and error logging.
        All exceptions are logged appropriately before being re-raised.
        
        Args:
            username: Email address (OAuth2 uses 'username' but we treat it as email)
            password: Plain text password
            request: FastAPI Request object for audit logs
            
        Returns:
            Dictionary with access_token, token_type, and expires_in (OAuth2-compatible format)
            
        Raises:
            InvalidCredentialsError: If credentials are invalid (logged)
            InactiveUserError: If user is not active (logged)
            InactiveRoleError: If user's role is not active (logged)
            Exception: Any unexpected error (logged)
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Authenticate user
            user = await self.authenticate_user(username, password)
            
            # Create tokens
            tokens = await self.create_tokens(user)
            
            # Create audit log for token generation (flush only, no commit)
            try:
                await create_audit_log(
                    session=self.session,
                    user_id=user.id,
                    action="token_generated",
                    entity_type="user",
                    entity_id=str(user.id),
                    old_values=None,
                    new_values={
                        "email": username,  # username is actually email in OAuth2
                        "token_type": tokens["token_type"],
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    description=f"OAuth2 token generated for user '{username}'",
                    request=request,
                )
            except Exception as e:
                # Log error but don't fail the token generation
                logger.error(f"Failed to create audit log for token generation: {str(e)}", exc_info=True)
                # Don't rollback here - will rollback in main commit if needed
            
            # Single commit for audit log
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                # Don't fail token generation if commit fails - tokens are already created
                logger.error(f"Failed to commit audit log for token generation", exc_info=True)
            
            return tokens
            
        except InvalidCredentialsError as e:
            # Log specific error for debugging while maintaining security
            logger.warning(
                f"Invalid credentials attempt for username: {username}",
                extra={"error_code": e.error_code, "username": username}
            )
            # Re-raise for router to handle HTTP formatting
            raise
            
        except InactiveUserError as e:
            # Log specific error for debugging while maintaining security
            logger.warning(
                f"Inactive user attempt for username: {username}",
                extra={"error_code": e.error_code, "username": username, "message": e.message}
            )
            # Re-raise for router to handle HTTP formatting
            raise
            
        except InactiveRoleError as e:
            # Log specific error for debugging while maintaining security
            logger.warning(
                f"Inactive role attempt for username: {username}",
                extra={"error_code": e.error_code, "username": username, "message": e.message}
            )
            # Re-raise for router to handle HTTP formatting
            raise
            
        except Exception as e:
            # Log unexpected exceptions with full details for debugging
            logger.error(
                f"Unexpected error during token generation for username: {username}",
                exc_info=True,
                extra={"error_type": type(e).__name__, "username": username}
            )
            # Re-raise for router to handle HTTP formatting
            raise
    
    async def logout(
        self,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> None:
        """Handle user logout and create audit log.
        
        Args:
            user_id: ID of the user logging out
            request: FastAPI Request object for audit logs
        """
        # Create audit log for logout (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=user_id,
                action="logout",
                entity_type="user",
                entity_id=str(user_id),
                old_values=None,
                new_values={
                    "logout_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                description=f"User logged out",
                request=request,
            )
        except Exception as e:
            # Log error but don't fail logout if audit log fails
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for logout: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for audit log
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            # Don't fail logout if commit fails
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to commit audit log for logout", exc_info=True)
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password.
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            Authenticated User model
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            InactiveUserError: If user is not active
            InactiveRoleError: If user's role is not active
        """
        # Get user by email
        user = await self.repository.get_user_by_email(email)
        
        if not user:
            raise InvalidCredentialsError()
        
        # Verify password
        if not user.password or not verify_password(password, user.password):
            raise InvalidCredentialsError()
        
        # Check user status
        if user.status != STATUS_ACTIVE:
            raise InactiveUserError()
        
        # Check role status (eager loaded)
        if not user.role or user.role.status != STATUS_ACTIVE:
            raise InactiveRoleError()
        
        return user
    
    async def create_tokens(self, user: User) -> dict:
        """Create JWT access token for user.
        
        Args:
            user: User model with role relationship loaded
            
        Returns:
            Dictionary with access_token, token_type, and expires_in
        """
        # Generate JWT ID for token revocation
        jti = f"jwt_{secrets.token_urlsafe(16)}"
        
        # Create token payload
        token_data = {
            "sub": str(user.id),
            "role_id": str(user.role_id),
            "role": str(user.role.slug) if user.role else None
        }
        
        # Create access token
        access_token = create_access_token(
            data=token_data,
            jti=jti,
        )
        
        return {
            "access_token": access_token,
            "token_type": TOKEN_TYPE_BEARER,
            "expires_in": auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        }
    
    async def login(self, login_data: LoginRequest) -> LoginResponse:
        """Login user and return token with user info."""

        # Authenticate user
        user = await self.authenticate_user(
            login_data.email,
            login_data.password,
        )

        # Create tokens
        tokens = await self.create_tokens(user)

        # Build user info
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            name=user.name,
            role_id=user.role_id,
            role=user.role.slug if user.role else None,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        # Create audit log (never break login flow)
        try:
            await create_audit_log(
                session=self.session,
                user_id=user.id,
                action="login",
                entity_type="user",
                entity_id=str(user.id),
                old_values=None,
                new_values={
                    "email": user.email,
                    "login_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                description=f"User '{user.email}' logged in successfully",
                request=None,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(
                f"Audit log failed during login: {str(e)}",
                exc_info=True,
            )
            # Don't rollback here - will rollback in main commit if needed

        # Single commit for audit log
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            # Don't fail login if commit fails
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to commit audit log for login", exc_info=True)

        return LoginResponse(
            access_token=tokens["access_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=user_info,
        )

    
    async def validate_invitation_token(self, token: str) -> InvitationValidateResponse:
        """Validate invitation token and return invitation status.
        
        Args:
            token: Invitation token
            
        Returns:
            InvitationValidateResponse with validation details
            
        Raises:
            InvitationNotFoundError: If token not found
            InvitationExpiredError: If token expired
            InvitationAlreadyAcceptedError: If invitation already accepted
        """
        # Get user by invitation token
        user = await self.repository.get_user_by_invite_token(token)
        
        if not user:
            raise InvitationNotFoundError(token)
        
        # Check if expired
        if user.invite_expires_at and user.invite_expires_at < datetime.now(timezone.utc):
            raise InvitationExpiredError()
        
        # Check if already accepted (user status is not "invited")
        if user.status != STATUS_INVITED:
            raise InvitationAlreadyAcceptedError()
        
        return InvitationValidateResponse(
            valid=True,
            user_id=user.id,
            email=user.email,
            status=user.status,
            invite_expires_at=user.invite_expires_at or datetime.now(timezone.utc),
            is_expired=False,
        )
    
    async def accept_invitation(self, token: str) -> InvitationAcceptResponse:
        """Accept invitation (validate token and mark as accepted).
        
        Args:
            token: Invitation token
            
        Returns:
            InvitationAcceptResponse with acceptance details
            
        Raises:
            InvitationNotFoundError: If token not found
            InvitationExpiredError: If token expired
            InvitationAlreadyAcceptedError: If invitation already accepted
        """
        # Validate invitation token
        validation = await self.validate_invitation_token(token)
        
        # Get user
        user = await self.repository.get_user_by_invite_token(token)
        if not user:
            raise InvitationNotFoundError(token)
        
        # Update invite_accepted_at
        user.invite_accepted_at = datetime.now(timezone.utc)
        
        # Update user (flush, not commit - service controls commit)
        user = await self.repository.update_user(user)
        
        # Create audit log for invitation acceptance (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=user.id,
                action="accept_invitation",
                entity_type="user",
                entity_id=str(user.id),
                old_values=None,
                new_values={
                    "invite_token": token,
                    "accepted_at": user.invite_accepted_at.isoformat(),
                },
                description=f"User '{user.email}' accepted invitation",
                request=None,
            )
        except Exception as e:
            # Log error but don't fail the invitation acceptance
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for invitation acceptance: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both user update and audit log
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except Exception:
            await self.session.rollback()
            raise
        
        return InvitationAcceptResponse(
            user_id=user.id,
            email=user.email,
            status=user.status,
            invite_accepted_at=user.invite_accepted_at,
            can_set_password=True,
        )
    
    async def set_password_from_invitation(
        self, token: str, password_data: SetPasswordRequest
    ) -> SetPasswordResponse:
        """Set initial password after accepting invitation.
        
        Args:
            token: Invitation token
            password_data: Password and confirmation
            
        Returns:
            SetPasswordResponse with password set details
            
        Raises:
            InvitationNotFoundError: If token not found
            InvitationExpiredError: If token expired
            InvitationNotAcceptedError: If invitation not accepted
            PasswordAlreadySetError: If password already set
            PasswordValidationError: If password validation fails
        """
        # Get user by invitation token
        user = await self.repository.get_user_by_invite_token(token)
        
        if not user:
            raise InvitationNotFoundError(token)
        
        # Check if expired
        if user.invite_expires_at and user.invite_expires_at < datetime.now(timezone.utc):
            raise InvitationExpiredError()
        
        # Check if invitation was accepted
        if not user.invite_accepted_at:
            raise InvitationNotAcceptedError()
        
        # Check if password already set
        if user.password:
            raise PasswordAlreadySetError()
        
        # Set password hash
        user.password = get_password_hash(password_data.password)
        
        # Update user status from "invited" to "active"
        user.status = STATUS_ACTIVE
        
        # Clear invitation fields
        user.invite_token = None
        user.invite_expires_at = None
        
        # Set invite_accepted_at if not already set
        if not user.invite_accepted_at:
            user.invite_accepted_at = datetime.now(timezone.utc)
        
        # Update user (flush, not commit - service controls commit)
        user = await self.repository.update_user(user)
        
        # Create audit log for password set from invitation (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=user.id,
                action="set_password_from_invitation",
                entity_type="user",
                entity_id=str(user.id),
                old_values=None,
                new_values={
                    "invite_token": token,
                    "password_set_at": datetime.now(timezone.utc).isoformat(),
                },
                description=f"User '{user.email}' set password from invitation",
                request=None,
            )
        except Exception as e:
            # Log error but don't fail the password set operation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for password set from invitation: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both user update and audit log
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except Exception:
            await self.session.rollback()
            raise
        
        # Send welcome email asynchronously (failures logged only)
        try:
            await self.email_service.send_welcome_email(
                to_email=user.email,
                to_name=user.name or "User",
            )
        except Exception as e:
            # Log error but don't fail the password set operation
            # Email failures logged only via audit logs, no retries
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}", exc_info=True)
        
        return SetPasswordResponse(
            user_id=user.id,
            email=user.email,
            status=user.status,
            password_set_at=datetime.now(timezone.utc),
        )
    
    async def request_password_reset(self, reset_data: ResetPasswordRequest) -> None:
        """Request password reset (generate reset token and send email).
        
        Args:
            reset_data: Reset password request with email
            
        Note:
            Always returns success (does not disclose whether user exists).
            If user exists and is active, generates reset token.
            Email sending is asynchronous (failures logged only).
        """
        # Get user by email
        user = await self.repository.get_user_by_email(reset_data.email)
        
        # If user exists and is active, generate reset token
        if user and user.status == STATUS_ACTIVE:
            # Generate reset token
            reset_token = generate_password_reset_token()
            
            # Set reset token and expiry
            user.password_reset_token = reset_token
            user.password_reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
                hours=auth_settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
            )
            
            # Update user (flush, not commit - service controls commit)
            user = await self.repository.update_user(user)
            
            # Create audit log for password reset request (flush only, no commit)
            try:
                await create_audit_log(
                    session=self.session,
                    user_id=user.id,
                    action="request_password_reset",
                    entity_type="user",
                    entity_id=str(user.id),
                    old_values=None,
                    new_values={
                        "reset_token": reset_token,
                        "requested_at": datetime.now(timezone.utc).isoformat(),
                    },
                    description=f"User '{user.email}' requested password reset",
                    request=None,
                )
            except Exception as e:
                # Log error but don't fail the password reset request
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create audit log for password reset request: {str(e)}", exc_info=True)
                # Don't rollback here - will rollback in main commit if needed
            
            # Single commit for both user update and audit log
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                raise
            
            # Send password reset email asynchronously (failures logged only)
            try:
                await self.email_service.send_password_reset_email(
                    to_email=user.email,
                    to_name=user.name or "User",
                    reset_token=reset_token,
                )
            except Exception as e:
                # Log error but don't fail the password reset request
                # Email failures logged only via audit logs, no retries
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
    
    async def reset_password(
        self, token: str, password_data: SetPasswordRequest
    ) -> ResetPasswordResponse:
        """Reset user password using reset token.
        
        This method ensures tokens are single-use by:
        1. Locking the row with FOR UPDATE to prevent concurrent access
        2. Invalidating the token immediately after validation
        3. Only then proceeding with password update
        
        Args:
            token: Password reset token
            password_data: Password and confirmation
            
        Returns:
            ResetPasswordResponse with reset details
            
        Raises:
            ResetTokenNotFoundError: If token not found
            ResetTokenExpiredError: If token expired
            PasswordValidationError: If password validation fails
        """
        # Get user by reset token with row lock (prevents concurrent token reuse)
        user = await self.repository.get_user_by_reset_token_for_update(token)
        
        if not user:
            raise ResetTokenNotFoundError(token)
        
        # Check if expired
        if (
            user.password_reset_token_expires_at
            and user.password_reset_token_expires_at < datetime.now(timezone.utc)
        ):
            raise ResetTokenExpiredError()
        
        # CRITICAL: Invalidate token IMMEDIATELY after validation to prevent reuse
        # This happens before password update to ensure token is single-use
        await self.repository.invalidate_reset_token(user)
        
        # Set new password hash
        user.password = get_password_hash(password_data.password)
        
        # Token is already cleared by invalidate_reset_token above
        # This ensures atomic invalidation even if password update fails
        
        # Update user (flush, not commit - service controls commit)
        user = await self.repository.update_user(user)
        
        # Create audit log for password reset completion (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=user.id,
                action="reset_password",
                entity_type="user",
                entity_id=str(user.id),
                old_values=None,
                new_values={
                    "reset_token": token,
                    "password_reset_at": datetime.now(timezone.utc).isoformat(),
                },
                description=f"User '{user.email}' reset password",
                request=None,
            )
        except Exception as e:
            # Log error but don't fail the password reset operation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for password reset: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both user update and audit log
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except Exception:
            await self.session.rollback()
            raise
        
        # Send password change confirmation email asynchronously (failures logged only)
        try:
            await self.email_service.send_password_changed_email(
                to_email=user.email,
                to_name=user.name or "User",
            )
        except Exception as e:
            # Log error but don't fail the password reset operation
            # Email failures logged only via audit logs, no retries
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send password changed email to {user.email}: {str(e)}", exc_info=True)
        
        return ResetPasswordResponse(
            user_id=user.id,
            email=user.email,
            password_reset_at=datetime.now(timezone.utc),
        )
    
    async def get_user_context(self, user_id: UUID) -> UserContextResponse:
        """Get current user's context.
        
        Args:
            user_id: User UUID from JWT token
            
        Returns:
            UserContextResponse with user and role
            
        Raises:
            InvalidTokenError: If user not found
        """
        # Get user by ID
        user = await self.repository.get_user_by_id(user_id)
        
        if not user or not user.role:
            raise InvalidTokenError()
        
        # Build user info
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            name=user.name,
            role_id=user.role_id,
            role=user.role.slug if user.role else None,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        
        # Build role info
        role_info = RoleInfo(
            id=user.role.id if user.role else None,
            slug=user.role.slug if user.role else None,
            name=user.role.name if user.role else None,
            status=user.role.status if user.role else None,
        )
        
        # Build response with ETag support
        response = UserContextResponse(
            user=user_info,
            role=role_info,
        )
        
        # Attach ETag for conditional GET
        response._etag = generate_etag(user.updated_at)
        response._last_modified = user.updated_at
        
        return response
