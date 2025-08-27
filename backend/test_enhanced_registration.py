#!/usr/bin/env python3
"""
Simple test server for enhanced registration system
Works without database - just validates the enhanced registration data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AnwaltsAI Enhanced Registration Test",
    description="Test server for enhanced user registration",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production domain
        "https://portal-anwalts.ai",
        "https://www.portal-anwalts.ai",
        # Development origins
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        # Allow all for testing
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test models matching our enhanced UserCreate
class EnhancedUserCreate(BaseModel):
    # Basic required fields
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    
    # Enhanced profile fields
    title: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    street_address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="Deutschland", max_length=100)
    specializations: List[str] = Field(default=[])
    bar_number: Optional[str] = Field(None, max_length=50)
    law_firm: Optional[str] = Field(None, max_length=255)
    years_experience: Optional[int] = Field(None, ge=0, le=70)
    language: str = Field(default="de", max_length=10)
    timezone: str = Field(default="Europe/Berlin", max_length=50)
    bio: Optional[str] = Field(None, max_length=1000)
    role: str = Field(default="assistant")

    @property
    def name(self) -> str:
        """Generate full name from first_name and last_name"""
        if self.title:
            return f"{self.title} {self.first_name} {self.last_name}".strip()
        return f"{self.first_name} {self.last_name}".strip()

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    law_firm: Optional[str] = None
    specializations: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    language: str = "de"
    timezone: str = "Europe/Berlin"
    created_at: str

# In-memory storage for testing
users_db = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "test_mode": "active",
            "enhanced_registration": "ready"
        }
    }

@app.post("/auth/register", response_model=UserResponse)
async def test_enhanced_registration(user_data: EnhancedUserCreate):
    """Test enhanced user registration - validates all fields"""
    try:
        # Check if user already exists
        if user_data.email in users_db:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create user ID
        user_id = str(uuid.uuid4())
        
        # Simulate user creation
        created_user = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "role": user_data.role,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "title": user_data.title,
            "company": user_data.company,
            "law_firm": user_data.law_firm,
            "specializations": user_data.specializations,
            "city": user_data.city,
            "state": user_data.state,
            "country": user_data.country,
            "language": user_data.language,
            "timezone": user_data.timezone,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store in memory
        users_db[user_data.email] = created_user
        
        logger.info(f"✅ Enhanced user registered successfully: {user_data.email}")
        logger.info(f"📋 Profile: {user_data.first_name} {user_data.last_name} ({user_data.law_firm})")
        logger.info(f"📍 Location: {user_data.city}, {user_data.state}")
        logger.info(f"⚖️ Specializations: {', '.join(user_data.specializations)}")
        
        return UserResponse(**created_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )

@app.get("/test/users")
async def list_registered_users():
    """List all registered users for testing"""
    return {
        "total_users": len(users_db),
        "users": list(users_db.values())
    }

@app.post("/test/clear")
async def clear_test_data():
    """Clear all test users"""
    users_db.clear()
    return {"message": "All test users cleared"}

@app.get("/test/validate-fields")
async def validate_enhanced_fields():
    """Validate that all enhanced fields are properly configured"""
    
    sample_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "title": "Dr.",
        "company": "Test Law Firm",
        "law_firm": "Test Law Firm",
        "specializations": ["Zivilrecht", "Handelsrecht"],
        "city": "Berlin",
        "state": "Berlin",
        "country": "Deutschland"
    }
    
    try:
        # Try to create the model with sample data
        test_user = EnhancedUserCreate(**sample_data)
        
        return {
            "status": "success",
            "message": "All enhanced fields validated successfully",
            "sample_user": {
                "name": test_user.name,
                "email": test_user.email,
                "specializations": test_user.specializations,
                "location": f"{test_user.city}, {test_user.state}",
                "law_firm": test_user.law_firm
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Field validation failed: {str(e)}"
        }

if __name__ == "__main__":
    print("Starting AnwaltsAI Enhanced Registration Test Server...")
    print("Server: http://localhost:8000")
    print("Test endpoints:")
    print("   POST /auth/register - Test enhanced registration")
    print("   GET /test/users - List registered users") 
    print("   GET /test/validate-fields - Validate field structure")
    print("   GET /health - Health check")
    
    uvicorn.run(
        "test_enhanced_registration:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )