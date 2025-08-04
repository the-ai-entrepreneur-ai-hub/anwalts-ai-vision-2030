#!/usr/bin/env python3
"""
Simple server startup script for AnwaltsAI Backend
"""

import asyncio
import uvicorn
import os
from pathlib import Path

# Load environment variables if .env file exists
def load_env():
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env")
    else:
        print("⚠️ No .env file found. Using default configuration.")
        print("   Create .env from .env.example for production settings.")

def main():
    print("🚀 Starting AnwaltsAI Backend Server")
    print("=" * 50)
    
    # Load environment variables
    load_env()
    
    # Configuration
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    print(f"Server: http://{host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Reload: {reload}")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if reload else "warning"
    )

if __name__ == "__main__":
    main()