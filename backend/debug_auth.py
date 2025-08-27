#!/usr/bin/env python3
"""
Debug authentication issues in AnwaltsAI
Test database queries and password verification
"""

import asyncio
import asyncpg
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()

async def test_auth_queries():
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/anwalts_ai_db')
    print(f'Testing database connection: {database_url}')
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Test basic connection
        result = await conn.fetchval('SELECT 1')
        print(f'Database connection OK: {result}')
        
        # Check if users table exists and admin user is there
        user_count = await conn.fetchval('SELECT COUNT(*) FROM users')
        print(f'Total users in database: {user_count}')
        
        # Check specific admin user
        admin_user = await conn.fetchrow(
            'SELECT id, email, name, role, is_active, password_hash FROM users WHERE email = $1',
            'admin@anwalts-ai.com'
        )
        
        if admin_user:
            print(f'Admin user found:')
            print(f'   ID: {admin_user["id"]}')
            print(f'   Email: {admin_user["email"]}')  
            print(f'   Name: {admin_user["name"]}')
            print(f'   Role: {admin_user["role"]}')
            print(f'   Active: {admin_user["is_active"]}')
            print(f'   Password hash length: {len(admin_user["password_hash"]) if admin_user["password_hash"] else 0}')
            
            # Test password verification
            test_password = "admin123"
            password_hash = admin_user["password_hash"]
            
            if password_hash:
                try:
                    # Test bcrypt verification
                    is_valid = bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8'))
                    print(f'   Password verification result: {is_valid}')
                except Exception as e:
                    print(f'   Password verification error: {e}')
            else:
                print('   No password hash found!')
        else:
            print('Admin user not found!')
        
        # Test query that matches the actual database.py code
        print('\n--- Testing actual database.py query ---')
        row = await conn.fetchrow(
            """
            SELECT id, email, name, role, password_hash, is_active,
                   created_at, updated_at
            FROM users 
            WHERE email = $1
            """,
            'admin@anwalts-ai.com'
        )
        
        if row:
            print('Query from database.py works:')
            print(f'   Email: {row["email"]}')
            print(f'   Active: {row["is_active"]}')
            print(f'   Has password hash: {bool(row["password_hash"])}')
        else:
            print('Query from database.py failed!')
        
        await conn.close()
        print('Database queries completed successfully')
        
    except Exception as e:
        print(f'Database test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_queries())