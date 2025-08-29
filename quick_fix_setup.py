#!/usr/bin/env python3
"""
Quick Fix Setup for AnwaltsAI
Fixes database, port, and frontend issues
"""

import sqlite3
import hashlib
import os
from pathlib import Path

def quick_setup():
    """Quick setup to fix all issues"""
    print("🔧 AnwaltsAI Quick Fix Setup")
    print("=" * 30)
    
    # 1. Create .env file if missing
    env_path = Path("backend/.env")
    if not env_path.exists():
        print("📝 Creating backend/.env file...")
        env_content = """TOGETHER_API_KEY=your_api_key_here
DEFAULT_AI_MODEL=deepseek-ai/DeepSeek-V3
DATABASE_URL=sqlite:///anwalts_ai.db
JWT_SECRET_KEY=super-secret-key-change-in-production
DEBUG=True"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
    
    # 2. Create SQLite database with users
    print("🗃️ Setting up SQLite database...")
    create_sqlite_db()
    
    # 3. Fix Together API timeout issue
    fix_together_api()
    
    print("\n✅ Quick fixes applied!")
    print("\n🚀 Now run:")
    print("   python simple_together_test.py")
    print("   .\\start_anwalts_ai.bat")

def create_sqlite_db():
    """Create simple SQLite database"""
    db_path = "anwalts_ai.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Simple users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)
    
    # Create admin user
    import uuid
    admin_id = str(uuid.uuid4())
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, email, password_hash, name, role)
        VALUES (?, ?, ?, ?, ?)
    """, (admin_id, "admin@anwalts-ai.com", admin_password, "Administrator", "admin"))
    
    conn.commit()
    conn.close()
    print(f"✅ SQLite database created: {db_path}")

def fix_together_api():
    """Fix Together API timeout issue"""
    ai_service_path = Path("backend/ai_service.py")
    
    if ai_service_path.exists():
        content = ai_service_path.read_text(encoding='utf-8')
        
        # Increase timeout
        if "timeout=120.0" in content:
            content = content.replace("timeout=120.0", "timeout=300.0")
            ai_service_path.write_text(content, encoding='utf-8')
            print("✅ Increased API timeout to 300 seconds")

def create_simple_frontend_test():
    """Create a simple frontend test page"""
    test_html = """<!DOCTYPE html>
<html>
<head>
    <title>AnwaltsAI - Simple Test</title>
</head>
<body>
    <h1>AnwaltsAI Test</h1>
    <button onclick="testAPI()">Test API Connection</button>
    <div id="result"></div>
    
    <script>
    async function testAPI() {
        try {
            const response = await fetch('http://localhost:5001/health');
            const data = await response.text();
            document.getElementById('result').innerHTML = 'Backend: ' + data;
        } catch (e) {
            document.getElementById('result').innerHTML = 'Error: ' + e.message;
        }
    }
    </script>
</body>
</html>"""
    
    with open("simple_test.html", "w") as f:
        f.write(test_html)
    print("✅ Simple test page created: simple_test.html")

if __name__ == "__main__":
    quick_setup()
    create_simple_frontend_test()