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
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    role: Optional[UserRole] = UserRole.ASSISTANT

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

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]