#!/usr/bin/env python3
"""
Create admin user with proper password hash
"""

import sys
sys.path.append('/var/www/portal-anwalts.ai/backend')

from auth_service import AuthService
from database import get_db
from models import User
from sqlalchemy.orm import sessionmaker
import bcrypt

def create_admin_user():
    """Create admin user with proper password hash"""
    
    # Get database session
    db = next(get_db())
    
    # Check if user exists
    existing = db.query(User).filter(User.email == "christopher.klaes@aigenex.de").first()
    if existing:
        print("✅ User already exists, updating password...")
        # Update existing user
        auth = AuthService()
        hashed_password = auth.hash_password("admin123")
        existing.password_hash = hashed_password
        existing.role = "admin"
        existing.is_active = True
        db.commit()
        print("✅ User updated successfully!")
    else:
        print("🔧 Creating new admin user...")
        # Create new user
        auth = AuthService()
        hashed_password = auth.hash_password("admin123")
        
        new_user = User(
            email="christopher.klaes@aigenex.de",
            password_hash=hashed_password,
            first_name="Dr. Markus",
            last_name="Weigl",
            role="admin",
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        print("✅ New admin user created successfully!")
    
    # Test login
    print("🔍 Testing login...")
    auth = AuthService()
    user = db.query(User).filter(User.email == "christopher.klaes@aigenex.de").first()
    if user and auth.verify_password("admin123", user.password_hash):
        print("✅ Login test successful!")
        print(f"   📧 Email: {user.email}")
        print(f"   👤 Name: {user.first_name} {user.last_name}")
        print(f"   🔑 Role: {user.role}")
        print(f"   🔓 Password: admin123")
    else:
        print("❌ Login test failed!")
    
    db.close()

if __name__ == "__main__":
    create_admin_user()