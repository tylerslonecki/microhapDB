#!/usr/bin/env python3

import asyncio
from sqlalchemy.future import select
from src.database import AsyncSessionLocal
from src.models import AdminOrcid, User

async def add_admin_orcid():
    async with AsyncSessionLocal() as session:
        # Get all users with admin role
        result = await session.execute(select(User).filter(User.role == 'admin'))
        admin_users = result.scalars().all()
        
        if not admin_users:
            print("No users with admin role found")
            return
        
        print(f"Found {len(admin_users)} users with admin role")
        
        # For each admin user, ensure they have an entry in admin_orcids
        for user in admin_users:
            # Check if the user already has an admin_orcid entry
            result = await session.execute(select(AdminOrcid).filter(AdminOrcid.orcid == user.orcid))
            existing_admin_orcid = result.scalar_one_or_none()
            
            if existing_admin_orcid:
                print(f"User {user.full_name} already has an admin ORCID entry")
                continue
            
            # Add the user's ORCID to the admin_orcids table
            admin_orcid = AdminOrcid(user_id=user.id, orcid=user.orcid)
            session.add(admin_orcid)
            await session.commit()
            print(f"Added admin ORCID for user {user.full_name} with ORCID {user.orcid}")

if __name__ == "__main__":
    asyncio.run(add_admin_orcid()) 