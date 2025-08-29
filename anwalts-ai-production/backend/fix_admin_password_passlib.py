#!/usr/bin/env python3
"""
Fix admin user password hash using passlib (same as auth_service)
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

async def fix_admin_password_passlib():
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/anwalts_ai_db')
    
    # Use same password context as auth_service
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=12
    )
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Generate correct password hash for "admin123" using passlib
        password = "admin123"
        password_hash = pwd_context.hash(password)
        
        print(f'Generated password hash with passlib: {password_hash}')
        
        # Update admin user with correct password hash
        result = await conn.execute(
            """
            UPDATE users 
            SET password_hash = $1 
            WHERE email = $2
            """,
            password_hash, 'admin@anwalts-ai.com'
        )
        
        print(f'Updated admin password: {result}')
        
        # Verify the update
        updated_user = await conn.fetchrow(
            'SELECT email, password_hash FROM users WHERE email = $1',
            'admin@anwalts-ai.com'
        )
        
        if updated_user:
            # Test password verification with passlib
            is_valid = pwd_context.verify(password, updated_user['password_hash'])
            print(f'Password verification test with passlib: {is_valid}')
        
        await conn.close()
        print('Admin password fixed successfully with passlib!')
        
    except Exception as e:
        print(f'Error fixing admin password: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_admin_password_passlib())