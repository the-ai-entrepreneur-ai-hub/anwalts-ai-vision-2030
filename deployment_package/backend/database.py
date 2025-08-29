"""
SQLAlchemy Database Operations for AnwaltsAI
Async PostgreSQL database with connection pooling and comprehensive CRUD operations
"""

import asyncio
import asyncpg
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
from contextlib import asynccontextmanager

from models import (
    UserInDB, TemplateInDB, ClauseInDB, ClipboardEntryInDB, 
    DocumentInDB
)

logger = logging.getLogger(__name__)

class Database:
    """Async PostgreSQL database operations with connection pooling"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = self._get_database_url()
        
    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        import os
        
        # Support both DATABASE_URL and individual components
        if db_url := os.getenv("DATABASE_URL"):
            return db_url
            
        # Construct from individual components
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        database = os.getenv("DB_NAME", "anwalts_ai")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    async def connect(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'jit': 'off'  # Disable JIT for better connection performance
                }
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        async with self.pool.acquire() as conn:
            yield conn
    
    # ============ USER OPERATIONS ============
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserInDB]:
        """Get user by ID"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, name, role, password_hash, is_active, 
                           created_at, updated_at
                    FROM users 
                    WHERE id = $1 AND is_active = true
                    """,
                    user_id
                )
                
                if row:
                    return UserInDB(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, name, role, password_hash, is_active,
                           created_at, updated_at
                    FROM users 
                    WHERE email = $1
                    """,
                    email.lower()
                )
                
                if row:
                    return UserInDB(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def create_user(
        self, 
        email: str, 
        name: str, 
        role: str, 
        password_hash: str
    ) -> UserInDB:
        """Create new user"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO users (email, name, role, password_hash)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, email, name, role, password_hash, is_active,
                              created_at, updated_at
                    """,
                    email.lower(), name, role, password_hash
                )
                
                return UserInDB(**dict(row))
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            raise
    
    # ============ TEMPLATE OPERATIONS ============
    
    async def get_templates(
        self, 
        user_id: uuid.UUID, 
        category: Optional[str] = None
    ) -> List[TemplateInDB]:
        """Get user templates with optional category filter"""
        try:
            async with self.get_connection() as conn:
                query = """
                    SELECT id, user_id, name, content, category, type, is_public,
                           usage_count, created_at, updated_at
                    FROM templates 
                    WHERE user_id = $1
                """
                params = [user_id]
                
                if category:
                    query += " AND category = $2"
                    params.append(category)
                
                query += " ORDER BY updated_at DESC"
                
                rows = await conn.fetch(query, *params)
                return [TemplateInDB(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting templates for user {user_id}: {e}")
            raise
    
    async def create_template(
        self,
        user_id: uuid.UUID,
        name: str,
        content: str,
        category: str,
        type: str
    ) -> TemplateInDB:
        """Create new template"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO templates (user_id, name, content, category, type)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, user_id, name, content, category, type, is_public,
                              usage_count, created_at, updated_at
                    """,
                    user_id, name, content, category, type
                )
                
                return TemplateInDB(**dict(row))
        except Exception as e:
            logger.error(f"Error creating template for user {user_id}: {e}")
            raise
    
    async def update_template(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs
    ) -> Optional[TemplateInDB]:
        """Update existing template"""
        try:
            if not kwargs:
                return await self.get_template_by_id(template_id, user_id)
            
            # Build dynamic update query
            set_clauses = []
            params = []
            param_count = 1
            
            for key, value in kwargs.items():
                if value is not None:
                    set_clauses.append(f"{key} = ${param_count}")
                    params.append(value)
                    param_count += 1
            
            if not set_clauses:
                return await self.get_template_by_id(template_id, user_id)
            
            params.extend([template_id, user_id])
            
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE templates 
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count} AND user_id = ${param_count + 1}
                    RETURNING id, user_id, name, content, category, type, is_public,
                              usage_count, created_at, updated_at
                    """,
                    *params
                )
                
                if row:
                    return TemplateInDB(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}")
            raise
    
    async def get_template_by_id(
        self, 
        template_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Optional[TemplateInDB]:
        """Get template by ID"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, user_id, name, content, category, type, is_public,
                           usage_count, created_at, updated_at
                    FROM templates 
                    WHERE id = $1 AND user_id = $2
                    """,
                    template_id, user_id
                )
                
                if row:
                    return TemplateInDB(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {e}")
            raise
    
    async def delete_template(
        self, 
        template_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> bool:
        """Delete template"""
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(
                    "DELETE FROM templates WHERE id = $1 AND user_id = $2",
                    template_id, user_id
                )
                
                return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            raise
    
    async def increment_template_usage(self, template_id: uuid.UUID):
        """Increment template usage count"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE templates SET usage_count = usage_count + 1 WHERE id = $1",
                    template_id
                )
        except Exception as e:
            logger.error(f"Error incrementing template usage {template_id}: {e}")
            # Don't raise - this is a non-critical operation
    
    # ============ CLAUSE OPERATIONS ============
    
    async def get_clauses(
        self,
        user_id: uuid.UUID,
        category: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[ClauseInDB]:
        """Get user clauses with optional filters"""
        try:
            async with self.get_connection() as conn:
                query = """
                    SELECT id, user_id, category, title, content, tags, language,
                           is_favorite, usage_count, created_at, updated_at
                    FROM clauses 
                    WHERE user_id = $1
                """
                params = [user_id]
                param_count = 2
                
                if category:
                    query += f" AND category = ${param_count}"
                    params.append(category)
                    param_count += 1
                
                if language:
                    query += f" AND language = ${param_count}"
                    params.append(language)
                
                query += " ORDER BY is_favorite DESC, updated_at DESC"
                
                rows = await conn.fetch(query, *params)
                return [ClauseInDB(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting clauses for user {user_id}: {e}")
            raise
    
    async def create_clause(
        self,
        user_id: uuid.UUID,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        language: str
    ) -> ClauseInDB:
        """Create new clause"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO clauses (user_id, category, title, content, tags, language)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id, user_id, category, title, content, tags, language,
                              is_favorite, usage_count, created_at, updated_at
                    """,
                    user_id, category, title, content, tags, language
                )
                
                return ClauseInDB(**dict(row))
        except Exception as e:
            logger.error(f"Error creating clause for user {user_id}: {e}")
            raise
    
    # ============ CLIPBOARD OPERATIONS ============
    
    async def get_clipboard_entries(
        self, 
        user_id: uuid.UUID, 
        limit: int = 50
    ) -> List[ClipboardEntryInDB]:
        """Get user clipboard entries"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, content, source_type, metadata, 
                           expires_at, created_at
                    FROM clipboard_entries 
                    WHERE user_id = $1 
                      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    ORDER BY created_at DESC 
                    LIMIT $2
                    """,
                    user_id, limit
                )
                
                return [ClipboardEntryInDB(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting clipboard entries for user {user_id}: {e}")
            raise
    
    async def create_clipboard_entry(
        self,
        user_id: uuid.UUID,
        content: str,
        source_type: str,
        metadata: Dict[str, Any],
        expires_at: Optional[datetime] = None
    ) -> ClipboardEntryInDB:
        """Create new clipboard entry"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO clipboard_entries 
                    (user_id, content, source_type, metadata, expires_at)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, user_id, content, source_type, metadata,
                              expires_at, created_at
                    """,
                    user_id, content, source_type, json.dumps(metadata), expires_at
                )
                
                return ClipboardEntryInDB(**dict(row))
        except Exception as e:
            logger.error(f"Error creating clipboard entry for user {user_id}: {e}")
            raise
    
    # ============ DOCUMENT OPERATIONS ============
    
    async def create_document(
        self,
        user_id: uuid.UUID,
        title: str,
        content: str,
        document_type: str,
        template_id: Optional[uuid.UUID] = None,
        ai_model: Optional[str] = None,
        ai_prompt: Optional[str] = None,
        generation_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cost_estimate: Optional[float] = None
    ) -> DocumentInDB:
        """Create new document"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO documents 
                    (user_id, title, content, document_type, template_id, ai_model,
                     ai_prompt, generation_time_ms, tokens_used, cost_estimate)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id, user_id, title, content, document_type, template_id,
                              ai_model, ai_prompt, generation_time_ms, tokens_used,
                              cost_estimate, quality_score, created_at
                    """,
                    user_id, title, content, document_type, template_id, ai_model,
                    ai_prompt, generation_time_ms, tokens_used, cost_estimate
                )
                
                return DocumentInDB(**dict(row))
        except Exception as e:
            logger.error(f"Error creating document for user {user_id}: {e}")
            raise
    
    # ============ ANALYTICS OPERATIONS ============
    
    async def create_analytics_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        event_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Create analytics event"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO analytics_events 
                    (user_id, event_type, event_data, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    user_id, event_type, json.dumps(event_data), 
                    ip_address, user_agent
                )
                return True
        except Exception as e:
            logger.error(f"Error creating analytics event: {e}")
            # Don't raise - analytics should not break main functionality
            return False
    
    # ============ SESSION OPERATIONS ============
    
    async def create_session(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> uuid.UUID:
        """Create new session"""
        try:
            async with self.get_connection() as conn:
                session_id = await conn.fetchval(
                    """
                    INSERT INTO sessions (user_id, token_hash, expires_at, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    user_id, token_hash, expires_at, ip_address, user_agent
                )
                return session_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def delete_session(self, token_hash: str) -> bool:
        """Delete session by token hash"""
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(
                    "DELETE FROM sessions WHERE token_hash = $1",
                    token_hash
                )
                return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def is_session_valid(self, token_hash: str) -> bool:
        """Check if session is valid"""
        try:
            async with self.get_connection() as conn:
                exists = await conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM sessions 
                        WHERE token_hash = $1 AND expires_at > CURRENT_TIMESTAMP
                    )
                    """,
                    token_hash
                )
                return exists
        except Exception as e:
            logger.error(f"Error checking session validity: {e}")
            return False
    
    # ============ MAINTENANCE OPERATIONS ============
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(
                    "DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP"
                )
                logger.info(f"Cleaned up expired sessions: {result}")
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    async def cleanup_expired_clipboard(self):
        """Clean up expired clipboard entries"""
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM clipboard_entries 
                    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
                    """
                )
                logger.info(f"Cleaned up expired clipboard entries: {result}")
        except Exception as e:
            logger.error(f"Error cleaning up expired clipboard entries: {e}")

# Dependency injection for FastAPI
async def get_database() -> Database:
    """Dependency to get database instance"""
    # This will be set by the main app during startup
    from main import db
    return db