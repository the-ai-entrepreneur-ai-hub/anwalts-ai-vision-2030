#!/usr/bin/env python3
"""
Test authentication logic in isolation
"""

import asyncio
import os
from dotenv import load_dotenv
from database import Database
from auth_service import AuthService

load_dotenv()

async def test_auth_logic():
    print("Testing authentication logic...")
    
    # Initialize services
    db = Database()
    await db.connect()
    
    auth_service = AuthService()
    
    try:
        # Test login flow
        email = "admin@anwalts-ai.com"
        password = "admin123"
        
        print(f"Testing login for: {email}")
        
        # Step 1: Get user by email (same as main.py)
        user = await db.get_user_by_email(email)
        print(f"User found: {user is not None}")
        
        if user:
            print(f"User details:")
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.name}")
            print(f"  Role: {user.role}")
            print(f"  Active: {user.is_active}")
            print(f"  Password hash length: {len(user.password_hash)}")
            
            # Step 2: Verify password (same as main.py)
            print(f"\nTesting password verification...")
            is_password_valid = auth_service.verify_password(password, user.password_hash)
            print(f"Password valid: {is_password_valid}")
            
            # Step 3: Check if user is active (same as main.py)
            print(f"User active: {user.is_active}")
            
            if is_password_valid and user.is_active:
                # Step 4: Create JWT token (same as main.py)
                print(f"\nCreating JWT token...")
                token = auth_service.create_access_token(data={"sub": str(user.id)})
                print(f"Token created: {token[:50]}...")
                
                print(f"\nAuthentication successful!")
            else:
                print(f"\nAuthentication failed: password_valid={is_password_valid}, user_active={user.is_active}")
        else:
            print("User not found!")
        
    except Exception as e:
        print(f"Error during authentication test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_auth_logic())