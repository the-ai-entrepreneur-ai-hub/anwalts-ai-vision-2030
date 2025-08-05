#!/usr/bin/env python3
"""
AnwaltsAI Backend Startup Script
Loads environment variables and starts the FastAPI server with proper configuration
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Verify critical environment variables
api_key = os.getenv("TOGETHER_API_KEY")
if not api_key:
    print("ERROR: TOGETHER_API_KEY not found in .env file!")
    print("Please check your .env file contains the API key.")
    exit(1)

print("=" * 60)
print("🤖 AnwaltsAI Backend Startup")
print("=" * 60)
print(f"✅ API Key loaded: {api_key[:10]}...{api_key[-10:]}")
print(f"✅ Default AI Model: {os.getenv('DEFAULT_AI_MODEL', 'deepseek-ai/DeepSeek-V3')}")
print(f"✅ Database URL: {os.getenv('DATABASE_URL', 'Not configured')}")
print(f"✅ Redis URL: {os.getenv('REDIS_URL', 'Not configured')}")
print("=" * 60)

# Import and start the server
try:
    import uvicorn
    from main import app
    
    print("🚀 Starting AnwaltsAI Backend Server...")
    print("📡 Server URL: http://localhost:8009")
    print("🏥 Health Check: http://localhost:8009/health")
    print("🔧 API Docs: http://localhost:8009/docs")
    print("=" * 60)
    
    # Start the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8009, 
        reload=False,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install fastapi uvicorn python-dotenv")
    exit(1)
except Exception as e:
    print(f"❌ Startup Error: {e}")
    exit(1)