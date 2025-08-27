#!/usr/bin/env python3
"""
Database initialization script for AnwaltsAI
Creates all necessary tables for the application
"""

import asyncio
import asyncpg
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with all necessary tables"""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/anwalts_ai_db")
    
    logger.info("Connecting to database...")
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Create tables
        logger.info("Creating database tables...")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'assistant',
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        logger.info("✅ Users table created")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(100) NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'document',
                is_public BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        logger.info("✅ Templates table created")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clauses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                tags TEXT[] DEFAULT '{}',
                language VARCHAR(10) DEFAULT 'de',
                is_favorite BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        logger.info("✅ Clauses table created")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_entries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                source_type VARCHAR(50) NOT NULL,
                metadata JSONB DEFAULT '{}',
                expires_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        logger.info("✅ Clipboard entries table created")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                document_type VARCHAR(100) NOT NULL,
                template_id UUID REFERENCES templates(id) ON DELETE SET NULL,
                ai_model VARCHAR(100),
                ai_prompt TEXT,
                generation_time_ms INTEGER,
                tokens_used INTEGER,
                cost_estimate DECIMAL(10,6),
                quality_score INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        logger.info("✅ Documents table created")
        
        # Create indexes for better performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_templates_user_id ON templates(user_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_clauses_user_id ON clauses(user_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_clipboard_user_id ON clipboard_entries(user_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);")
        logger.info("✅ Database indexes created")
        
        # Insert default admin user for testing
        try:
            await conn.execute("""
                INSERT INTO users (email, name, role, password_hash, is_active)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (email) DO NOTHING
            """, "admin@anwalts-ai.com", "Administrator", "admin", 
                "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewqFtONyE5yYYOTK", True)  # password: admin123
            logger.info("✅ Default admin user created (email: admin@anwalts-ai.com, password: admin123)")
        except Exception as e:
            logger.info("ℹ️ Default admin user already exists")
        
        await conn.close()
        logger.info("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(init_database())