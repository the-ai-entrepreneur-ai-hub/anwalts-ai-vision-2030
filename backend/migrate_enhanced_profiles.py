#!/usr/bin/env python3
"""
Database migration to add enhanced user profile fields
Extends the users table with comprehensive profile information
"""

import asyncio
import asyncpg
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_enhanced_profiles():
    """Add enhanced profile fields to users table"""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/anwalts_ai_db")
    
    logger.info("🔄 Starting enhanced profile migration...")
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Add enhanced profile fields to users table
        migration_sql = """
        -- Add enhanced profile fields to users table
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS title VARCHAR(20),
        
        -- Professional information
        ADD COLUMN IF NOT EXISTS company VARCHAR(255),
        ADD COLUMN IF NOT EXISTS department VARCHAR(255),
        ADD COLUMN IF NOT EXISTS position VARCHAR(255),
        
        -- Contact information
        ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
        ADD COLUMN IF NOT EXISTS mobile VARCHAR(20),
        ADD COLUMN IF NOT EXISTS fax VARCHAR(20),
        
        -- Address information
        ADD COLUMN IF NOT EXISTS street_address VARCHAR(255),
        ADD COLUMN IF NOT EXISTS city VARCHAR(100),
        ADD COLUMN IF NOT EXISTS state VARCHAR(100),
        ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20),
        ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'Deutschland',
        
        -- Legal specializations
        ADD COLUMN IF NOT EXISTS specializations TEXT[] DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS bar_number VARCHAR(50),
        ADD COLUMN IF NOT EXISTS law_firm VARCHAR(255),
        ADD COLUMN IF NOT EXISTS years_experience INTEGER,
        
        -- Profile settings
        ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'de',
        ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Europe/Berlin',
        ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS bio TEXT,
        
        -- Notification preferences
        ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE,
        ADD COLUMN IF NOT EXISTS browser_notifications BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS ai_updates BOOLEAN DEFAULT TRUE,
        
        -- Professional settings
        ADD COLUMN IF NOT EXISTS signature TEXT,
        ADD COLUMN IF NOT EXISTS letterhead VARCHAR(500),
        
        -- System fields
        ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255);
        """
        
        await conn.execute(migration_sql)
        logger.info("✅ Enhanced profile fields added to users table")
        
        # Create indexes for better performance
        index_sql = """
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_users_email_lower ON users (lower(email));
        CREATE INDEX IF NOT EXISTS idx_users_last_name ON users (last_name);
        CREATE INDEX IF NOT EXISTS idx_users_law_firm ON users (law_firm);
        CREATE INDEX IF NOT EXISTS idx_users_city ON users (city);
        CREATE INDEX IF NOT EXISTS idx_users_specializations ON users USING GIN (specializations);
        CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);
        """
        
        await conn.execute(index_sql)
        logger.info("✅ Performance indexes created")
        
        # Update existing users with derived names from existing 'name' field
        update_existing_sql = """
        UPDATE users 
        SET 
            first_name = CASE 
                WHEN position(' ' IN name) > 0 
                THEN split_part(name, ' ', 1)
                ELSE name
            END,
            last_name = CASE 
                WHEN position(' ' IN name) > 0 
                THEN substring(name FROM position(' ' IN name) + 1)
                ELSE ''
            END
        WHERE first_name IS NULL OR last_name IS NULL;
        """
        
        result = await conn.execute(update_existing_sql)
        logger.info(f"✅ Updated existing users with derived first/last names: {result}")
        
        # Add trigger to update updated_at timestamp
        trigger_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_users_updated_at ON users;
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        await conn.execute(trigger_sql)
        logger.info("✅ Updated timestamp trigger created")
        
        # Test the migration
        test_query = """
        SELECT 
            id, email, name, first_name, last_name, title,
            company, position, law_firm, specializations,
            language, timezone, email_notifications
        FROM users 
        LIMIT 1;
        """
        
        test_result = await conn.fetchrow(test_query)
        if test_result:
            logger.info("✅ Migration test successful - enhanced fields accessible")
        else:
            logger.info("ℹ️ No existing users to test with")
        
        await conn.close()
        logger.info("🎉 Enhanced profile migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_enhanced_profiles())