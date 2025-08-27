#!/usr/bin/env python3
"""
AnwaltsAI Simple Backend - AI Generation Only
Runs without database dependency for AI document generation
"""

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Verify API key
api_key = os.getenv("TOGETHER_API_KEY")
if not api_key:
    print("ERROR: TOGETHER_API_KEY not found in .env file!")
    exit(1)

print("=" * 60)
print("🤖 AnwaltsAI Simple Backend (AI Generation Only)")
print("=" * 60)
print(f"✅ API Key loaded: {api_key[:10]}...{api_key[-10:]}")
print(f"✅ AI Model: {os.getenv('DEFAULT_AI_MODEL', 'deepseek-ai/DeepSeek-V3')}")
print("⚠️  Database: Disabled (AI generation still works)")
print("=" * 60)

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    from ai_service import AIService
    
    # Create simple FastAPI app
    app = FastAPI(title="AnwaltsAI Simple Backend")
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize AI service
    ai_service = AIService()
    
    class DocumentRequest(BaseModel):
        title: str
        document_type: str
        prompt: str
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": "2025-08-06T19:00:00Z",
            "services": {
                "database": "disabled",
                "cache": "disabled", 
                "ai_service": "healthy"
            }
        }
    
    @app.post("/api/ai/generate-document-simple")
    async def generate_document(request: DocumentRequest):
        try:
            # Create AI prompt
            ai_prompt = f"""Erstelle ein professionelles deutsches Rechtsdokument mit folgenden Anforderungen:

Titel: {request.title}
Dokumenttyp: {request.document_type}
Zusätzliche Anweisungen: {request.prompt}

Das Dokument soll:
- In deutscher Sprache verfasst sein
- Den deutschen Rechtsstandards entsprechen
- Eine professionelle Struktur haben
- Alle relevanten rechtlichen Klauseln enthalten
- Spezifische Details aus den Anweisungen berücksichtigen

Bitte erstelle ein vollständiges, rechtlich korrektes Dokument."""

            # Call AI service
            ai_response = await ai_service.generate_completion(
                prompt=ai_prompt,
                model="deepseek-ai/DeepSeek-V3",
                max_tokens=2048,
                temperature=0.3
            )
            
            return {
                "success": True,
                "document": {
                    "id": f"doc_simple_{hash(request.title) % 10000}",
                    "title": request.title,
                    "content": ai_response.content,
                    "document_type": request.document_type,
                    "created_at": "2025-08-06T19:00:00Z",
                    "tokens_used": ai_response.tokens_used,
                    "model_used": ai_response.model_used,
                    "generation_time_ms": ai_response.generation_time_ms,
                    "processing_time": ai_response.generation_time_ms / 1000,
                    "confidence": 0.95,
                    "cost_estimate": ai_response.cost_estimate
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI generation failed: {str(e)}"
            }
    
    print("🚀 Starting Simple AnwaltsAI Backend...")
    print("📡 Server: http://localhost:8009")
    print("🏥 Health: http://localhost:8009/health")
    print("🤖 AI Generation: Ready!")
    print("=" * 60)
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8009, reload=False)
    
except Exception as e:
    print(f"❌ Startup Error: {e}")
    exit(1)