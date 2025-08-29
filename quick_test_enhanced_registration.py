#!/usr/bin/env python3
"""
Quick test of enhanced registration system - validates models directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import UserCreate
from datetime import datetime
import json

def test_basic_model():
    """Test basic UserCreate model"""
    try:
        basic_data = {
            "email": "test@anwalts-ai.com",
            "password": "testpassword123",
            "first_name": "Max",
            "last_name": "Mustermann"
        }
        
        user = UserCreate(**basic_data)
        
        print("Basic Model Test:")
        print(f"  Name: {user.name}")
        print(f"  Email: {user.email}")
        print(f"  Valid: True")
        return True
        
    except Exception as e:
        print(f"  Basic Model Test Failed: {e}")
        return False

def test_enhanced_model():
    """Test enhanced UserCreate model with all fields"""
    try:
        enhanced_data = {
            # Required fields
            "email": "enhanced@anwalts-ai.com",
            "password": "testpassword123", 
            "first_name": "Dr. Maria",
            "last_name": "Schmidt",
            
            # Enhanced fields
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
            "bio": "Erfahrene Anwaltin mit Schwerpunkt auf digitales Recht.",
            "role": "assistant"
        }
        
        user = UserCreate(**enhanced_data)
        
        print("Enhanced Model Test:")
        print(f"  Full Name: {user.name}")
        print(f"  Email: {user.email}")
        print(f"  Law Firm: {user.law_firm}")
        print(f"  Location: {user.city}, {user.state}")
        print(f"  Specializations: {', '.join(user.specializations)}")
        print(f"  Experience: {user.years_experience} years")
        print(f"  Valid: True")
        return True
        
    except Exception as e:
        print(f"  Enhanced Model Test Failed: {e}")
        return False

def test_field_validation():
    """Test field validation rules"""
    print("Field Validation Tests:")
    
    # Test required fields
    try:
        UserCreate(email="test@test.com", password="123", first_name="Test", last_name="User")
        print("  Password too short: FAILED (should have failed)")
        return False
    except Exception:
        print("  Password validation: PASSED")
    
    # Test email validation
    try:
        UserCreate(email="invalid-email", password="testpass123", first_name="Test", last_name="User")
        print("  Invalid email: FAILED (should have failed)")
        return False  
    except Exception:
        print("  Email validation: PASSED")
    
    # Test experience range
    try:
        UserCreate(
            email="test@test.com", 
            password="testpass123", 
            first_name="Test", 
            last_name="User",
            years_experience=100  # Should fail
        )
        print("  Experience range: FAILED (should have failed)")
        return False
    except Exception:
        print("  Experience range validation: PASSED")
    
    return True

def test_api_client_integration():
    """Test API client compatibility"""
    try:
        # Simulate what the API client would send
        enhanced_registration_data = {
            "email": "api.test@anwalts-ai.com",
            "password": "testpassword123",
            "first_name": "API",
            "last_name": "Test",
            "law_firm": "Test Firm",
            "specializations": ["Zivilrecht"],
            "city": "Berlin",
            "country": "Deutschland"
        }
        
        # This should work with our enhanced model
        user = UserCreate(**enhanced_registration_data)
        
        print("API Client Integration:")
        print(f"  Compatible: True")
        print(f"  Name: {user.name}")
        print(f"  Law Firm: {user.law_firm}")
        return True
        
    except Exception as e:
        print(f"  API Client Integration Failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("AnwaltsAI Enhanced Registration Model Validation")
    print("=" * 60)
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        test_basic_model,
        test_enhanced_model,
        test_field_validation,
        test_api_client_integration
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("SUCCESS: All model validation tests passed!")
        print("The enhanced registration system is properly configured.")
        
        print("\nNext steps:")
        print("1. Start the backend server: python backend/test_enhanced_registration.py")
        print("2. Open test page: Client/test-enhanced-registration.html")
        print("3. Test registration with both basic and enhanced forms")
        
    else:
        print("FAILED: Some tests failed. Check the model definitions.")

if __name__ == "__main__":
    main()