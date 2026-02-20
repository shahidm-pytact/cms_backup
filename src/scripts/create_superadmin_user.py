"""Script to create a superadmin user for testing and initial setup."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import AsyncSessionLocal, engine
from src.user.models import User
from src.roles.models import Role
from src.audit_logs.models import AuditLog  # Import to resolve User.audit_logs relationship
from src.auth.utils import get_password_hash


async def get_or_create_superadmin_role(session: AsyncSession) -> Role:
    """Get existing superadmin role or create a new one.
    
    Args:
        session: Database session
        
    Returns:
        Superadmin Role model
    """
    # Try to find existing superadmin role
    result = await session.execute(
        select(Role).where(
            Role.slug == "superadmin",
            Role.deleted_at.is_(None)
        )
    )
    role = result.scalar_one_or_none()
    
    if role:
        print(f"✓ Found existing superadmin role: {role.name} (ID: {role.id})")
        return role
    
    # Create new superadmin role
    print("Creating new superadmin role...")
    superadmin_role = Role(
        slug="superadmin",
        name="Super Administrator",
        status="active",
        role_type="superadmin",
        permissions_json={
            "modules": {},
            "system": {}
        }
    )
    session.add(superadmin_role)
    await session.flush()
    await session.refresh(superadmin_role)
    print(f"✓ Created superadmin role: {superadmin_role.name} (ID: {superadmin_role.id})")
    return superadmin_role


async def create_superadmin_user() -> None:
    """Create a superadmin user with the specified credentials."""
    email = "pytact@yopmail.com"
    password = "Admin@123"
    name = "Admin User"
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if user already exists
            result = await session.execute(
                select(User)
                .options(selectinload(User.role))
                .where(
                    User.email == email,
                    User.deleted_at.is_(None)
                )
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠ User with email {email} already exists!")
                print(f"  User ID: {existing_user.id}")
                print(f"  Status: {existing_user.status}")
                print(f"  Role: {existing_user.role.name if existing_user.role else 'None'}")
                
                # Update password and status if needed
                if existing_user.status != "active":
                    existing_user.status = "active"
                    print(f"  Updated status to: active")
                
                if not existing_user.password:
                    existing_user.password = get_password_hash(password)
                    print(f"  Set password")
                
                await session.commit()
                print(f"✓ User updated successfully!")
                return
            
            # Get or create superadmin role
            superadmin_role = await get_or_create_superadmin_role(session)
            
            # Create new user
            print(f"\nCreating user: {email}")
            hashed_password = get_password_hash(password)
            
            new_user = User(
                email=email,
                name=name,
                password=hashed_password,
                role_id=superadmin_role.id,
                status="active"
            )
            
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user, ["role"])
            await session.commit()
            
            print(f"✓ User created successfully!")
            print(f"  User ID: {new_user.id}")
            print(f"  Email: {new_user.email}")
            print(f"  Name: {new_user.name}")
            print(f"  Status: {new_user.status}")
            print(f"  Role: {new_user.role.name if new_user.role else 'None'}")
            print(f"\nYou can now login with:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Error creating user: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("=" * 50)
    print("Create Superadmin User Script")
    print("=" * 50)
    asyncio.run(create_superadmin_user())
