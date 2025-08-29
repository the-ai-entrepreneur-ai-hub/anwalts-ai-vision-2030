#!/usr/bin/env python3
"""
Test FastAPI login endpoint with detailed logging
"""

import asyncio
import os
from dotenv import load_dotenv
from database import Database
from auth_service import AuthService
from models import LoginRequest
import logging
import uuid

# Setup detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_fastapi_login_logic():
    print("Testing FastAPI login logic with detailed logging...")
    
    # Initialize services exactly as in main.py
    db = Database()
    await db.connect()
    
    auth_service = AuthService()
    
    try:
        # Simulate the exact login request data
        login_data = LoginRequest(email="admin@anwalts-ai.com", password="admin123")
        
        print(f"Login request: email={login_data.email}")
        
        # Step 1: Get user by email - EXACT copy from main.py
        print("Step 1: Getting user by email...")
        user = await db.get_user_by_email(login_data.email)
        print(f"User found: {user is not None}")
        
        if not user:
            print("ERROR: User not found - this would raise 401 Unauthorized")
            return
        
        # Step 2: Verify password - EXACT copy from main.py  
        print("Step 2: Verifying password...")
        password_valid = auth_service.verify_password(login_data.password, user.password_hash)
        print(f"Password valid: {password_valid}")
        
        if not password_valid:
            print("ERROR: Invalid password - this would raise 401 Unauthorized")
            return
        
        # Step 3: Check if user is active - EXACT copy from main.py
        print("Step 3: Checking if user is active...")
        if not user.is_active:
            print("ERROR: User not active - this would raise 401 Unauthorized")
            return
        
        print("SUCCESS: User is active")
        
        # Step 4: Create JWT token - EXACT copy from main.py
        print("Step 4: Creating JWT token...")
        token = auth_service.create_access_token(data={"sub": str(user.id)})
        print(f"SUCCESS: Token created: {token[:50]}...")
        
        # Step 5: Store session - EXACT copy from main.py
        print("Step 5: Storing session...")
        from cache_service import CacheService
        cache_service = CacheService()
        await cache_service.connect()
        
        session_id = str(uuid.uuid4())
        session_stored = await cache_service.store_session(session_id, str(user.id), expires_in=86400)
        print(f"SUCCESS: Session stored: {session_stored}")
        
        # Step 6: Create response - EXACT copy from main.py
        print("Step 6: Creating response...")
        from models import LoginResponse, UserResponse
        
        response = LoginResponse(
            token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role
            )
        )
        
        print("SUCCESS: Login simulation successful!")
        print(f"Response: {response.dict()}")
        
        await cache_service.disconnect()
        
    except Exception as e:
        print(f"ERROR: Error during login simulation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_fastapi_login_logic())