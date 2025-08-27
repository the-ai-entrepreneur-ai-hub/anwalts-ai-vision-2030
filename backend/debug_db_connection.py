#!/usr/bin/env python3
"""
Debug database connection issues
"""

import asyncio
import os
from dotenv import load_dotenv
from database import Database

load_dotenv()

async def debug_db_connection():
    print("Debugging database connection...")
    
    db = Database()
    print(f"Database URL: {db.database_url}")
    
    try:
        await db.connect()
        print("Database connected successfully")
        
        # Test health check
        health = await db.health_check()
        print(f"Health check: {health}")
        
        # Test getting user
        user = await db.get_user_by_email("admin@anwalts-ai.com")
        print(f"User found: {user is not None}")
        
        if user:
            print(f"User details: {user.email}, {user.name}, {user.role}")
        
        await db.disconnect()
        
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_db_connection())