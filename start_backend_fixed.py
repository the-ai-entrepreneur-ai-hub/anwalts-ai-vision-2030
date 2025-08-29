#!/usr/bin/env python3
"""
Quick backend startup script with environment setup
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def setup_environment():
    """Set up environment variables"""
    # Set Together AI key if not already set
    if not os.getenv('TOGETHER_API_KEY'):
        # You should set this to your actual Together AI key
        os.environ['TOGETHER_API_KEY'] = 'your_together_api_key_here'
        print("⚠️  Warning: Using placeholder Together API key. Please set your actual key!")
    
    # Set other required environment variables
    os.environ['DATABASE_URL'] = 'sqlite:///./anwalts_ai.db'
    os.environ['REDIS_URL'] = 'redis://localhost:6379'
    os.environ['JWT_SECRET'] = 'development-jwt-secret-change-in-production'
    
    print("✅ Environment variables set")

def start_backend():
    """Start the FastAPI backend server"""
    try:
        # Change to backend directory
        os.chdir('backend')
        
        print("🚀 Starting AnwaltsAI Backend Server...")
        print("📍 Backend will be available at: http://localhost:8000")
        print("📋 Health check: http://localhost:8000/health")
        print("📚 API docs: http://localhost:8000/docs")
        
        # Start uvicorn server
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload',
            '--log-level', 'info'
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Setting up AnwaltsAI Backend...")
    setup_environment()
    
    print("\n" + "="*50)
    print("AnwaltsAI Backend Server Starting...")
    print("="*50)
    
    start_backend()