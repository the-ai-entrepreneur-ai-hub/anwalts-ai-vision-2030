"""
Pydantic Models for AnwaltsAI Backend API
Defines request/response models and database entities
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

# ============ ENUMS ============

class UserRole(str, Enum):
    ADMIN = "admin"
    ASSISTANT = "assistant"

class TemplateType(str, Enum):
    DOCUMENT = "document"
    EMAIL = "email"
    CLAUSE = "clause"

class SourceType(str, Enum):
    MANUAL = "manual"
    TEMPLATE = "template"
    AI_GENERATED = "ai_generated"

# ============ DATABASE ENTITIES ============

class UserInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    email: str
    name: str
    role: str
    password_hash: str
    is_active: bool = True
    
    # Enhanced profile fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None  # Dr., Prof., etc.
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    
    # Contact information
    phone: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    
    # Address information
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "Deutschland"
    
    # Legal specializations
    specializations: List[str] = []
    bar_number: Optional[str] = None  # Anwaltsnummer
    law_firm: Optional[str] = None
    years_experience: Optional[int] = None
    
    # Profile settings
    language: str = "de"
    timezone: str = "Europe/Berlin"
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Notification preferences
    email_notifications: bool = True
    browser_notifications: bool = False
    ai_updates: bool = True
    
    # Professional settings
    signature: Optional[str] = None
    letterhead: Optional[str] = None
    
    # System fields
    last_login: Optional[datetime] = None
    login_count: int = 0
    is_verified: bool = False
    verification_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TemplateInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    content: str
    category: str
    type: str
    is_public: bool = False
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

class ClauseInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    title: str
    content: str
    tags: List[str] = []
    language: str = "de"
    is_favorite: bool = False
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

class ClipboardEntryInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    source_type: str
    metadata: Dict[str, Any] = {}
    expires_at: Optional[datetime] = None
    created_at: datetime

class DocumentInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    document_type: str
    template_id: Optional[uuid.UUID] = None
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None
    generation_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    quality_score: Optional[int] = None
    created_at: datetime

# ============ REQUEST MODELS ============

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserCreate(BaseModel):
    # Basic required fields
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    # Enhanced profile fields
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    title: Optional[str] = Field(None, max_length=20)  # Dr., Prof., etc.
    
    # Professional information
    company: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    
    # Contact information
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    
    # Address information
    street_address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="Deutschland", max_length=100)
    
    # Legal specializations
    specializations: List[str] = Field(default=[])
    bar_number: Optional[str] = Field(None, max_length=50)  # Anwaltsnummer
    law_firm: Optional[str] = Field(None, max_length=255)
    years_experience: Optional[int] = Field(None, ge=0, le=70)
    
    # Profile settings
    language: str = Field(default="de", max_length=10)
    timezone: str = Field(default="Europe/Berlin", max_length=50)
    bio: Optional[str] = Field(None, max_length=1000)
    
    # System fields
    role: Optional[UserRole] = UserRole.ASSISTANT
    
    @property
    def name(self) -> str:
        """Generate full name from first_name and last_name"""
        if self.title:
            return f"{self.title} {self.first_name} {self.last_name}".strip()
        return f"{self.first_name} {self.last_name}".strip()

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: str = Field(default="general", max_length=100)
    type: TemplateType = TemplateType.DOCUMENT

class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    type: Optional[TemplateType] = None

class ClauseCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    tags: List[str] = Field(default=[])
    language: str = Field(default="de", max_length=10)

class ClipboardCreate(BaseModel):
    content: str = Field(..., min_length=1)
    source_type: SourceType = SourceType.MANUAL
    metadata: Dict[str, Any] = Field(default={})
    expires_at: Optional[datetime] = None

class AIRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None
    max_tokens: int = Field(default=2000, ge=1, le=8000)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    context: str = Field(default="general")

class DocumentGenerateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    document_type: str = Field(..., min_length=1)
    template_content: str = Field(default="")
    variables: Dict[str, Any] = Field(default={})
    template_id: Optional[uuid.UUID] = None
    model: Optional[str] = None

# ============ RESPONSE MODELS ============

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    
    # Enhanced profile fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    
    # Contact information
    phone: Optional[str] = None
    mobile: Optional[str] = None
    
    # Address information
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    # Legal specializations
    specializations: List[str] = []
    law_firm: Optional[str] = None
    years_experience: Optional[int] = None
    
    # Profile settings
    language: str = "de"
    timezone: str = "Europe/Berlin"
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime

class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserResponse

class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    content: str
    category: str
    type: str
    usage_count: int
    created_at: datetime
    updated_at: datetime

class ClauseResponse(BaseModel):
    id: uuid.UUID
    category: str
    title: str
    content: str
    tags: List[str]
    language: str
    is_favorite: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

class ClipboardResponse(BaseModel):
    id: uuid.UUID
    content: str
    source_type: str
    metadata: Dict[str, Any]
    created_at: datetime

class AIResponse(BaseModel):
    content: str
    tokens_used: int
    cost_estimate: float
    generation_time_ms: int
    model_used: str

class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    document_type: str
    created_at: datetime

# ============ PROFILE UPDATE MODELS ============

class UserProfileUpdate(BaseModel):
    # Personal information
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    title: Optional[str] = Field(None, max_length=20)
    
    # Professional information
    company: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    
    # Contact information
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    
    # Address information
    street_address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Legal specializations
    specializations: Optional[List[str]] = None
    bar_number: Optional[str] = Field(None, max_length=50)
    law_firm: Optional[str] = Field(None, max_length=255)
    years_experience: Optional[int] = Field(None, ge=0, le=70)
    
    # Profile settings
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=1000)
    
    # Notification preferences
    email_notifications: Optional[bool] = None
    browser_notifications: Optional[bool] = None
    ai_updates: Optional[bool] = None
    
    # Professional settings
    signature: Optional[str] = Field(None, max_length=2000)
    letterhead: Optional[str] = Field(None, max_length=500)

class UserSettingsUpdate(BaseModel):
    # Notification preferences
    email_notifications: Optional[bool] = None
    browser_notifications: Optional[bool] = None
    ai_updates: Optional[bool] = None
    
    # UI preferences
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, max_length=20)
    
    # AI preferences
    ai_model: Optional[str] = Field(None, max_length=100)
    ai_creativity: Optional[int] = Field(None, ge=0, le=100)
    auto_save: Optional[bool] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]