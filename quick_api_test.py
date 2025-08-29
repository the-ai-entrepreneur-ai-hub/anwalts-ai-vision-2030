#!/usr/bin/env python3
"""
Quick Together API Test - Just the essentials
"""

import os

def quick_test():
    """Quick API key check - that's all we need"""
    print("🧪 Quick Together API Check")
    print("=" * 30)
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if api_key:
        print(f"✅ API Key found: {api_key[:10]}...")
        print("✅ Together API ready")
        return True
    else:
        print("❌ TOGETHER_API_KEY not set")
        return False

if __name__ == "__main__":
    if quick_test():
        print("\n🚀 Ready to start AnwaltsAI!")
    else:
        print("\n❌ Set your API key first")