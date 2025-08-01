#!/usr/bin/env python3
"""
Quick PDF test
"""

import requests

def quick_test():
    try:
        # Test health first
        health = requests.get("http://localhost:8003/health", timeout=10)
        print(f"Health: {health.status_code}")
        
        if health.status_code == 200:
            print("Server is responding!")
        
    except Exception as e:
        print(f"Server test failed: {e}")

if __name__ == "__main__":
    quick_test()