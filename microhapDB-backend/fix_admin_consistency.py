#!/usr/bin/env python3

import asyncio
from sqlalchemy.future import select
from src.database import AsyncSessionLocal
from src.models import AdminOrcid, User, UserRoleEnum

async def fix_admin_consistency():
    """
    This script ensures consistency between User.role and AdminOrcid table:
    1. All users with role='admin' should have an entry in AdminOrcid
    2. All users with an entry in AdminOrcid should have role='admin'
    """
    async with AsyncSessionLocal() as session:
        print("Starting admin consistency check...")
        
        # Get all users with admin role
        result = await session.execute(select(User).filter(User.role == UserRoleEnum.ADMIN.value))
        admin_users = result.scalars().all()
        print(f"Found {len(admin_users)} users with admin role")
        
        # Get all admin ORCIDs
        result = await session.execute(select(AdminOrcid))
        admin_orcids = result.scalars().all()
        admin_orcid_values = {admin.orcid for admin in admin_orcids}
        print(f"Found {len(admin_orcids)} entries in AdminOrcid table")
        
        # Fix users with admin role but no AdminOrcid entry
        for user in admin_users:
            if user.orcid not in admin_orcid_values:
                print(f"User {user.full_name} has admin role but no AdminOrcid entry - fixing...")
                admin_orcid = AdminOrcid(user_id=user.id, orcid=user.orcid)
                session.add(admin_orcid)
                await session.commit()
        
        # Fix users with AdminOrcid entry but not admin role
        for admin_orcid in admin_orcids:
            if admin_orcid.user_id:
                user = await session.get(User, admin_orcid.user_id)
                if user and user.role != UserRoleEnum.ADMIN.value:
                    print(f"User {user.full_name} has AdminOrcid entry but role is {user.role} - fixing...")
                    user.role = UserRoleEnum.ADMIN.value
                    await session.commit()
        
        print("Admin consistency check completed")

if __name__ == "__main__":
    asyncio.run(fix_admin_consistency()) 