#!/usr/bin/env python3
"""
Fix crypto.randomUUID error and create admin user
"""

import sqlite3
import hashlib
import uuid
import os
from pathlib import Path

def create_admin_user():
    """Create admin user for Dr. Markus Weigl"""
    
    # Connect to database
    db_path = "/var/www/portal-anwalts.ai/backend/anwalts_ai.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE email = ?", ("christopher.klaes@aigenex.de",))
    existing = cursor.fetchone()
    
    if existing:
        print("✅ User christopher.klaes@aigenex.de already exists")
        conn.close()
        return True
    
    # Create password hash (using simple hash for now)
    password = "admin123"  # Default password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Insert new admin user
    try:
        cursor.execute("""
            INSERT INTO users (
                id, email, password_hash, first_name, last_name, 
                role, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            str(uuid.uuid4()),
            "christopher.klaes@aigenex.de",
            password_hash,
            "Dr. Markus",
            "Weigl",
            "admin",
            True
        ))
        
        conn.commit()
        print("✅ Admin user created successfully!")
        print(f"   📧 Email: christopher.klaes@aigenex.de")
        print(f"   🔑 Password: admin123")
        print(f"   👤 Role: admin")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def create_crypto_polyfill():
    """Create crypto.randomUUID polyfill for older browsers"""
    
    polyfill_content = '''
// Crypto.randomUUID polyfill for older browsers
if (!crypto.randomUUID) {
    crypto.randomUUID = function() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0;
            var v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    };
}
'''
    
    polyfill_path = "/var/www/portal-anwalts.ai/frontend/crypto-polyfill.js"
    
    try:
        with open(polyfill_path, 'w') as f:
            f.write(polyfill_content)
        print(f"✅ Crypto polyfill created at {polyfill_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating crypto polyfill: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing crypto.randomUUID error and creating admin user...")
    print()
    
    # Fix crypto issue
    print("1️⃣ Creating crypto polyfill...")
    create_crypto_polyfill()
    
    print()
    print("2️⃣ Creating admin user...")
    create_admin_user()
    
    print()
    print("✅ All fixes completed!")
    print()
    print("🎯 Next steps:")
    print("  1. Add crypto-polyfill.js to HTML head section")
    print("  2. Test login with christopher.klaes@aigenex.de / admin123")