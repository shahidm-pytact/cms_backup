"""Authentication service with business logic."""
import logging
import secrets
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.repository import AuthRepository
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
from src.email.service import EmailService


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = AuthRepository(session)
        self.session = session
        self.email_service = EmailService()
    
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
            "role": str(user.role.slug)
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
        """Login user and return token with user info.
        
        Args:
            login_data: Login request with email and password
            
        Returns:
            LoginResponse with token and user info
        """
        # Authenticate user
        user = await self.authenticate_user(login_data.email, login_data.password)
        
        # Create tokens
        tokens = await self.create_tokens(user)
        
        # Build user info
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            name=user.name,
            role_id=user.role_id,
            role=user.role.slug,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        
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
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
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
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
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
            
            # Commit transaction
            await self.session.commit()
            
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
        # Get user by reset token
        user = await self.repository.get_user_by_reset_token(token)
        
        if not user:
            raise ResetTokenNotFoundError(token)
        
        # Check if expired
        if (
            user.password_reset_token_expires_at
            and user.password_reset_token_expires_at < datetime.now(timezone.utc)
        ):
            raise ResetTokenExpiredError()
        
        # Set new password hash
        user.password = get_password_hash(password_data.password)
        
        # Clear reset token fields
        user.password_reset_token = None
        user.password_reset_token_expires_at = None
        
        # Update user (flush, not commit - service controls commit)
        user = await self.repository.update_user(user)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
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
            role=user.role.slug,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        
        # Build role info
        role_info = RoleInfo(
            id=user.role.id,
            slug=user.role.slug,
            name=user.role.name,
            status=user.role.status,
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
