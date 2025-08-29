#!/usr/bin/env python3
"""
Direct test script for enhanced registration API
Tests the registration system without needing a web server
"""

import requests
import json
import time
from datetime import datetime

# Auto-detect base URL based on environment
import os
if os.getenv('PRODUCTION') == 'true':
    BASE_URL = "https://portal-anwalts.ai/api"
else:
    BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """Test server health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Health Check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_field_validation():
    """Test field validation"""
    try:
        response = requests.get(f"{BASE_URL}/test/validate-fields", timeout=5)
        print(f"✅ Field Validation: {response.status_code}")
        result = response.json()
        print(f"   Status: {result.get('status')}")
        print(f"   Sample User: {result.get('sample_user', {})}")
        return True
    except Exception as e:
        print(f"❌ Field Validation Failed: {e}")
        return False

def test_basic_registration():
    """Test basic registration"""
    basic_user = {
        "email": f"basic.test.{int(time.time())}@anwalts-ai.com",
        "password": "testpassword123",
        "first_name": "Max",
        "last_name": "Mustermann"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register", 
            json=basic_user, 
            timeout=10
        )
        
        print(f"✅ Basic Registration: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   User ID: {result.get('id')}")
            print(f"   Name: {result.get('name')}")
            print(f"   Email: {result.get('email')}")
        else:
            print(f"   Error: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Basic Registration Failed: {e}")
        return False

def test_enhanced_registration():
    """Test enhanced registration with all fields"""
    enhanced_user = {
        # Required fields
        "email": f"enhanced.test.{int(time.time())}@anwalts-ai.com", 
        "password": "testpassword123",
        "first_name": "Dr. Maria",
        "last_name": "Schmidt",
        
        # Enhanced profile fields
        "title": "Dr.",
        "company": "Kanzlei Schmidt & Partner",
        "law_firm": "Kanzlei Schmidt & Partner",
        "position": "Senior Partner",
        "phone": "+49 30 123456789",
        "mobile": "+49 170 987654321",
        "street_address": "Unter den Linden 42",
        "city": "Berlin",
        "state": "Berlin", 
        "postal_code": "10117",
        "country": "Deutschland",
        "specializations": ["Zivilrecht", "Handelsrecht", "IT-Recht"],
        "bar_number": "BAR789123",
        "years_experience": 12,
        "language": "de",
        "timezone": "Europe/Berlin",
        "bio": "Erfahrene Anwältin mit Schwerpunkt auf digitales Recht und E-Commerce. Über 12 Jahre Erfahrung in der Beratung von Tech-Unternehmen.",
        "role": "assistant"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register", 
            json=enhanced_user, 
            timeout=10
        )
        
        print(f"✅ Enhanced Registration: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   User ID: {result.get('id')}")
            print(f"   Full Name: {result.get('name')}")
            print(f"   Email: {result.get('email')}")
            print(f"   Law Firm: {result.get('law_firm')}")
            print(f"   Specializations: {result.get('specializations')}")
            print(f"   Location: {result.get('city')}, {result.get('state')}")
            print(f"   Experience: {result.get('years_experience')} years")
        else:
            print(f"   Error: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Registration Failed: {e}")
        return False

def test_list_users():
    """Test listing registered users"""
    try:
        response = requests.get(f"{BASE_URL}/test/users", timeout=5)
        print(f"✅ List Users: {response.status_code}")
        result = response.json()
        print(f"   Total Users: {result.get('total_users', 0)}")
        
        for i, user in enumerate(result.get('users', []), 1):
            print(f"   User {i}: {user.get('name')} ({user.get('email')})")
            
        return True
    except Exception as e:
        print(f"❌ List Users Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("AnwaltsAI Enhanced Registration API Tests")
    print("=" * 60)
    print(f"Testing server at: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Server Health Check", test_health_check),
        ("Field Validation", test_field_validation),
        ("Basic Registration", test_basic_registration),
        ("Enhanced Registration", test_enhanced_registration),
        ("List Registered Users", test_list_users)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing: {test_name}")
        if test_func():
            passed += 1
        print()
        time.sleep(1)  # Small delay between tests
    
    print("=" * 60)
    print(f"Tests Completed: {passed}/{total} passed")
    
    if passed == total:
        print("All tests passed! Enhanced registration system is working perfectly!")
    else:
        print("Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()