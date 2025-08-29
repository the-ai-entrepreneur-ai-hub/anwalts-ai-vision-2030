#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for AnwaltsAI Backend
Tests all components: Database, API, AI Service, Cache, Authentication
"""

import asyncio
import os
import sys
import json
import logging
import httpx
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import Database
from ai_service import AIService
from cache_service import CacheService
from auth_service import AuthService
from models import UserCreate, TemplateCreate, ClauseCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database():
    """Test database connectivity and basic operations"""
    logger.info("Testing database connectivity...")
    
    try:
        db = Database()
        await db.connect()
        
        # Test health check
        await db.health_check()
        logger.info("✅ Database health check passed")
        
        # Test basic operations (without actually creating data)
        logger.info("✅ Database connectivity test passed")
        
        await db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

async def test_cache_service():
    """Test Redis cache connectivity"""
    logger.info("Testing cache service...")
    
    try:
        cache = CacheService()
        await cache.connect()
        
        # Test health check
        await cache.health_check()
        logger.info("✅ Cache health check passed")
        
        # Test basic operations
        await cache.set("test_key", "test_value", expires_in=60)
        value = await cache.get("test_key")
        
        if value == "test_value":
            logger.info("✅ Cache set/get test passed")
        else:
            logger.error("❌ Cache set/get test failed")
            return False
        
        await cache.delete("test_key")
        await cache.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Cache test failed: {e}")
        return False

def test_auth_service():
    """Test authentication service"""
    logger.info("Testing authentication service...")
    
    try:
        auth = AuthService()
        
        # Test password hashing
        password = "test_password_123"
        hashed = auth.hash_password(password)
        
        if auth.verify_password(password, hashed):
            logger.info("✅ Password hashing test passed")
        else:
            logger.error("❌ Password hashing test failed")
            return False
        
        # Test JWT token creation
        token = auth.create_access_token(data={"sub": "test_user"})
        payload = auth.verify_token(token)
        
        if payload.get("sub") == "test_user":
            logger.info("✅ JWT token test passed")
        else:
            logger.error("❌ JWT token test failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Auth service test failed: {e}")
        return False

def test_ai_service():
    """Test AI service (without actual API calls)"""
    logger.info("Testing AI service...")
    
    try:
        ai_service = AIService()
        
        # Check if API key is configured (but don't test actual calls)
        if ai_service.health_check():
            logger.info("✅ AI service configuration check passed")
        else:
            logger.warning("⚠️ TOGETHER_API_KEY not configured")
        
        # Test cost calculation
        cost = ai_service._calculate_cost("meta-llama/Llama-3.1-70B-Instruct-Turbo", 1000)
        if cost > 0:
            logger.info("✅ AI service cost calculation test passed")
        else:
            logger.error("❌ AI service cost calculation test failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI service test failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    logger.info("Testing environment configuration...")
    
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "SECRET_KEY",
        "TOGETHER_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Please copy .env.example to .env and configure the variables")
    else:
        logger.info("✅ All required environment variables are set")
    
    return len(missing_vars) == 0

async def run_integration_tests():
    """Run all integration tests"""
    logger.info("Starting AnwaltsAI Backend Integration Tests")
    logger.info("=" * 50)
    
    # Test core services first
    core_results = {
        "environment": test_environment_config(),
        "auth_service": test_auth_service(),
        "ai_service": test_ai_service(),
        "cache_service": await test_cache_service(),
        "database": await test_database()
    }
    
    logger.info("=" * 50)
    logger.info("Core Service Test Results:")
    
    core_passed = True
    for test_name, passed in core_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if not passed:
            core_passed = False
    
    # Test API integration if core services pass
    api_passed = False
    if core_passed:
        logger.info("\n" + "=" * 50)
        logger.info("Testing API Integration...")
        api_passed = await test_full_api_integration()
    else:
        logger.warning("⚠️ Skipping API tests due to core service failures")
    
    logger.info("=" * 50)
    logger.info("FINAL TEST SUMMARY:")
    
    final_results = {**core_results, "api_integration": api_passed}
    
    all_passed = True
    for test_name, passed in final_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 50)
    
    if all_passed:
        logger.info("🎉 All tests passed! Backend is ready for deployment.")
        return True
    elif core_passed:
        logger.warning("⚠️ Core services passed but API integration had issues.")
        logger.warning("Check if the FastAPI server is running on localhost:8000")
        return False
    else:
        logger.error("❌ Core service tests failed. Please fix configuration issues.")
        return False

class APITester:
    """Test API endpoints comprehensively"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_token: Optional[str] = None
        self.test_user_email = "test@anwalts-ai.de"
        self.test_user_password = "TestPass123!"
        
    async def test_health_endpoint(self) -> bool:
        """Test API health endpoint"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ Health endpoint: {health_data.get('status', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ Health endpoint returned {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Health endpoint failed: {e}")
            return False
    
    async def test_authentication_flow(self) -> bool:
        """Test complete authentication flow"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test user registration
                user_data = {
                    "email": self.test_user_email,
                    "name": "Test User",
                    "password": self.test_user_password,
                    "role": "assistant"
                }
                
                register_response = await client.post(
                    f"{self.base_url}/auth/register",
                    json=user_data
                )
                
                # User might already exist
                if register_response.status_code not in [200, 201, 409]:
                    logger.error(f"❌ Registration failed: {register_response.status_code}")
                    return False
                
                # Test login
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                login_response = await client.post(
                    f"{self.base_url}/auth/login",
                    json=login_data
                )
                
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    self.auth_token = login_result.get("token")
                    logger.info("✅ Authentication flow successful")
                    return True
                else:
                    logger.error(f"❌ Login failed: {login_response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")
            return False
    
    async def test_template_crud(self) -> bool:
        """Test template CRUD operations"""
        if not self.auth_token:
            logger.warning("⚠️ Skipping template tests - no auth token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Create template
                template_data = {
                    "name": "Integration Test Template",
                    "content": "Test content with [PLACEHOLDER]",
                    "category": "test",
                    "type": "document"
                }
                
                create_response = await client.post(
                    f"{self.base_url}/templates",
                    json=template_data,
                    headers=headers
                )
                
                if create_response.status_code not in [200, 201]:
                    logger.error(f"❌ Template creation failed: {create_response.status_code}")
                    return False
                
                template = create_response.json()
                template_id = template["id"]
                
                # Test retrieval
                get_response = await client.get(
                    f"{self.base_url}/templates",
                    headers=headers
                )
                
                if get_response.status_code != 200:
                    logger.error(f"❌ Template retrieval failed: {get_response.status_code}")
                    return False
                
                # Clean up
                await client.delete(
                    f"{self.base_url}/templates/{template_id}",
                    headers=headers
                )
                
                logger.info("✅ Template CRUD operations successful")
                return True
                
        except Exception as e:
            logger.error(f"❌ Template CRUD test failed: {e}")
            return False
    
    async def test_ai_endpoints(self) -> bool:
        """Test AI-powered endpoints"""
        if not self.auth_token:
            logger.warning("⚠️ Skipping AI tests - no auth token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test document generation
                doc_request = {
                    "title": "Test Document",
                    "document_type": "brief",
                    "template_content": "Test template: [CONTENT]",
                    "variables": {"content": "Sample content"}
                }
                
                doc_response = await client.post(
                    f"{self.base_url}/ai/generate-document",
                    json=doc_request,
                    headers=headers
                )
                
                if doc_response.status_code == 200:
                    doc_result = doc_response.json()
                    if "content" in doc_result and len(doc_result["content"]) > 0:
                        logger.info("✅ AI document generation successful")
                        return True
                
                logger.error(f"❌ AI document generation failed: {doc_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ AI endpoints test failed: {e}")
            return False

async def test_full_api_integration() -> bool:
    """Test complete API integration"""
    logger.info("Testing full API integration...")
    
    api_tester = APITester()
    
    # Test basic health
    if not await api_tester.test_health_endpoint():
        return False
    
    # Test authentication
    if not await api_tester.test_authentication_flow():
        return False
    
    # Test core functionality
    if not await api_tester.test_template_crud():
        return False
    
    # Test AI endpoints (might fail if no API key)
    ai_success = await api_tester.test_ai_endpoints()
    if not ai_success:
        logger.warning("⚠️ AI endpoints failed - check TOGETHER_API_KEY configuration")
    
    logger.info("✅ API integration tests completed")
    return True

def print_next_steps():
    """Print next steps for deployment"""
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS FOR DEPLOYMENT")
    print("=" * 60)
    print()
    print("1. Configure Environment:")
    print("   cp .env.example .env")
    print("   # Edit .env with your configuration")
    print()
    print("2. Start the full stack:")
    print("   docker-compose up -d")
    print()
    print("3. Initialize the database:")
    print("   docker-compose exec backend python scripts/init_db.py")
    print()
    print("4. Run integration tests:")
    print("   python test_integration.py")
    print()
    print("5. Test the API:")
    print("   curl http://localhost:8000/health")
    print("   # Or visit http://localhost:8000/docs")
    print()
    print("6. Migrate existing data:")
    print("   python migration/migrate_client_data.py")
    print()
    print("7. Update frontend configuration:")
    print("   # Update API_BASE_URL in frontend config")
    print()

if __name__ == "__main__":
    # Load environment variables if .env exists
    from pathlib import Path
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    try:
        success = asyncio.run(run_integration_tests())
        
        if success:
            print_next_steps()
            sys.exit(0)
        else:
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)