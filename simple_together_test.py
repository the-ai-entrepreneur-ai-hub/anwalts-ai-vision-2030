#!/usr/bin/env python3
"""
Simple Together API Test - Just check if API works
"""

import os
import asyncio
import httpx

async def test_together_simple():
    """Simple test of Together API"""
    print("🧪 Testing Together API...")
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("❌ TOGETHER_API_KEY not set")
        print("Set it with: set TOGETHER_API_KEY=your_key")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-ai/DeepSeek-V3",
                    "messages": [{"role": "user", "content": "Test: Say 'Hello from Together API'"}],
                    "max_tokens": 50
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ Together API working!")
                print(f"   Response: {content}")
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_together_simple())
    if success:
        print("\n🚀 Together API is working - ready to connect frontend!")
    else:
        print("\n❌ Fix API issues first")