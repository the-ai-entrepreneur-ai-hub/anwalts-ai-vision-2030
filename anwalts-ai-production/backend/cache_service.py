"""
Redis Cache Service for AnwaltsAI
Provides session management, data caching, and rate limiting
"""

import asyncio
import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import uuid

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service with session management and rate limiting"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url = self._get_redis_url()
        
    def _get_redis_url(self) -> str:
        """Get Redis URL from environment variables"""
        import os
        
        # Support both REDIS_URL and individual components
        if redis_url := os.getenv("REDIS_URL"):
            return redis_url
            
        # Construct from individual components
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")
        password = os.getenv("REDIS_PASSWORD", "")
        db = os.getenv("REDIS_DB", "0")
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        else:
            return f"redis://{host}:{port}/{db}"
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
                retry_on_timeout=True,
                max_connections=50
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            raise
    
    def _get_key(self, prefix: str, key: str) -> str:
        """Generate standardized cache key"""
        return f"anwalts_ai:{prefix}:{key}"
    
    # ============ SESSION MANAGEMENT ============
    
    async def store_session(
        self, 
        session_id: str, 
        user_id: str, 
        expires_in: int = 86400,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store user session with TTL"""
        try:
            session_data = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            }
            
            if metadata:
                session_data.update(metadata)
            
            key = self._get_key("session", session_id)
            await self.redis_client.setex(
                key, 
                expires_in, 
                json.dumps(session_data)
            )
            
            # Also store reverse lookup for user sessions
            user_sessions_key = self._get_key("user_sessions", user_id)
            await self.redis_client.sadd(user_sessions_key, session_id)
            await self.redis_client.expire(user_sessions_key, expires_in)
            
            logger.info(f"Session {session_id} stored for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            key = self._get_key("session", session_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        try:
            # Get session to find user_id
            session_data = await self.get_session(session_id)
            
            key = self._get_key("session", session_id)
            result = await self.redis_client.delete(key)
            
            # Remove from user sessions set
            if session_data and "user_id" in session_data:
                user_sessions_key = self._get_key("user_sessions", session_data["user_id"])
                await self.redis_client.srem(user_sessions_key, session_id)
            
            logger.info(f"Session {session_id} deleted")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def extend_session(self, session_id: str, extends_by: int = 3600) -> bool:
        """Extend session TTL"""
        try:
            key = self._get_key("session", session_id)
            current_ttl = await self.redis_client.ttl(key)
            
            if current_ttl > 0:
                new_ttl = current_ttl + extends_by
                await self.redis_client.expire(key, new_ttl)
                
                # Update session data
                session_data = await self.get_session(session_id)
                if session_data:
                    session_data["expires_at"] = (
                        datetime.utcnow() + timedelta(seconds=new_ttl)
                    ).isoformat()
                    await self.redis_client.setex(key, new_ttl, json.dumps(session_data))
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error extending session {session_id}: {e}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active sessions for a user"""
        try:
            user_sessions_key = self._get_key("user_sessions", user_id)
            sessions = await self.redis_client.smembers(user_sessions_key)
            return list(sessions) if sessions else []
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user"""
        try:
            sessions = await self.get_user_sessions(user_id)
            deleted_count = 0
            
            for session_id in sessions:
                if await self.delete_session(session_id):
                    deleted_count += 1
            
            # Clean up user sessions set
            user_sessions_key = self._get_key("user_sessions", user_id)
            await self.redis_client.delete(user_sessions_key)
            
            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting user sessions for {user_id}: {e}")
            return 0
    
    # ============ DATA CACHING ============
    
    async def cache_templates(
        self, 
        user_id: str, 
        templates: List[Dict[str, Any]], 
        ttl: int = 3600
    ) -> bool:
        """Cache user templates"""
        try:
            key = self._get_key("templates", user_id)
            data = json.dumps(templates, default=str)
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Error caching templates for user {user_id}: {e}")
            return False
    
    async def get_cached_templates(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached templates"""
        try:
            key = self._get_key("templates", user_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached templates for user {user_id}: {e}")
            return None
    
    async def cache_clauses(
        self, 
        user_id: str, 
        clauses: List[Dict[str, Any]], 
        ttl: int = 3600
    ) -> bool:
        """Cache user clauses"""
        try:
            key = self._get_key("clauses", user_id)
            data = json.dumps(clauses, default=str)
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Error caching clauses for user {user_id}: {e}")
            return False
    
    async def get_cached_clauses(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached clauses"""
        try:
            key = self._get_key("clauses", user_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached clauses for user {user_id}: {e}")
            return None
    
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all cached data for a user"""
        try:
            keys_to_delete = [
                self._get_key("templates", user_id),
                self._get_key("clauses", user_id),
                self._get_key("clipboard", user_id)
            ]
            
            deleted = await self.redis_client.delete(*keys_to_delete)
            logger.info(f"Invalidated {deleted} cache keys for user {user_id}")
            return deleted > 0
        except Exception as e:
            logger.error(f"Error invalidating cache for user {user_id}: {e}")
            return False
    
    # ============ RATE LIMITING ============
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window: int = 3600,
        action: str = "api"
    ) -> Dict[str, Any]:
        """Check rate limit using sliding window"""
        try:
            key = self._get_key(f"rate_limit:{action}", identifier)
            current_time = int(datetime.utcnow().timestamp())
            
            # Use sliding window with sorted sets
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, current_time - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(uuid.uuid4()): current_time})
            
            # Set expiry
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_count = results[1] + 1  # +1 for the request we just added
            
            return {
                "allowed": current_count <= limit,
                "count": current_count,
                "limit": limit,
                "window": window,
                "reset_time": current_time + window
            }
        except Exception as e:
            logger.error(f"Error checking rate limit for {identifier}: {e}")
            # On error, allow the request to proceed
            return {
                "allowed": True,
                "count": 0,
                "limit": limit,
                "window": window,
                "reset_time": int(datetime.utcnow().timestamp()) + window
            }
    
    async def get_rate_limit_status(
        self, 
        identifier: str, 
        action: str = "api"
    ) -> Dict[str, Any]:
        """Get current rate limit status without incrementing"""
        try:
            key = self._get_key(f"rate_limit:{action}", identifier)
            current_time = int(datetime.utcnow().timestamp())
            
            # Clean and count current requests
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - 3600)  # 1 hour window
            pipe.zcard(key)
            
            results = await pipe.execute()
            current_count = results[1]
            
            return {
                "count": current_count,
                "reset_time": current_time + 3600
            }
        except Exception as e:
            logger.error(f"Error getting rate limit status for {identifier}: {e}")
            return {"count": 0, "reset_time": int(datetime.utcnow().timestamp()) + 3600}
    
    # ============ AI RESPONSE CACHING ============
    
    async def cache_ai_response(
        self, 
        prompt_hash: str, 
        response: Dict[str, Any], 
        ttl: int = 7200
    ) -> bool:
        """Cache AI response for reuse"""
        try:
            key = self._get_key("ai_response", prompt_hash)
            data = json.dumps(response, default=str)
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Error caching AI response: {e}")
            return False
    
    async def get_cached_ai_response(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached AI response"""
        try:
            key = self._get_key("ai_response", prompt_hash)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached AI response: {e}")
            return None
    
    def hash_prompt(self, prompt: str, model: str, **kwargs) -> str:
        """Create hash for AI prompt caching"""
        prompt_data = {
            "prompt": prompt,
            "model": model,
            **kwargs
        }
        
        # Create deterministic hash
        content = json.dumps(prompt_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    # ============ STATISTICS AND MONITORING ============
    
    async def increment_counter(
        self, 
        counter_name: str, 
        value: int = 1, 
        ttl: Optional[int] = None
    ) -> int:
        """Increment a counter"""
        try:
            key = self._get_key("counter", counter_name)
            result = await self.redis_client.incrby(key, value)
            
            if ttl:
                await self.redis_client.expire(key, ttl)
            
            return result
        except Exception as e:
            logger.error(f"Error incrementing counter {counter_name}: {e}")
            return 0
    
    async def get_counter(self, counter_name: str) -> int:
        """Get counter value"""
        try:
            key = self._get_key("counter", counter_name)
            result = await self.redis_client.get(key)
            return int(result) if result else 0
        except Exception as e:
            logger.error(f"Error getting counter {counter_name}: {e}")
            return 0
    
    async def store_metrics(
        self, 
        metrics: Dict[str, Any], 
        ttl: int = 86400
    ) -> bool:
        """Store application metrics"""
        try:
            timestamp = int(datetime.utcnow().timestamp())
            key = self._get_key("metrics", str(timestamp))
            
            data = json.dumps(metrics, default=str)
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
            return False
    
    # ============ CLEANUP OPERATIONS ============
    
    async def cleanup_expired_keys(self):
        """Clean up expired keys (Redis handles this automatically, but we can be proactive)"""
        try:
            # Get keys that might be expired
            pattern = self._get_key("*", "*")
            keys = await self.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    expired_count += 1
            
            logger.info(f"Found {expired_count} expired keys during cleanup")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        try:
            info = await self.redis_client.info()
            
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}