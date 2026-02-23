"""Script to insert roles into the roles table.

This script creates/updates roles with their permissions as defined in the database.
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.database import AsyncSessionLocal, engine
from src.roles.models import Role
from src.user.models import User  # Import User to resolve Role relationships
from src.audit_logs.models import AuditLog  # Import AuditLog to resolve User relationships

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Role configurations matching database structure
ROLES_CONFIG = [
    {
        "slug": "super-admin",
        "name": "superadmin",
        "status": "active",
        "role_type": "superadmin",
        "permissions_json": {
            "modules": {
                "blogs": {
                    "blog": {
                        "read": True,
                        "create": True,
                        "delete": True,
                        "update": True,
                        "read_all": True
                    }
                },
                "roles": {
                    "role": {
                        "read": True,
                        "create": True,
                        "delete": True,
                        "update": True,
                        "read_all": True,
                        "delete_all": True,
                        "update_all": True
                    }
                },
                "users": {
                    "user": {
                        "read": True,
                        "delete": True,
                        "invite": True,
                        "status": True,
                        "update": True,
                        "read_all": True
                    }
                },
                "audits": {
                    "audit": {
                        "read": False
                    }
                }
            }
        }
    },
    {
        "slug": "operator",
        "name": "Operator",
        "status": "active",
        "role_type": "operator",
        "permissions_json": {
            "modules": {
                "blogs": {
                    "blog": {
                        "read": True,
                        "create": True,
                        "update": True,
                        "read_all": True
                    }
                },
                "users": {
                    "user": {
                        "read": True,
                        "update": True
                    }
                }
            }
        }
    }
]


async def insert_role(
    role_config: dict,
    session: AsyncSession,
    created_by: Optional[UUID] = None
) -> tuple[bool, str, Optional[Role]]:
    """Insert or update a role.
    
    Args:
        role_config: Role configuration dictionary
        session: Database session
        created_by: Optional user ID for created_by field
        
    Returns:
        Tuple of (success: bool, message: str, role: Optional[Role])
    """
    slug = role_config["slug"]
    
    try:
        # Check if role already exists
        result = await session.execute(
            select(Role).where(
                Role.slug == slug,
                Role.deleted_at.is_(None)
            )
        )
        existing_role = result.scalar_one_or_none()
        
        if existing_role:
            logger.info(f"Role with slug '{slug}' already exists")
            
            # Check if update is needed
            needs_update = False
            
            if existing_role.name != role_config["name"]:
                existing_role.name = role_config["name"]
                needs_update = True
            
            if existing_role.status != role_config["status"]:
                existing_role.status = role_config["status"]
                needs_update = True
            
            if existing_role.role_type != role_config["role_type"]:
                existing_role.role_type = role_config["role_type"]
                needs_update = True
            
            if existing_role.permissions_json != role_config["permissions_json"]:
                existing_role.permissions_json = role_config["permissions_json"]
                needs_update = True
            
            if needs_update:
                if created_by:
                    existing_role.updated_by = created_by
                await session.commit()
                logger.info(f"✓ Updated role: {slug}")
                return (True, f"Updated existing role: {slug}", existing_role)
            else:
                logger.info(f"⊘ Role '{slug}' is already up to date")
                return (True, f"Skipped (already exists and up to date): {slug}", existing_role)
        
        # Create new role
        logger.info(f"Creating role: {slug}")
        new_role = Role(
            slug=slug,
            name=role_config["name"],
            status=role_config["status"],
            role_type=role_config["role_type"],
            permissions_json=role_config["permissions_json"],
            created_by=created_by,
            updated_by=created_by
        )
        
        session.add(new_role)
        await session.flush()
        await session.refresh(new_role)
        await session.commit()
        
        logger.info(f"✓ Successfully created role: {slug} (ID: {new_role.id})")
        return (True, f"Created successfully: {slug} (ID: {new_role.id})", new_role)
        
    except IntegrityError as e:
        await session.rollback()
        if "slug" in str(e.orig).lower() or "unique constraint" in str(e.orig).lower():
            logger.warning(f"Skipping {slug} - duplicate slug (IntegrityError)")
            return (True, f"Skipped (duplicate slug): {slug}", None)
        else:
            logger.error(f"Integrity error for {slug}: {e}")
            return (False, f"Integrity error: {str(e)}", None)
    except Exception as e:
        await session.rollback()
        logger.error(f"Error inserting role {slug}: {e}", exc_info=True)
        return (False, f"Error: {str(e)}", None)


async def get_migration_user(session: AsyncSession) -> Optional[User]:
    """Get a user for migration (prefer superadmin, fallback to any active user).
    
    Args:
        session: Database session
        
    Returns:
        User model or None
    """
    # Try to find superadmin user
    from src.roles.models import Role
    result = await session.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(
            Role.slug.in_(["super-admin", "superadmin"]),
            User.status == "active",
            User.deleted_at.is_(None)
        )
        .limit(1)
    )
    user = result.scalar_one_or_none()
    
    if user:
        return user
    
    # Fallback to any active user
    result = await session.execute(
        select(User)
        .where(
            User.status == "active",
            User.deleted_at.is_(None)
        )
        .limit(1)
    )
    user = result.scalar_one_or_none()
    
    return user


async def insert_all_roles() -> None:
    """Insert all roles from ROLES_CONFIG."""
    logger.info("=" * 60)
    logger.info("Role Insertion Script")
    logger.info("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Get user for created_by/updated_by fields (optional)
            user = await get_migration_user(session)
            created_by = user.id if user else None
            
            if user:
                logger.info(f"Using user: {user.email} (Role: {user.role.slug if user.role else 'None'})")
            else:
                logger.info("No user found - roles will be created without created_by/updated_by")
            logger.info("")
            
            # Track results
            success_count = 0
            skip_count = 0
            error_count = 0
            results = []
            
            # Process each role
            for idx, role_config in enumerate(ROLES_CONFIG, 1):
                logger.info(f"[{idx}/{len(ROLES_CONFIG)}] Processing: {role_config['slug']}")
                
                success, message, role = await insert_role(
                    role_config,
                    session,
                    created_by=created_by
                )
                
                if success:
                    if "Skipped" in message or "already exists" in message:
                        skip_count += 1
                    else:
                        success_count += 1
                else:
                    error_count += 1
                
                results.append((role_config["slug"], success, message))
                logger.info("")
            
            # Print summary
            logger.info("=" * 60)
            logger.info("Insertion Summary")
            logger.info("=" * 60)
            logger.info(f"Total roles: {len(ROLES_CONFIG)}")
            logger.info(f"✓ Successfully created/updated: {success_count}")
            logger.info(f"⊘ Skipped: {skip_count}")
            logger.info(f"✗ Errors: {error_count}")
            logger.info("")
            
            if error_count > 0:
                logger.info("Failed insertions:")
                for slug, success, message in results:
                    if not success:
                        logger.info(f"  - {slug}: {message}")
            
            logger.info("Detailed results:")
            for slug, success, message in results:
                status = "✓" if success else "✗"
                logger.info(f"  {status} {slug}: {message}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Fatal error during insertion: {e}", exc_info=True)
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(insert_all_roles())
