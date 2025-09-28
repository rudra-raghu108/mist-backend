#!/usr/bin/env python3
"""
Quick test script to test the backend
"""

import requests
import json

def test_backend():
    """Test the backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Backend Endpoints...")
    
    # Test health
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
        return
    
    # Test scraping status
    try:
        response = requests.get(f"{base_url}/api/scraping/status")
        print(f"✅ Scraping Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Scraped sources: {data.get('summary', {}).get('scraped_data_count', 0)}")
    except Exception as e:
        print(f"❌ Scraping status failed: {e}")
    
    # Test debug scraped data
    try:
        response = requests.get(f"{base_url}/api/debug/scraped-data")
        print(f"✅ Debug Data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Total sources: {data.get('total_sources', 0)}")
            sources = data.get('scraped_data', {})
            for source_id, source_data in sources.items():
                print(f"  - {source_id}: {source_data.get('status', 'unknown')}")
                if 'content' in source_data:
                    content = source_data['content']
                    if 'admission_info' in content:
                        print(f"    📝 Admission items: {len(content['admission_info'])}")
                    if 'sub_pages' in source_data:
                        print(f"    🔗 Sub-pages: {len(source_data['sub_pages'])}")
    except Exception as e:
        print(f"❌ Debug data failed: {e}")
    
    # Test chat with admission query
    try:
        chat_data = {
            "message": "admissions process",
            "user_id": "test_user"
        }
        response = requests.post(f"{base_url}/api/chat", json=chat_data)
        print(f"✅ Chat: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"💬 Response length: {len(data.get('response', ''))}")
            print(f"📝 Response preview: {data.get('response', '')[:200]}...")
    except Exception as e:
        print(f"❌ Chat failed: {e}")

if __name__ == "__main__":
    test_backend()
