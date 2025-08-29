#!/usr/bin/env python3
"""
Test Together API Integration for AnwaltsAI
This script tests the connection to Together API and verifies document generation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from ai_service import AIService

async def test_together_api():
    """Test Together API connection and document generation"""
    print("🧪 Testing Together API Integration for AnwaltsAI")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("❌ TOGETHER_API_KEY environment variable not set")
        print("\nTo fix this:")
        print("1. Get your API key from https://api.together.xyz/")
        print("2. Set environment variable: TOGETHER_API_KEY=your_key_here")
        print("3. Or create .env file in backend/ folder")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Initialize AI service
    ai_service = AIService()
    
    # Test 1: Health check
    print("\n📋 Test 1: Health Check")
    health = ai_service.health_check()
    print(f"   Health status: {'✅ Healthy' if health else '❌ Not healthy'}")
    
    # Test 2: Simple completion
    print("\n📋 Test 2: Simple German Legal Completion")
    try:
        response = await ai_service.generate_completion(
            prompt="Was ist ein Kaufvertrag nach BGB?",
            max_tokens=200,
            temperature=0.3
        )
        
        print(f"   ✅ Completion successful")
        print(f"   Model: {response.model_used}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_estimate:.6f}")
        print(f"   Time: {response.generation_time_ms}ms")
        print(f"   Preview: {response.content[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Completion failed: {e}")
        return False
    
    # Test 3: Document generation
    print("\n📋 Test 3: German Legal Document Generation")
    try:
        doc_response = await ai_service.generate_document(
            document_type="Mietvertrag",
            variables={
                "mieter_name": "Max Mustermann",
                "vermieter_name": "Maria Beispiel",
                "miete": "1200 Euro",
                "kaution": "3600 Euro"
            }
        )
        
        print(f"   ✅ Document generation successful")
        print(f"   Model: {doc_response.model_used}")
        print(f"   Tokens: {doc_response.tokens_used}")
        print(f"   Cost: ${doc_response.cost_estimate:.6f}")
        print(f"   Time: {doc_response.generation_time_ms}ms")
        print(f"   Preview: {doc_response.content[:150]}...")
        
    except Exception as e:
        print(f"   ❌ Document generation failed: {e}")
        return False
    
    # Test 4: Email response generation
    print("\n📋 Test 4: German Legal Email Response")
    try:
        email_response = await ai_service.generate_email_response(
            original_email="Sehr geehrte Damen und Herren, ich habe Fragen zu meinem Mietvertrag...",
            response_type="professional",
            key_points=["Mietrecht erläutern", "Nächste Schritte aufzeigen"]
        )
        
        print(f"   ✅ Email generation successful")
        print(f"   Model: {email_response.model_used}")
        print(f"   Tokens: {email_response.tokens_used}")
        print(f"   Cost: ${email_response.cost_estimate:.6f}")
        print(f"   Preview: {email_response.content[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Email generation failed: {e}")
        return False
    
    # Test 5: Available models
    print("\n📋 Test 5: Available Models")
    try:
        models = await ai_service.get_available_models()
        print(f"   ✅ Found {len(models)} models")
        for model in models[:3]:  # Show first 3
            print(f"   - {model['id']} ({model.get('context_length', 'N/A')} context)")
        
    except Exception as e:
        print(f"   ⚠️ Model listing failed (but API works): {e}")
    
    print("\n🎉 Together API Integration Test Complete!")
    print("✅ Your AnwaltsAI app is ready to use Together API")
    print("\n📊 Summary:")
    print("- German legal text generation: ✅ Working")
    print("- Document creation: ✅ Working") 
    print("- Email responses: ✅ Working")
    print("- Cost tracking: ✅ Working")
    
    return True

async def test_specific_model(model_name: str):
    """Test a specific model"""
    print(f"\n🔧 Testing specific model: {model_name}")
    
    ai_service = AIService()
    
    try:
        response = await ai_service.generate_completion(
            prompt="Erkläre den Unterschied zwischen Kauf- und Werkvertrag im BGB.",
            model=model_name,
            max_tokens=300
        )
        
        print(f"✅ {model_name} working")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_estimate:.6f}")
        print(f"   Response quality: {'Good' if len(response.content) > 100 else 'Short'}")
        
    except Exception as e:
        print(f"❌ {model_name} failed: {e}")

def main():
    """Main test function"""
    print("AnwaltsAI - Together API Integration Test")
    print("This will test your law firm app's AI capabilities")
    
    # Check if running from correct directory
    if not os.path.exists("backend/ai_service.py"):
        print("❌ Please run this from the Law Firm Vision 2030 directory")
        print("   Current directory should contain backend/ folder")
        return
    
    # Load environment variables if .env exists
    env_file = Path("backend/.env")
    if env_file.exists():
        print(f"📁 Loading environment from {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
    else:
        print("⚠️ No .env file found - using system environment variables")
    
    # Run main test
    try:
        success = asyncio.run(test_together_api())
        if success:
            print("\n🚀 Your AnwaltsAI app is ready for production!")
            print("   Start your backend: python backend/main.py")
            print("   Open your frontend and test document generation")
        else:
            print("\n❌ Setup incomplete - please fix issues above")
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()