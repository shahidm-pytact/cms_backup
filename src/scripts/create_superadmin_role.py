"""Script to create an Operator role with specific permissions."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import AsyncSessionLocal, engine
from src.roles.models import Role
from src.user.models import User  # Import User to resolve Role relationships
from src.audit_logs.models import AuditLog  # Import AuditLog to resolve User relationships


# superadmin role permissions from permissions.json
SUPERADMIN_PERMISSIONS = {
    "modules": {
        "users": {
            "user": {
                "invite": True,
                "read_all": True,
                "read": True,
                "update": True,
                "delete": True,
                "status": True
            }
        },
        "roles": {
            "role": {
                "create": True,
                "read_all": True,
                "read": True,
                "update_all": True,
                "update": True,
                "delete": True,
                "delete_all": True
            }
        },
        "blogs": {
            "blog": {
                "create": True,
                "read_all": True,
                "read": True,
                "update": True,
                "delete": True
            }
        },
        "audits": {
            "audit": {
                "read": False
            }
        }
    }
}


async def create_superadmin_role() -> None:
    """Create an superadmin role with the specified permissions."""
    slug = "superadmin"
    name = "superadmin"
    
    async with AsyncSessionLocal() as session:
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
                print(f"⚠ Role with slug '{slug}' already exists!")
                print(f"  Role ID: {existing_role.id}")
                print(f"  Name: {existing_role.name}")
                print(f"  Status: {existing_role.status}")
                print(f"  Role Type: {existing_role.role_type}")
                
                updated = False
                # Update permissions if they differ
                if existing_role.permissions_json != SUPERADMIN_PERMISSIONS:
                    existing_role.permissions_json = SUPERADMIN_PERMISSIONS
                    updated = True
                
                # Update role_type if it's not 'superadmin'
                if existing_role.role_type != "superadmin":
                    existing_role.role_type = "superadmin"
                    updated = True
                
                # Update status to active
                if existing_role.status != "active":
                    existing_role.status = "active"
                    updated = True
                
                if updated:
                    await session.commit()
                    print(f"  ✓ Updated role (permissions, role_type, and/or status)")
                else:
                    print(f"  Permissions and role type are already up to date")
                
                print(f"✓ Role information displayed above")
                return
            
            # Create new superadmin role
            print(f"Creating Superadmin role...")
            superadmin_role = Role(
                slug=slug,
                name=name,
                status="active",
                role_type="superadmin",
                permissions_json=SUPERADMIN_PERMISSIONS
            )
            
            session.add(superadmin_role)
            await session.flush()
            await session.refresh(superadmin_role)
            await session.commit()
            
            print(f"✓ superadmin role created successfully!")
            print(f"  Role ID: {superadmin_role.id}")
            print(f"  Slug: {superadmin_role.slug}")
            print(f"  Name: {superadmin_role.name}")
            print(f"  Status: {superadmin_role.status}")
            print(f"  Role Type: {superadmin_role.role_type}")
            print(f"\nPermissions configured:")
            print(f"  - Users: invite, read_all, read, update, delete, status")
            print(f"  - Roles: create, read_all, read, update_all, update, delete, delete_all")
            print(f"  - Blogs: create, read_all, read, update, delete")
            print(f"  - Audits: read (disabled)")
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Error creating role: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("=" * 50)
    print("Create superadmin Role Script")
    print("=" * 50)
    asyncio.run(create_superadmin_role())
