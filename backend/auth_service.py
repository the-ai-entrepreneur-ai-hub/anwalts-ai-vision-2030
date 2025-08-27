"""
Authentication Service for AnwaltsAI
JWT token management and password hashing with security best practices
"""

import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from passlib.context import CryptContext
import uuid
import hashlib

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service with JWT tokens and secure password hashing"""
    
    def __init__(self):
        # JWT Configuration
        self.secret_key = self._get_secret_key()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days
        
        # Password hashing context
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Strong hashing rounds
        )
        
        # Token blacklist (in production, use Redis or database)
        self.blacklisted_tokens: Set[str] = set()
        
        # Security settings
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
        
    def _get_secret_key(self) -> str:
        """Get JWT secret key from environment or generate one"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        
        if not secret_key:
            # Generate a secure secret key
            secret_key = os.urandom(64).hex()
            logger.warning(
                "JWT_SECRET_KEY not found in environment. "
                "Generated temporary key. Set JWT_SECRET_KEY for persistence."
            )
        
        return secret_key
    
    # ============ PASSWORD MANAGEMENT ============
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            # Add password strength validation
            self._validate_password_strength(password)
            
            # Hash password
            hashed = self.pwd_context.hash(password)
            logger.info("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise ValueError("Failed to hash password")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase, lowercase, number, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        # For development/testing, be more lenient
        # In production this should be more strict
        criteria_met = sum([has_upper, has_lower, has_digit, has_special])
        if criteria_met < 3:
            raise ValueError(
                "Password must contain at least 3 of: uppercase letter, "
                "lowercase letter, number, or special character"
            )
        
        # Check for common weak passwords
        weak_passwords = {
            "password", "123456", "12345678", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        }
        
        if password.lower() in weak_passwords:
            raise ValueError("Password is too common. Please choose a stronger password.")
        
        return True
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """Check if password hash needs to be updated"""
        return self.pwd_context.needs_update(hashed_password)
    
    # ============ JWT TOKEN MANAGEMENT ============
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        try:
            to_encode = data.copy()
            
            # Set expiration
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Add standard JWT claims
            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4()),  # JWT ID for blacklisting
                "type": "access"
            })
            
            # Create and return token
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Access token created for user: {data.get('sub', 'unknown')}")
            
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise ValueError("Failed to create access token")
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4()),
                "type": "refresh"
            })
            
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Refresh token created for user: {data.get('sub', 'unknown')}")
            
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise ValueError("Failed to create refresh token")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            # Decode token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            # Verify token type
            token_type = payload.get("type")
            if token_type not in ["access", "refresh"]:
                raise jwt.InvalidTokenError("Invalid token type")
            
            logger.debug(f"Token verified for user: {payload.get('sub', 'unknown')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise jwt.InvalidTokenError("Invalid token")
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            raise jwt.InvalidTokenError("Token verification failed")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Create new access token from refresh token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Invalid token type for refresh")
            
            # Create new access token
            user_id = payload.get("sub")
            if not user_id:
                raise jwt.InvalidTokenError("Missing user ID in token")
            
            new_access_token = self.create_access_token(data={"sub": user_id})
            
            # Optionally create new refresh token for token rotation
            new_refresh_token = self.create_refresh_token(data={"sub": user_id})
            
            # Blacklist old refresh token
            self.blacklist_token(refresh_token)
            
            logger.info(f"Token refreshed for user: {user_id}")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise ValueError("Failed to refresh token")
    
    def get_token_claims(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token claims without verification (for debugging)"""
        try:
            # Decode without verification
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload
        except Exception as e:
            logger.error(f"Error getting token claims: {e}")
            return None
    
    # ============ TOKEN BLACKLISTING ============
    
    def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist"""
        try:
            # Get token JTI for blacklisting
            payload = self.get_token_claims(token)
            if payload and "jti" in payload:
                token_id = payload["jti"]
                self.blacklisted_tokens.add(token_id)
                logger.info(f"Token blacklisted: {token_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            payload = self.get_token_claims(token)
            if payload and "jti" in payload:
                return payload["jti"] in self.blacklisted_tokens
            return False
        except Exception:
            return False
    
    def cleanup_blacklist(self):
        """Clean up expired tokens from blacklist"""
        try:
            # In production, implement proper cleanup based on token expiration
            # For now, we'll limit the blacklist size
            if len(self.blacklisted_tokens) > 10000:
                # Keep only the most recent 5000 tokens
                recent_tokens = list(self.blacklisted_tokens)[-5000:]
                self.blacklisted_tokens = set(recent_tokens)
                logger.info("Blacklist cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up blacklist: {e}")
    
    # ============ SECURITY UTILITIES ============
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return os.urandom(length).hex()
    
    def hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def constant_time_compare(self, val1: str, val2: str) -> bool:
        """Constant-time string comparison to prevent timing attacks"""
        if len(val1) != len(val2):
            return False
        
        result = 0
        for x, y in zip(val1, val2):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token for forms"""
        return self.generate_secure_token(32)
    
    def verify_csrf_token(self, token: str, expected: str) -> bool:
        """Verify CSRF token"""
        return self.constant_time_compare(token, expected)
    
    # ============ SESSION SECURITY ============
    
    def create_session_data(
        self, 
        user_id: str, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create secure session data"""
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "session_id": str(uuid.uuid4()),
            "csrf_token": self.generate_csrf_token()
        }
        
        if ip_address:
            session_data["ip_address"] = ip_address
        
        if user_agent:
            # Hash user agent for privacy
            session_data["user_agent_hash"] = hashlib.sha256(
                user_agent.encode()
            ).hexdigest()[:16]
        
        return session_data
    
    def validate_session_security(
        self, 
        session_data: Dict[str, Any],
        current_ip: Optional[str] = None,
        current_user_agent: Optional[str] = None
    ) -> bool:
        """Validate session security parameters"""
        try:
            # Check IP address consistency (optional, can be disabled for mobile users)
            if current_ip and "ip_address" in session_data:
                if session_data["ip_address"] != current_ip:
                    logger.warning(f"IP address mismatch for session: {session_data.get('session_id')}")
                    # Don't reject, just log for monitoring
            
            # Check user agent consistency (basic fingerprinting)
            if current_user_agent and "user_agent_hash" in session_data:
                current_hash = hashlib.sha256(current_user_agent.encode()).hexdigest()[:16]
                if session_data["user_agent_hash"] != current_hash:
                    logger.warning(f"User agent mismatch for session: {session_data.get('session_id')}")
                    # Don't reject, just log for monitoring
            
            return True
        except Exception as e:
            logger.error(f"Error validating session security: {e}")
            return False
    
    # ============ PASSWORD RESET ============
    
    def create_password_reset_token(self, user_id: str) -> str:
        """Create password reset token"""
        try:
            data = {
                "sub": user_id,
                "type": "password_reset",
                "exp": datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            }
            
            token = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Password reset token created for user: {user_id}")
            
            return token
        except Exception as e:
            logger.error(f"Error creating password reset token: {e}")
            raise ValueError("Failed to create password reset token")
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return user ID"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            if payload.get("type") != "password_reset":
                raise jwt.InvalidTokenError("Invalid token type")
            
            user_id = payload.get("sub")
            logger.info(f"Password reset token verified for user: {user_id}")
            
            return user_id
        except jwt.ExpiredSignatureError:
            logger.warning("Password reset token has expired")
            raise ValueError("Password reset token has expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid password reset token")
            raise ValueError("Invalid password reset token")
        except Exception as e:
            logger.error(f"Error verifying password reset token: {e}")
            raise ValueError("Failed to verify password reset token")
    
    # ============ EMAIL VERIFICATION ============
    
    def create_email_verification_token(self, email: str) -> str:
        """Create email verification token"""
        try:
            data = {
                "email": email,
                "type": "email_verification",
                "exp": datetime.utcnow() + timedelta(days=7)  # 7 days expiry
            }
            
            token = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Email verification token created for: {email}")
            
            return token
        except Exception as e:
            logger.error(f"Error creating email verification token: {e}")
            raise ValueError("Failed to create email verification token")
    
    def verify_email_verification_token(self, token: str) -> Optional[str]:
        """Verify email verification token and return email"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            if payload.get("type") != "email_verification":
                raise jwt.InvalidTokenError("Invalid token type")
            
            email = payload.get("email")
            logger.info(f"Email verification token verified for: {email}")
            
            return email
        except jwt.ExpiredSignatureError:
            logger.warning("Email verification token has expired")
            raise ValueError("Email verification token has expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid email verification token")
            raise ValueError("Invalid email verification token")
        except Exception as e:
            logger.error(f"Error verifying email verification token: {e}")
            raise ValueError("Failed to verify email verification token")
    
    # ============ SECURITY MONITORING ============
    
    def log_security_event(
        self, 
        event_type: str, 
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security-related events"""
        try:
            log_data = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            if details:
                log_data.update(details)
            
            # In production, send to security monitoring system
            logger.warning(f"Security event: {log_data}")
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    # ============ DEPENDENCY INJECTION ============
    
    def get_current_user_id(self, credentials=None) -> str:
        """Dependency function to get current user ID from JWT token"""
        try:
            if not credentials:
                from fastapi import Depends, HTTPException, status
                from fastapi.security import HTTPBearer
                security = HTTPBearer()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication credentials"
                )
            
            # Verify token and extract user ID
            payload = self.verify_token(credentials.credentials)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )
            
            return user_id
            
        except Exception as e:
            logger.error(f"Get current user ID error: {e}")
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )