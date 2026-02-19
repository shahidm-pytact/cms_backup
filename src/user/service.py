"""User service for business logic."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi.responses import Response as FastAPIResponse
from fastapi import status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.repository import UserRepository
from src.user.models import User
from src.audit_logs.utils import create_audit_log, mask_sensitive_value
from src.user.schemas import (
    UserInvite,
    UserUpdate,
    UserStatusUpdate,
    UserListQuery,
    UserRead,
    UserListItem,
    UserPaginatedResponse,
    UserInviteResponse,
    InvitationStatusResponse,
    ResendInviteResponse,
    PasswordResetRequestResponse,
    InvitationStatus,
    RoleInfo,
)
from src.user.exceptions import (
    UserNotFound,
    DuplicateEmail,
    RoleNotFound,
    InactiveRole,
    InvalidStateTransition,
    UserNotActive,
    UserNotInvited,
    InvitationNotFound,
    EmptyRequestBody,
)
from src.user.constants import (
    STATUS_INVITED,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    STATUS_EXPIRED,
    STATUS_CANCELLED,
)
from src.utils import generate_etag, format_last_modified, set_304_response_headers
from src.schemas import AuthContext
from src.auth.utils import generate_invitation_token, generate_password_reset_token
from src.email.service import EmailService
from src.exceptions import PreconditionRequiredError, PreconditionFailedError
import logging


class UserService:
    """Service for user-related business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)
        self.email_service = EmailService()
    
    async def invite_user(
        self,
        data: UserInvite,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> UserInviteResponse:
        """Invite a new user with role assignment.
        
        Creates user with status = invited, generates invitation token,
        and sets invitation expiration (7 days from now).
        
        Args:
            data: User invitation data
            ctx: AuthContext with user information
            
        Returns:
            UserInviteResponse with invitation details
            
        Raises:
            DuplicateEmail: If email already exists
            RoleNotFound: If role ID not found
            InactiveRole: If role is not active
        """
        # Check if email already exists (case-insensitive)
        existing_user = await self.repository.get_by_email(data.email)
        if existing_user:
            raise DuplicateEmail(data.email)
        
        # Check if role exists and is active
        role = await self.repository.get_role_by_id(data.role_id)
        if not role:
            raise RoleNotFound(str(data.role_id))
        
        if role.status != STATUS_ACTIVE:
            raise InactiveRole(str(data.role_id))
        
        # Generate invitation token and expiration (7 days from now)
        invite_token = generate_invitation_token()
        invite_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Create user with status = invited
        user = User(
            email=data.email.lower(),  # Store email in lowercase
            name=data.name,
            role_id=data.role_id,
            status=STATUS_INVITED,
            invite_token=invite_token,
            invite_expires_at=invite_expires_at,
            invited_at=datetime.now(timezone.utc),
            invited_by=ctx.user_id,
            created_by=ctx.user_id,
            updated_by=ctx.user_id,
        )
        
        # Save user
        user = await self.repository.create(user)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
        # Send invitation email asynchronously (failures logged only)
        try:
            await self.email_service.send_invitation_email(
                to_email=user.email,
                to_name=user.name,
                invitation_token=invite_token,
            )
        except Exception as e:
            # Log error but don't fail the invitation creation
            # Email failures logged only via audit logs, no retries
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send invitation email to {user.email}: {str(e)}", exc_info=True)
        
        # Return response
        return UserInviteResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            status=user.status,
            role_id=user.role_id,
            invited_at=user.invited_at,
            invite_expires_at=user.invite_expires_at,
            invited_by=user.invited_by,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    
    async def get_user(
        self,
        user_id: UUID,
        if_none_match: Optional[str] = None,
    ) -> UserRead | FastAPIResponse:
        """Get user details with invitation status and role information.
        
        Args:
            user_id: User ID to retrieve
            if_none_match: ETag from If-None-Match header
            
        Returns:
            UserRead with user details, or FastAPIResponse (304) if unchanged
            
        Raises:
            UserNotFound: If user not found
        """
        # Get user with relationships
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # Generate ETag
        etag = generate_etag(user.updated_at)
        
        # Check If-None-Match header
        if if_none_match and if_none_match == etag:
            response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
            return set_304_response_headers(None, response, etag, user.updated_at)
        
        # Build role info
        role_info = None
        if user.role:
            role_info = RoleInfo(
                id=user.role.id,
                name=user.role.name,
            )
        
        # Build invitation status (only if status is "invited")
        invitation_status = None
        if user.status == STATUS_INVITED:
            is_expired = user.invite_expires_at is not None and user.invite_expires_at < datetime.now(timezone.utc)
            can_resend = is_expired or user.invite_expires_at is None
            
            invitation_status = InvitationStatus(
                invited_at=user.invited_at,
                invite_expires_at=user.invite_expires_at,
                invite_accepted_at=user.invite_accepted_at,
                is_expired=is_expired,
                can_resend=can_resend,
            )
        
        # Build response
        result = UserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            status=user.status,
            role_id=user.role_id,
            role=role_info,
            invitation_status=invitation_status,
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
        
        # Attach ETag for router
        result._etag = etag
        result._last_modified = user.updated_at
        
        return result
    
    async def list_users(
        self,
        query: UserListQuery,
        if_none_match: Optional[str] = None,
    ) -> UserPaginatedResponse | FastAPIResponse:
        """List users with pagination, search, filtering, and sorting.
        
        Args:
            query: Query parameters for filtering and pagination
            if_none_match: ETag from If-None-Match header
            
        Returns:
            UserPaginatedResponse with paginated users, or FastAPIResponse (304) if unchanged
        """
        # Get users from repository
        users, total = await self.repository.list_with_pagination(
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            status=query.status,
            role_id=query.role_id,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
            user_id_filter=None,
        )
        
        # Calculate pagination metadata
        total_pages = (total + query.page_size - 1) // query.page_size if total > 0 else 0
        
        # Build next_page and prev_page URLs (simplified - actual implementation would build full URLs)
        next_page = None
        if query.page < total_pages:
            next_page = f"/v1/users?page={query.page + 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                next_page += f"&status={query.status}"
            if query.role_id:
                next_page += f"&role_id={query.role_id}"
        
        prev_page = None
        if query.page > 1:
            prev_page = f"/v1/users?page={query.page - 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                prev_page += f"&status={query.status}"
            if query.role_id:
                prev_page += f"&role_id={query.role_id}"
        
        # Build response items
        items = [
            UserListItem(
                id=user.id,
                email=user.email,
                name=user.name,
                status=user.status,
                role_id=user.role_id,
                created_at=user.created_at,
            )
            for user in users
        ]
        
        # Generate ETag from latest user updated_at (if any users)
        etag = None
        if users:
            latest_user = max(users, key=lambda u: u.updated_at)
            etag = generate_etag(latest_user.updated_at)
            
            # Check If-None-Match header
            if if_none_match and if_none_match == etag:
                response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
                return set_304_response_headers(None, response, etag, latest_user.updated_at)
        
        # Build paginated response
        result = UserPaginatedResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
        
        # Attach ETag if available
        if etag:
            result._etag = etag
            if users:
                latest_user = max(users, key=lambda u: u.updated_at)
                result._last_modified = latest_user.updated_at
        
        return result
    
    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
        ctx: AuthContext,
        if_match: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> UserRead:
        """Update user information (name, email, role_id).
        
        Supports partial updates - only provided fields are updated.
        Requires If-Match header for concurrency control.
        Note: Status updates should use update_user_status() method.
        
        Args:
            user_id: User ID to update
            data: Update data (partial)
            ctx: AuthContext with user information
            if_match: ETag from If-Match header (required)
            
        Returns:
            UserRead with updated user details
            
        Raises:
            EmptyRequestBody: If no fields provided
            UserNotFound: If user not found
            DuplicateEmail: If email already exists
            RoleNotFound: If role ID not found
            InactiveRole: If role is not active
            PreconditionRequired: If If-Match header missing
            PreconditionFailed: If ETag mismatch
        """
        # Check if at least one field is provided
        if not any([data.name is not None, data.email is not None, data.role_id is not None]):
            raise EmptyRequestBody()
        
        # Get current user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # Capture old values for audit log
        old_email = user.email
        old_name = user.name
        old_role_id = user.role_id
        
        # Validate ETag (If-Match header required)
        current_etag = generate_etag(user.updated_at)
        if not if_match:
            raise PreconditionRequiredError(
                message="If-Match header required for update operations",
                error_code="PRECONDITION_REQUIRED",
                details=[{"field": "If-Match", "issue": "If-Match header is required for update operations"}],
            )
        
        if if_match != current_etag:
            raise PreconditionFailedError(
                message="Resource version mismatch. Please refresh and try again.",
                error_code="PRECONDITION_FAILED",
                details=[{"field": "If-Match", "issue": "ETag mismatch"}],
            )
        
        # Track email change for notification
        email_changed = False
        
        # Update email if provided
        if data.email is not None:
            new_email_lower = data.email.lower()
            # Check if email is actually changing
            if user.email != new_email_lower:
                # Check if email already exists (case-insensitive, excluding current user)
                existing_user = await self.repository.get_by_email(new_email_lower)
                if existing_user and existing_user.id != user_id:
                    raise DuplicateEmail(data.email)
                old_email = user.email
                user.email = new_email_lower
                email_changed = True
        
        # Update name if provided
        if data.name is not None:
            user.name = data.name
        
        # Update role_id if provided
        if data.role_id is not None:
            # Check if role exists and is active
            role = await self.repository.get_role_by_id(data.role_id)
            if not role:
                raise RoleNotFound(str(data.role_id))
            
            if role.status != STATUS_ACTIVE:
                raise InactiveRole(str(data.role_id))
            
            user.role_id = data.role_id
        
        # Update audit fields
        user.updated_by = ctx.user_id
        
        # Save changes
        user = await self.repository.update(user)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
        # Create audit log
        try:
            # Build old_values and new_values for audit log
            old_values = {}
            new_values = {}
            
            if data.email is not None and email_changed:
                old_values["email"] = old_email
                new_values["email"] = user.email
            if data.name is not None:
                old_values["name"] = old_name
                new_values["name"] = user.name
            if data.role_id is not None:
                old_values["role_id"] = str(old_role_id)
                new_values["role_id"] = str(user.role_id)
                # Get role name for description
                role = await self.repository.get_role_by_id(user.role_id)
                if role:
                    old_values["role_name"] = "previous_role"  # We don't store old role name
                    new_values["role_name"] = role.name
            
            if old_values or new_values:  # Only create audit log if something changed
                await create_audit_log(
                    session=self.session,
                    user_id=ctx.user_id,
                    action="update",
                    entity_type="user",
                    entity_id=user.id,
                    old_values=old_values if old_values else None,
                    new_values=new_values if new_values else None,
                    description=f"User '{user.email}' updated",
                    request=request,
                )
                await self.session.commit()
        except Exception as e:
            # Log error but don't fail the update operation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for user update: {str(e)}", exc_info=True)
        
        # Send email change notification if email was changed
        if email_changed and old_email:
            try:
                await self.email_service.send_email_changed_notification(
                    to_email=user.email,  # Send to new email
                    to_name=user.name,
                    old_email=old_email,
                    new_email=user.email,
                )
            except Exception as e:
                # Log error but don't fail the update operation
                # Email failures logged only via audit logs, no retries
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send email change notification to {user.email}: {str(e)}", exc_info=True)
        
        # Build role info
        role_info = None
        if user.role:
            role_info = RoleInfo(
                id=user.role.id,
                name=user.role.name,
            )
        
        # Build response
        result = UserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            status=user.status,
            role_id=user.role_id,
            role=role_info,
            invitation_status=None,  # Not included in update response
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
        
        # Attach ETag for router
        result._etag = generate_etag(user.updated_at)
        result._last_modified = user.updated_at
        
        return result
    
    async def update_user_status(
        self,
        user_id: UUID,
        data: UserStatusUpdate,
        ctx: AuthContext,
        if_match: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> UserRead:
        """Update user status (activate or deactivate).
        
        Args:
            user_id: User ID to update
            data: Status update data (activate or deactivate)
            ctx: AuthContext with user information
            if_match: ETag from If-Match header (required)
            
        Returns:
            UserRead with updated user details
            
        Raises:
            UserNotFound: If user not found
            InvalidStateTransition: If invalid status transition
            PreconditionRequired: If If-Match header missing
            PreconditionFailed: If ETag mismatch
        """
        # Get current user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # Capture old status for audit log
        old_status = user.status
        
        # Validate ETag (If-Match header required)
        current_etag = generate_etag(user.updated_at)
        if not if_match:
            raise PreconditionRequiredError(
                message="If-Match header required for update operations",
                error_code="PRECONDITION_REQUIRED",
                details=[{"field": "If-Match", "issue": "If-Match header is required for update operations"}],
            )
        
        if if_match != current_etag:
            raise PreconditionFailedError(
                message="Resource version mismatch. Please refresh and try again.",
                error_code="PRECONDITION_FAILED",
                details=[{"field": "If-Match", "issue": "ETag mismatch"}],
            )
        
        # Parse status action
        status_action = data.status.lower().strip()
        current_status = user.status.lower()
        
        # Validate and set new status
        if status_action == "activate":
            # Can only activate if role is active
            if user.role and user.role.status != STATUS_ACTIVE:
                raise InvalidStateTransition("Cannot activate user with inactive role")
            # Can transition from "invited" to "active" (after password is set)
            if current_status not in [STATUS_INVITED]:
                raise InvalidStateTransition(f"Cannot transition from {current_status} to active")
            user.status = STATUS_ACTIVE
        elif status_action == "deactivate":
            # Can transition to inactive from active or invited states
            if current_status not in [STATUS_ACTIVE, STATUS_INVITED]:
                raise InvalidStateTransition(f"Cannot transition from {current_status} to inactive")
            user.status = STATUS_INACTIVE
        else:
            raise InvalidStateTransition(f"Invalid status action: {status_action}. Must be 'activate' or 'deactivate'")
        
        # Update audit fields
        user.updated_by = ctx.user_id
        
        # Save changes
        user = await self.repository.update(user)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
        # Create audit log
        try:
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="update_status",
                entity_type="user",
                entity_id=user.id,
                old_values={
                    "status": old_status
                },
                new_values={
                    "status": user.status
                },
                description=f"User '{user.email}' status changed from '{old_status}' to '{user.status}'",
                request=request,
            )
            await self.session.commit()
        except Exception as e:
            # Log error but don't fail the status update operation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for user status update: {str(e)}", exc_info=True)
        
        # Build role info
        role_info = None
        if user.role:
            role_info = RoleInfo(
                id=user.role.id,
                name=user.role.name,
            )
        
        # Build response
        result = UserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            status=user.status,
            role_id=user.role_id,
            role=role_info,
            invitation_status=None,  # Not included in status update response
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
        
        # Attach ETag for router
        result._etag = generate_etag(user.updated_at)
        result._last_modified = user.updated_at
        
        return result
    
    async def get_invitation_status(
        self,
        user_id: UUID,
    ) -> InvitationStatusResponse:
        """Get user invitation status including status, expiry date, and re-invite eligibility.
        
        Args:
            user_id: User ID to get invitation status for
            
        Returns:
            InvitationStatusResponse with invitation details
            
        Raises:
            UserNotFound: If user not found
            InvitationNotFound: If user does not have an invitation
        """
        # Get user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # Check if user has invitation
        if user.status != STATUS_INVITED:
            raise InvitationNotFound(str(user_id))
        
        # Calculate invitation status
        is_expired = user.invite_expires_at is not None and user.invite_expires_at < datetime.now(timezone.utc)
        can_resend = is_expired or user.invite_expires_at is None
        
        # Build response
        return InvitationStatusResponse(
            user_id=user.id,
            email=user.email,
            status=user.status,
            invited_at=user.invited_at,
            invite_expires_at=user.invite_expires_at,
            invite_accepted_at=user.invite_accepted_at,
            is_expired=is_expired,
            can_resend=can_resend,
            invited_by=user.invited_by,
        )
    
    async def resend_invite(
        self,
        user_id: UUID,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> ResendInviteResponse:
        """Resend invitation to user with new token.
        
        Resets invitation token and expiration, sends new invitation email.
        
        Args:
            user_id: User ID to resend invitation for
            ctx: AuthContext with user information
            
        Returns:
            ResendInviteResponse with new invitation details
            
        Raises:
            UserNotFound: If user not found
            UserNotInvited: If user status is not "invited"
            InactiveRole: If user's role is not active
        """
        # Get user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # Capture old values for audit log
        old_invite_expires_at = user.invite_expires_at
        old_status = user.status
        
        # Check if user's role is active
        if not user.role or user.role.status != STATUS_ACTIVE:
            raise InactiveRole(str(user.role_id) if user.role_id else "unknown")
        
        # Note: According to API spec, re-invite is supported from any status
        # But typically used for expired invitations
        # We'll update status to "invited" if needed
        
        # Generate new invitation token and expiration (7 days from now)
        invite_token = generate_invitation_token()
        invite_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Update invitation fields
        user.invite_token = invite_token
        user.invite_expires_at = invite_expires_at
        user.invited_at = datetime.now(timezone.utc)
        user.invited_by = ctx.user_id
        
        # Update status to "invited" if not already
        if user.status != STATUS_INVITED:
            user.status = STATUS_INVITED
        
        # Update audit fields
        user.updated_by = ctx.user_id
        
        # Save changes
        user = await self.repository.update(user)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
        # Create audit log
        try:
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="resend_invite",
                entity_type="user",
                entity_id=user.id,
                old_values={
                    "invite_token": mask_sensitive_value(user.invite_token) if hasattr(user, 'invite_token') else None,
                    "invite_expires_at": old_invite_expires_at.isoformat() if old_invite_expires_at else None,
                    "status": old_status,
                },
                new_values={
                    "invite_token": mask_sensitive_value(invite_token),
                    "invite_expires_at": invite_expires_at.isoformat(),
                    "invited_at": user.invited_at.isoformat() if user.invited_at else None,
                    "status": user.status,
                },
                description=f"Invitation resent to user '{user.email}'",
                request=request,
            )
            await self.session.commit()
        except Exception as e:
            # Log error but don't fail the resend operation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for resend invite: {str(e)}", exc_info=True)
        
        # Send invitation email asynchronously (failures logged only)
        try:
            await self.email_service.send_invitation_email(
                to_email=user.email,
                to_name=user.name,
                invitation_token=invite_token,
            )
        except Exception as e:
            # Log error but don't fail the resend operation
            # Email failures logged only via audit logs, no retries
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send invitation email to {user.email}: {str(e)}", exc_info=True)
        
        # Build response
        return ResendInviteResponse(
            user_id=user.id,
            email=user.email,
            status=user.status,
            invited_at=user.invited_at,
            invite_expires_at=user.invite_expires_at,
            invited_by=user.invited_by,
        )
    
    async def request_password_reset(
        self,
        user_id: UUID,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> PasswordResetRequestResponse:
        """Request password reset for a user (generates reset token and sends email).
        
        This is an admin-initiated password reset, different from the public forgot-password flow.
        
        Args:
            user_id: User ID to request password reset for
            
        Returns:
            PasswordResetRequestResponse with reset token expiration
            
        Raises:
            UserNotFound: If user not found
            UserNotActive: If user status is not "active"
            InactiveRole: If user's role is not active
        """
        # Get user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # Check if user is active
        if user.status != STATUS_ACTIVE:
            raise UserNotActive()
        
        # Check if user's role is active
        if not user.role or user.role.status != STATUS_ACTIVE:
            raise InactiveRole(str(user.role_id) if user.role_id else "unknown")
        
        # Generate password reset token and expiration (24 hours from now)
        reset_token = generate_password_reset_token()
        reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        # Update password reset fields
        user.password_reset_token = reset_token
        user.password_reset_token_expires_at = reset_token_expires_at
        
        # Save changes
        user = await self.repository.update(user)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(user)
        
        # Create audit log
        try:
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="request_password_reset",
                entity_type="user",
                entity_id=user.id,
                old_values={
                    "password_reset_token": None,
                    "password_reset_token_expires_at": None,
                },
                new_values={
                    "password_reset_token": mask_sensitive_value(reset_token),
                    "password_reset_token_expires_at": reset_token_expires_at.isoformat(),
                },
                description=f"Password reset requested for user '{user.email}'",
                request=request,
            )
            await self.session.commit()
        except Exception as e:
            # Log error but don't fail the password reset request
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for password reset request: {str(e)}", exc_info=True)
        
        # Send password reset email asynchronously (failures logged only)
        try:
            await self.email_service.send_password_reset_email(
                to_email=user.email,
                to_name=user.name,
                reset_token=reset_token,
            )
        except Exception as e:
            # Log error but don't fail the password reset request
            # Email failures logged only via audit logs, no retries
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
        
        # Build response
        return PasswordResetRequestResponse(
            user_id=user.id,
            email=user.email,
            password_reset_token_expires_at=user.password_reset_token_expires_at,
        )
