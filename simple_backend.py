#!/usr/bin/env python3
"""
Simple AnwaltsAI Backend - No Database Required
Just Together API + document generation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AnwaltsAI Simple Backend", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple request/response models
class GenerateRequest(BaseModel):
    prompt: str
    template_id: str = ""

class GenerateResponse(BaseModel):
    document: str
    success: bool = True

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AnwaltsAI Backend Running"}

@app.post("/generate-document")
async def generate_document(request: GenerateRequest):
    """Generate document using Together API - frontend compatible"""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="TOGETHER_API_KEY not configured")
    
    # German legal system prompt
    system_prompt = """Sie sind ein erfahrener deutscher Rechtsanwalt. 
    Erstellen Sie professionelle, rechtlich korrekte deutsche Rechtsdokumente.
    Verwenden Sie präzise deutsche Rechtssprache und aktuelle Gesetze."""
    
    try:
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-ai/DeepSeek-V3",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request.prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                generation_time = int((time.time() - start_time) * 1000)
                logger.info(f"Document generated successfully in {generation_time}ms")
                
                return GenerateResponse(document=content, success=True)
            else:
                logger.error(f"Together API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="AI generation failed")
                
    except httpx.TimeoutException:
        logger.error("Together API timeout")
        raise HTTPException(status_code=504, detail="AI generation timeout")
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/templates")
async def get_templates():
    """Get available templates - simple mock for frontend"""
    return [
        {"id": "1", "name": "Kaufvertrag", "category": "Verträge"},
        {"id": "2", "name": "Mietvertrag", "category": "Verträge"},
        {"id": "3", "name": "Arbeitsvertrag", "category": "Verträge"},
    ]

@app.post("/auth/login")
async def login(credentials: dict):
    """Simple auth for frontend compatibility"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    # Simple hardcoded auth
    if email == "admin@anwalts-ai.com" and password == "admin123":
        return {
            "success": True,
            "token": "simple-auth-token-123",
            "user": {"email": email, "name": "Administrator"}
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/auth/validate")
async def validate_token():
    """Simple token validation"""
    return {"valid": True, "user": {"email": "admin@anwalts-ai.com"}}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Simple AnwaltsAI Backend...")
    print("📡 Backend will run on: http://localhost:5001")
    print("🔑 Default login: admin@anwalts-ai.com / admin123")
    print("🤖 Together API integration enabled")
    
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")