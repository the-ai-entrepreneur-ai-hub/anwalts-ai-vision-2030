#!/usr/bin/env python3
"""
Check and create default users for AnwaltsAI
"""

import sqlite3
import hashlib
import os
from pathlib import Path

def check_and_create_users():
    """Check existing users and create defaults if needed"""
    print("🔐 AnwaltsAI - User Account Check")
    print("=" * 40)
    
    # Find database file
    db_paths = [
        "anwalts_ai.db",
        "backend/anwalts_ai.db",
        "law-firm-ai/anwalts_ai.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No database file found")
        print("Creating new database with default users...")
        db_path = "anwalts_ai.db"
        create_database_and_users(db_path)
        return
    
    print(f"📁 Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if not cursor.fetchone():
            print("⚠️ Users table doesn't exist. Creating...")
            create_users_table(cursor)
            conn.commit()
        
        # Check existing users
        cursor.execute("SELECT email, name, role FROM users")
        users = cursor.fetchall()
        
        if users:
            print(f"✅ Found {len(users)} existing users:")
            for email, name, role in users:
                print(f"   - {email} ({name}) - {role}")
        else:
            print("⚠️ No users found. Creating default users...")
            create_default_users(cursor)
            conn.commit()
            
            # Show created users
            cursor.execute("SELECT email, name, role FROM users")
            users = cursor.fetchall()
            print(f"✅ Created {len(users)} default users:")
            for email, name, role in users:
                print(f"   - {email} ({name}) - {role}")
        
        conn.close()
        
        print("\n🎯 DEFAULT LOGIN CREDENTIALS:")
        print("=" * 40)
        print("Email: admin@anwalts-ai.com")
        print("Password: admin123")
        print("\nOR")
        print("Email: test@anwalts-ai.com") 
        print("Password: test123")
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def create_database_and_users(db_path):
    """Create new database with users table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    create_users_table(cursor)
    create_default_users(cursor)
    
    conn.commit()
    conn.close()
    print(f"✅ New database created: {db_path}")

def create_users_table(cursor):
    """Create users table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'assistant',
            password_hash TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_default_users(cursor):
    """Create default users with simple password hashing"""
    import uuid
    
    # Simple password hashing (for demo purposes)
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    default_users = [
        {
            "id": str(uuid.uuid4()),
            "email": "admin@anwalts-ai.com",
            "name": "Administrator",
            "role": "admin", 
            "password": "admin123"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "test@anwalts-ai.com",
            "name": "Test User",
            "role": "assistant",
            "password": "test123"
        }
    ]
    
    for user in default_users:
        cursor.execute("""
            INSERT OR IGNORE INTO users 
            (id, email, name, role, password_hash, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user["id"],
            user["email"], 
            user["name"],
            user["role"],
            hash_password(user["password"]),
            True
        ))

if __name__ == "__main__":
    check_and_create_users()