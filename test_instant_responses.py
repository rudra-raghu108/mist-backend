#!/usr/bin/env python3
"""
Test script to verify instant AI responses from knowledge database
"""

import requests
import json
import time

def test_instant_responses():
    """Test instant AI responses"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Instant AI Response System...")
    
    # Test questions that should get instant responses
    test_questions = [
        "admissions process",
        "engineering courses",
        "research programs",
        "campus facilities",
        "hostel information"
    ]
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        
        start_time = time.time()
        
        try:
            chat_data = {
                "message": question,
                "user_id": "test_user"
            }
            response = requests.post(f"{base_url}/api/chat", json=chat_data)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                print(f"✅ Response Time: {response_time:.1f}ms")
                print(f"📝 Response Length: {len(response_text)} characters")
                print(f"💬 Preview: {response_text[:150]}...")
                
                # Check if response contains database information
                if "Instant Information from SRM Knowledge Database" in response_text:
                    print("🎯 ✅ Using Knowledge Database (Instant Response)")
                elif "Latest SRM Admission Information" in response_text:
                    print("🎯 ✅ Using Fallback Data (Instant Response)")
                else:
                    print("⚠️ Response format unclear")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    # Test knowledge database status
    print(f"\n📊 Checking Knowledge Database Status...")
    try:
        response = requests.get(f"{base_url}/api/debug/knowledge-database")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database Total Items: {data.get('total_items', 0)}")
            print(f"📅 Last Updated: {data.get('last_updated', 'Unknown')}")
            
            summary = data.get('summary', {})
            for category, count in summary.items():
                print(f"  - {category}: {count} items")
        else:
            print(f"❌ Could not check database status: {response.status_code}")
    except Exception as e:
        print(f"❌ Database check failed: {e}")

if __name__ == "__main__":
    test_instant_responses()
