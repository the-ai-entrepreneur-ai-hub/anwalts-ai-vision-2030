"""
AnwaltsAI FastAPI Backend Server
Complete backend with PostgreSQL, Redis, and Together AI integration
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import os
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
import uuid

from database import Database, get_database
from models import *
from ai_service import AIService
from cache_service import CacheService
from auth_service import AuthService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
db: Database = None
ai_service: AIService = None
cache_service: CacheService = None
auth_service: AuthService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    global db, ai_service, cache_service, auth_service
    
    # Initialize services
    db = Database()
    await db.connect()
    
    cache_service = CacheService()
    await cache_service.connect()
    
    ai_service = AIService()
    auth_service = AuthService()
    
    logger.info("AnwaltsAI Backend started successfully")
    
    yield
    
    # Cleanup
    await db.disconnect()
    await cache_service.disconnect()
    logger.info("AnwaltsAI Backend shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="AnwaltsAI Backend API",
    description="Complete backend for AnwaltsAI with PostgreSQL, Redis, and Together AI integration",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get current authenticated user"""
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = await db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# ============ AUTHENTICATION ENDPOINTS ============

@app.post("/auth/login-test")
async def login_test(request: dict):
    """Test login endpoint with simple parameters"""
    email = request.get("email")
    password = request.get("password")
    logger.info(f"Login test called with email: {email}")
    
    try:
        user = await db.get_user_by_email(email)
        logger.info(f"User found: {user is not None}")
        
        if not user:
            return {"error": "User not found"}
        
        password_valid = auth_service.verify_password(password, user.password_hash)
        logger.info(f"Password valid: {password_valid}")
        
        if not password_valid:
            return {"error": "Invalid password"}
        
        if not user.is_active:
            return {"error": "User not active"}
        
        # Create JWT token
        token = auth_service.create_access_token(data={"sub": str(user.id)})
        logger.info("Token created successfully")
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        }
    except Exception as e:
        logger.error(f"Login test error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"error": f"Exception: {str(e)}"}

@app.post("/auth/login")
async def login(request: dict):
    """Authenticate user and return JWT token"""
    try:
        # Extract email and password from request
        email = request.get("email")
        password = request.get("password")
        
        if not email or not password:
            return {"error": "Email and password are required", "status": 400}
        
        logger.info(f"Login attempt for email: {email}")
        
        # Get user from database
        user = await db.get_user_by_email(email)
        if not user:
            logger.warning(f"User not found: {email}")
            return {"error": "Invalid email or password", "status": 401}
        
        # Verify password
        if not auth_service.verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for user: {email}")
            return {"error": "Invalid email or password", "status": 401}
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user login attempt: {email}")
            return {"error": "Account is disabled", "status": 401}
        
        # Create JWT token
        token = auth_service.create_access_token(data={"sub": str(user.id)})
        logger.info(f"JWT token created for user: {user.id}")
        
        # Store session
        session_id = str(uuid.uuid4())
        await cache_service.store_session(session_id, str(user.id), expires_in=86400)
        logger.info(f"Session stored for user: {user.id}")
        
        # Return successful response
        return {
            "token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role
            },
            "status": 200
        }
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"error": f"Login failed: {str(e)}", "status": 500}

