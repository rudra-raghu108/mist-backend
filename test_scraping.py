#!/usr/bin/env python3
"""
Simple test script to test the scraping functionality
"""

import requests
from bs4 import BeautifulSoup
import json

def test_simple_scraping():
    """Test basic scraping functionality"""
    print("🧪 Testing basic scraping...")
    
    url = "https://www.srmist.edu.in/admissions/"
    
    try:
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        print(f"🌐 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page title
        title = soup.find('title').text.strip() if soup.find('title') else "No title found"
        print(f"📄 Title: {title}")
        
        # Extract main content text
        main_content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])[:10]:
            if tag.text.strip():
                main_content.append({
                    "type": tag.name,
                    "text": tag.text.strip()
                })
        
        print(f"📝 Found {len(main_content)} content elements")
        
        # Extract admission-specific content
        admission_info = []
        for tag in soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.text.strip()
            if any(keyword in text.lower() for keyword in ['admission', 'apply', 'deadline', 'form', 'requirement', 'enrollment', 'entrance', 'exam', 'cutoff', 'merit']):
                if len(text) > 10 and len(text) < 500:
                    admission_info.append(text)
        
        print(f"🎓 Found {len(admission_info)} admission-related items")
        
        # Show first few admission items
        for i, item in enumerate(admission_info[:5]):
            print(f"  {i+1}. {item[:100]}...")
        
        # Find links
        links = []
        for link in soup.find_all('a', href=True)[:10]:
            href = link.get('href')
            if href.startswith('/'):
                href = url.rstrip('/') + href
            elif not href.startswith('http'):
                href = url.rstrip('/') + '/' + href.lstrip('/')
            
            if 'srmist.edu.in' in href:
                links.append({
                    "text": link.text.strip(),
                    "url": href
                })
        
        print(f"🔗 Found {len(links)} relevant links")
        
        return {
            "success": True,
            "title": title,
            "content_count": len(main_content),
            "admission_items": len(admission_info),
            "links_count": len(links),
            "sample_admission": admission_info[:3] if admission_info else []
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    result = test_simple_scraping()
    print("\n" + "="*50)
    print("📊 TEST RESULTS:")
    print(json.dumps(result, indent=2))