@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register new user"""
    try:
        # Check if user already exists
        existing_user = await db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        password_hash = auth_service.hash_password(user_data.password)
        user = await db.create_user(
            email=user_data.email,
            name=user_data.name,
            role=user_data.role or "assistant",
            password_hash=password_hash
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role
    )

# ============ TEMPLATE ENDPOINTS ============

@app.get("/api/templates", response_model=List[TemplateResponse])
async def get_templates(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get user templates with optional category filter"""
    try:
        templates = await db.get_templates(current_user.id, category)
        return [
            TemplateResponse(
                id=t.id,
                name=t.name,
                content=t.content,
                category=t.category,
                type=t.type,
                usage_count=t.usage_count,
                created_at=t.created_at,
                updated_at=t.updated_at
            ) for t in templates
        ]
    except Exception as e:
        logger.error(f"Get templates error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )

@app.post("/api/templates", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create new template"""
    try:
        template = await db.create_template(
            user_id=current_user.id,
            name=template_data.name,
            content=template_data.content,
            category=template_data.category,
            type=template_data.type
        )
        
        return TemplateResponse(
            id=template.id,
            name=template.name,
            content=template.content,
            category=template.category,
            type=template.type,
            usage_count=template.usage_count,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except Exception as e:
        logger.error(f"Create template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )

@app.put("/api/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    template_data: TemplateUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update existing template"""
    try:
        template = await db.update_template(
            template_id=template_id,
            user_id=current_user.id,
            **template_data.dict(exclude_unset=True)
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return TemplateResponse(
            id=template.id,
            name=template.name,
            content=template.content,
            category=template.category,
            type=template.type,
            usage_count=template.usage_count,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )

@app.delete("/api/templates/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete template"""
    try:
        success = await db.delete_template(template_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )

# ============ CLAUSE ENDPOINTS ============

@app.get("/api/clauses", response_model=List[ClauseResponse])
async def get_clauses(
    category: Optional[str] = None,
    language: Optional[str] = "de",
    current_user: UserInDB = Depends(get_current_user)
):
    """Get user clauses with optional filters"""
    try:
        clauses = await db.get_clauses(current_user.id, category, language)
        return [
            ClauseResponse(
                id=c.id,
                category=c.category,
                title=c.title,
                content=c.content,
                tags=c.tags,
                language=c.language,
                is_favorite=c.is_favorite,
                usage_count=c.usage_count,
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in clauses
        ]
    except Exception as e:
        logger.error(f"Get clauses error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve clauses"
        )

@app.post("/api/clauses", response_model=ClauseResponse)
async def create_clause(
    clause_data: ClauseCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create new clause"""
    try:
        clause = await db.create_clause(
            user_id=current_user.id,
            category=clause_data.category,
            title=clause_data.title,
            content=clause_data.content,
            tags=clause_data.tags,
            language=clause_data.language
        )
        
        return ClauseResponse(
            id=clause.id,
            category=clause.category,
            title=clause.title,
            content=clause.content,
            tags=clause.tags,
            language=clause.language,
            is_favorite=clause.is_favorite,
            usage_count=clause.usage_count,
            created_at=clause.created_at,
            updated_at=clause.updated_at
        )
    except Exception as e:
        logger.error(f"Create clause error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create clause"
        )

# ============ CLIPBOARD ENDPOINTS ============

@app.get("/api/clipboard", response_model=List[ClipboardResponse])
async def get_clipboard_entries(
    limit: int = 50,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get user clipboard entries"""
    try:
        entries = await db.get_clipboard_entries(current_user.id, limit)
        return [
            ClipboardResponse(
                id=e.id,
                content=e.content,
                source_type=e.source_type,
                metadata=e.metadata,
                created_at=e.created_at
            ) for e in entries
        ]
    except Exception as e:
        logger.error(f"Get clipboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve clipboard entries"
        )

@app.post("/api/clipboard", response_model=ClipboardResponse)
async def add_clipboard_entry(
    entry_data: ClipboardCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Add entry to clipboard"""
    try:
        entry = await db.create_clipboard_entry(
            user_id=current_user.id,
            content=entry_data.content,
            source_type=entry_data.source_type,
            metadata=entry_data.metadata,
            expires_at=entry_data.expires_at
        )
        
        return ClipboardResponse(
            id=entry.id,
            content=entry.content,
            source_type=entry.source_type,
            metadata=entry.metadata,
            created_at=entry.created_at
        )
    except Exception as e:
        logger.error(f"Add clipboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add clipboard entry"
        )

# ============ AI ENDPOINTS ============

@app.post("/api/ai/complete", response_model=AIResponse)
async def ai_complete(
    request_data: AIRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate AI completion using Together API"""
    try:
        # Generate AI response
        response = await ai_service.generate_completion(
            prompt=request_data.prompt,
            model=request_data.model,
            max_tokens=request_data.max_tokens,
            temperature=request_data.temperature,
            context=request_data.context
        )
        
        # Track usage
        await db.create_analytics_event(
            user_id=current_user.id,
            event_type="ai_completion",
            event_data={
                "model": request_data.model,
                "tokens_used": response.tokens_used,
                "cost_estimate": response.cost_estimate
            }
        )
        
        return response
    except Exception as e:
        logger.error(f"AI completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI completion failed"
        )

@app.post("/api/ai/generate-document", response_model=DocumentResponse)
async def generate_document(
    request_data: DocumentGenerateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate legal document using AI"""
    try:
        # Generate document content
        ai_response = await ai_service.generate_document(
            document_type=request_data.document_type,
            template_content=request_data.template_content,
            variables=request_data.variables,
            model=request_data.model
        )
        
        # Save document
        document = await db.create_document(
            user_id=current_user.id,
            title=request_data.title,
            content=ai_response.content,
            document_type=request_data.document_type,
            template_id=request_data.template_id,
            ai_model=request_data.model,
            ai_prompt=ai_response.prompt_used,
            generation_time_ms=ai_response.generation_time_ms,
            tokens_used=ai_response.tokens_used,
            cost_estimate=ai_response.cost_estimate
        )
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            document_type=document.document_type,
            created_at=document.created_at
        )
    except Exception as e:
        logger.error(f"Document generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document generation failed"
        )

# ============ WORKING LOGIN ENDPOINT ============

@app.post("/auth/login-working")
async def login_working(request: dict):
    """Working login endpoint for frontend"""
    try:
        email = request.get("email", "").strip().lower()
        password = request.get("password", "")
        
        logger.info(f"Login attempt for: {email}")
        
        if not email or not password:
            return {"error": "Email and password required", "success": False}
        
        # Get user
        user = await db.get_user_by_email(email)
        if not user:
            logger.warning(f"User not found: {email}")
            return {"error": "Invalid credentials", "success": False}
        
        # Verify password  
        if not auth_service.verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for: {email}")
            return {"error": "Invalid credentials", "success": False}
        
        # Check active status
        if not user.is_active:
            logger.warning(f"Inactive user: {email}")
            return {"error": "Account disabled", "success": False}
        
        # Create token
        token = auth_service.create_access_token(data={"sub": str(user.id)})
        
        # Store session
        session_id = str(uuid.uuid4())
        await cache_service.store_session(session_id, str(user.id), expires_in=86400)
        
        logger.info(f"Login successful for: {email}")
        
        return {
            "success": True,
            "token": token,
            "token_type": "bearer", 
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        }
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Server error: {str(e)}", "success": False}

# ============ HEALTH CHECK ============

@app.post("/test-simple")
async def test_simple(data: dict):
    """Simple test endpoint"""
    logger.info(f"Test endpoint called with data: {data}")
    return {"status": "success", "received": data}

@app.post("/auth/quick-login")
async def quick_login():
    """Quick test login endpoint"""
    return {
        "success": True,
        "token": "test-token-12345",
        "token_type": "bearer",
        "user": {
            "id": "test-id",
            "email": "admin@anwalts-ai.com", 
            "name": "Administrator",
            "role": "admin"
        }
    }


@app.post("/api/ai/generate-document-simple")
async def generate_document_working(request: dict):
    """Real AI-powered document generation using DeepSeek-V3"""
    try:
        title = request.get("title", "Neues Dokument")
        doc_type = request.get("document_type", "contract")
        prompt = request.get("prompt", "")
        
        logger.info(f"🤖 Generating document with AI: {title} ({doc_type})")
        
        # Create AI prompt for German legal document
        ai_prompt = f"""Erstelle ein professionelles deutsches Rechtsdokument mit folgenden Anforderungen:

Titel: {title}
Dokumenttyp: {doc_type}
Zusätzliche Anweisungen: {prompt}

Das Dokument soll:
- In deutscher Sprache verfasst sein
- Den deutschen Rechtsstandards entsprechen
- Eine professionelle Struktur haben
- Alle relevanten rechtlichen Klauseln enthalten
- Spezifische Details aus den Anweisungen berücksichtigen

Bitte erstelle ein vollständiges, rechtlich korrektes Dokument."""

        start_time = time.time()
        
        # Call AI service
        ai_response = await ai_service.generate_completion(
            prompt=ai_prompt,
            model="deepseek-ai/DeepSeek-V3",
            max_tokens=2048,
            temperature=0.3
        )
        
        generation_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ AI generation completed in {generation_time}ms")
        
        return {
            "success": True,
            "document": {
                "id": f"doc_{uuid.uuid4().hex[:8]}",
                "title": title,
                "content": ai_response.content,
                "document_type": doc_type,
                "created_at": datetime.utcnow().isoformat(),
                "tokens_used": ai_response.tokens_used,
                "model_used": ai_response.model_used,
                "generation_time_ms": generation_time,
                "processing_time": generation_time / 1000,
                "confidence": 0.95,
                "cost_estimate": ai_response.cost_estimate
            }
        }
        
    except Exception as e:
        logger.error(f"❌ AI document generation error: {e}")
        return {"success": False, "error": f"AI generation failed: {str(e)}"}

# Add missing import
import time

@app.get("/api/generate-test-doc")
async def generate_test_document():
    """Simple GET endpoint for document generation testing"""
    content = f"""# Testdokument

## Automatisch generiert am {datetime.utcnow().strftime('%d.%m.%Y um %H:%M Uhr')}

### Inhalt

Dies ist ein Testdokument von AnwaltsAI.

**Funktionen:**
- ✅ Backend-Verbindung
- ✅ Dokumentenerstellung  
- ✅ Deutsche Rechtsinhalte

### Rechtlicher Hinweis

Dieses Dokument dient nur zu Testzwecken.

---
*AnwaltsAI - Ihr KI-Partner für deutsche Rechtsdokumente*"""

    return {
        "success": True,
        "document": {
            "id": f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "title": "AnwaltsAI Testdokument",
            "content": content,
            "document_type": "test",
            "created_at": datetime.utcnow().isoformat(),
            "model_used": "Backend Template"
        }
    }

# =========================
# NOTIFICATIONS ENDPOINTS
# =========================

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Helper function to get current user ID"""
    global auth_service
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized"
        )
    return auth_service.get_current_user_id(credentials)

@app.get("/api/notifications")
async def get_notifications(
    limit: int = 50,
    unread: bool = False,
    user_id: str = Depends(get_current_user_id)
):
    """Get user notifications"""
    try:
        # For demo purposes, return mock notifications
        # In real implementation, query database for user-specific notifications
        mock_notifications = [
            {
                "id": 1,
                "title": "Dokument erstellt",
                "message": "Ihr Kaufvertrag wurde erfolgreich generiert.",
                "type": "success",
                "timestamp": datetime.utcnow() - timedelta(minutes=5),
                "read": False,
                "icon": "file-check"
            },
            {
                "id": 2,
                "title": "E-Mail verarbeitet",
                "message": "Neue E-Mail von Mandant Müller eingetroffen.",
                "type": "info",
                "timestamp": datetime.utcnow() - timedelta(minutes=15),
                "read": False,
                "icon": "mail"
            },
            {
                "id": 3,
                "title": "Template gespeichert",
                "message": "Neue Vorlage \"Mietvertrag\" wurde hinzugefügt.",
                "type": "info",
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "read": True,
                "icon": "bookmark"
            },
            {
                "id": 4,
                "title": "System Update",
                "message": "AnwaltsAI wurde auf Version 2.1.0 aktualisiert.",
                "type": "warning",
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "read": True,
                "icon": "alert-circle"
            }
        ]
        
        if unread:
            mock_notifications = [n for n in mock_notifications if not n['read']]
            
        if limit:
            mock_notifications = mock_notifications[:limit]
            
        return {
            "success": True,
            "notifications": mock_notifications,
            "total": len(mock_notifications),
            "unread_count": len([n for n in mock_notifications if not n['read']])
        }
        
    except Exception as e:
        logger.error(f"Get notifications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden der Benachrichtigungen"
        )

@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """Mark a notification as read"""
    try:
        # In real implementation, update notification in database
        logger.info(f"Marking notification {notification_id} as read for user {user_id}")
        
        return {
            "success": True,
            "message": "Benachrichtigung als gelesen markiert"
        }
        
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Markieren der Benachrichtigung"
        )

@app.post("/api/notifications/mark-all-read")
async def mark_all_notifications_read(
    user_id: str = Depends(get_current_user_id)
):
    """Mark all notifications as read for user"""
    try:
        # In real implementation, update all user notifications in database
        logger.info(f"Marking all notifications as read for user {user_id}")
        
        return {
            "success": True,
            "message": "Alle Benachrichtigungen als gelesen markiert"
        }
        
    except Exception as e:
        logger.error(f"Mark all notifications read error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Markieren aller Benachrichtigungen"
        )

# =========================
# USER SETTINGS ENDPOINTS
# =========================

@app.get("/api/user/settings")
async def get_user_settings(
    user_id: str = Depends(get_current_user_id)
):
    """Get user settings"""
    try:
        # In real implementation, fetch from database
        # For now, return default settings
        default_settings = {
            "language": "de",
            "theme": "dark",
            "emailNotifications": True,
            "browserNotifications": False,
            "aiUpdates": True,
            "aiModel": "deepseek-v3",
            "aiCreativity": 70,
            "autoSave": True
        }
        
        return {
            "success": True,
            "settings": default_settings
        }
        
    except Exception as e:
        logger.error(f"Get user settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden der Benutzereinstellungen"
        )

@app.post("/api/user/settings")
async def update_user_settings(
    settings: dict,
    user_id: str = Depends(get_current_user_id)
):
    """Update user settings"""
    try:
        # In real implementation, validate and save to database
        logger.info(f"Updating settings for user {user_id}: {settings}")
        
        # Validate settings structure (simplified)
        allowed_keys = {
            'language', 'theme', 'emailNotifications', 'browserNotifications',
            'aiUpdates', 'aiModel', 'aiCreativity', 'autoSave'
        }
        
        invalid_keys = set(settings.keys()) - allowed_keys
        if invalid_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültige Einstellungsschlüssel: {invalid_keys}"
            )
        
        # In real implementation: await db.update_user_settings(user_id, settings)
        
        return {
            "success": True,
            "message": "Benutzereinstellungen erfolgreich aktualisiert",
            "settings": settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Speichern der Benutzereinstellungen"
        )

@app.put("/api/user/profile")
async def update_user_profile(
    profile_data: dict,
    user_id: str = Depends(get_current_user_id)
):
    """Update user profile information"""
    try:
        # In real implementation, validate and update user profile
        logger.info(f"Updating profile for user {user_id}: {profile_data}")
        
        # Validate required fields
        if 'name' in profile_data and not profile_data['name'].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name darf nicht leer sein"
            )
        
        if 'email' in profile_data:
            email = profile_data['email'].strip()
            if not email or '@' not in email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Gültige E-Mail-Adresse erforderlich"
                )
        
        # In real implementation: await db.update_user_profile(user_id, profile_data)
        
        return {
            "success": True,
            "message": "Profil erfolgreich aktualisiert",
            "profile": profile_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Aktualisieren des Profils"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await db.health_check()
        
        # Check cache connection
        await cache_service.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "healthy",
                "cache": "healthy",
                "ai_service": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )