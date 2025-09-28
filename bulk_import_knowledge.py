#!/usr/bin/env python3
"""
Bulk Import Knowledge for SRM Guide Bot
Import training data from JSON files or create sample data
"""

import asyncio
import json
from datetime import datetime
from train_ai_custom import CustomAITrainer

# Sample training data for SRM University
SAMPLE_KNOWLEDGE = [
    {
        "category": "admissions",
        "question": "What are the admission requirements for B.Tech?",
        "answer": "For B.Tech admission, you need: 1) 10+2 with Physics, Chemistry, and Mathematics with minimum 60% aggregate, 2) Valid JEE Main score or SRMJEEE score, 3) Age should be between 17-25 years as of December 31st of the admission year.",
        "tags": ["admissions", "btech", "requirements", "eligibility"],
        "confidence_score": 0.95
    },
    {
        "category": "admissions",
        "question": "How do I apply for SRM University?",
        "answer": "To apply for SRM University: 1) Visit the official website www.srmist.edu.in, 2) Click on 'Admissions' and select your program, 3) Fill the online application form, 4) Upload required documents, 5) Pay the application fee, 6) Submit and wait for counseling call.",
        "tags": ["admissions", "application", "process", "online"],
        "confidence_score": 0.90
    },
    {
        "category": "courses",
        "question": "What engineering courses are available at SRM?",
        "answer": "SRM offers various B.Tech programs: Computer Science Engineering, Artificial Intelligence, Data Science, Mechanical Engineering, Civil Engineering, Electrical & Electronics, Electronics & Communication, Biotechnology, Chemical Engineering, and more. Each program has multiple specializations.",
        "tags": ["courses", "engineering", "btech", "specializations"],
        "confidence_score": 0.92
    },
    {
        "category": "courses",
        "question": "What is the duration of B.Tech program?",
        "answer": "The B.Tech program at SRM University is a 4-year (8 semesters) full-time undergraduate program. Each semester is approximately 6 months long, and the program follows the academic calendar set by the university.",
        "tags": ["courses", "duration", "semesters", "academic"],
        "confidence_score": 0.88
    },
    {
        "category": "hostel",
        "question": "What are the hostel facilities at SRM?",
        "answer": "SRM provides modern hostel facilities with: 1) AC and non-AC rooms, 2) 24/7 security, 3) Wi-Fi connectivity, 4) Modern amenities, 5) Separate hostels for boys and girls, 6) Nutritious food in dining halls, 7) Medical facilities, 8) Laundry services.",
        "tags": ["hostel", "facilities", "accommodation", "amenities"],
        "confidence_score": 0.85
    },
    {
        "category": "fees",
        "question": "What is the fee structure for B.Tech?",
        "answer": "B.Tech fees at SRM vary by specialization: Computer Science Engineering costs around ₹2.5-3.5 lakhs per year, while other branches range from ₹2-3 lakhs per year. This includes tuition fees, hostel charges, and other academic expenses. Scholarships are available based on merit.",
        "tags": ["fees", "btech", "cost", "scholarships"],
        "confidence_score": 0.80
    },
    {
        "category": "placements",
        "question": "What are the placement statistics at SRM?",
        "answer": "SRM has excellent placement records: 1) 95%+ placement rate, 2) Average package: ₹6-8 LPA, 3) Highest package: ₹50+ LPA, 4) Top recruiters: Google, Microsoft, Amazon, TCS, Infosys, Wipro, 5) Regular placement drives and career counseling.",
        "tags": ["placements", "statistics", "companies", "career"],
        "confidence_score": 0.90
    },
    {
        "category": "campus",
        "question": "Where are SRM campuses located?",
        "answer": "SRM has multiple campuses: 1) Kattankulathur (Main Campus) - Chennai, 2) Vadapalani - Chennai, 3) Ramapuram - Chennai, 4) Delhi NCR - Ghaziabad, 5) Sonepat - Haryana, 6) Amaravati - Andhra Pradesh. Each campus offers different programs and facilities.",
        "tags": ["campus", "locations", "chennai", "delhi", "haryana"],
        "confidence_score": 0.88
    },
    {
        "category": "events",
        "question": "What events and activities happen at SRM?",
        "answer": "SRM hosts various events: 1) Technical symposiums and hackathons, 2) Cultural festivals and competitions, 3) Sports tournaments, 4) Industry workshops and seminars, 5) Student clubs and organizations, 6) National and international conferences, 7) Alumni meets and networking events.",
        "tags": ["events", "activities", "festivals", "workshops", "clubs"],
        "confidence_score": 0.85
    },
    {
        "category": "academics",
        "question": "What is the academic structure at SRM?",
        "answer": "SRM follows a semester-based academic structure: 1) 8 semesters over 4 years, 2) Credit-based system, 3) Continuous evaluation with mid-semester and end-semester exams, 4) Project work and internships, 5) Industry collaborations, 6) Research opportunities, 7) International exchange programs.",
        "tags": ["academics", "semester", "credits", "evaluation", "projects"],
        "confidence_score": 0.87
    }
]

async def bulk_import_sample_data():
    """Import sample knowledge data"""
    print("🚀 Bulk Import Sample Knowledge Data")
    print("=" * 50)
    
    trainer = CustomAITrainer()
    
    # Import sample data
    result = await trainer.add_bulk_knowledge(SAMPLE_KNOWLEDGE)
    
    print(f"\n📊 Import Results:")
    print(f"   Success: {result['success']}")
    print(f"   Errors: {result['errors']}")
    
    # Validate quality
    await trainer.validate_knowledge_quality()
    
    return result

async def import_from_json_file(filename: str):
    """Import knowledge from JSON file"""
    print(f"📁 Importing from: {filename}")
    print("=" * 50)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
        
        trainer = CustomAITrainer()
        result = await trainer.add_bulk_knowledge(knowledge_data)
        
        print(f"\n📊 Import Results:")
        print(f"   Success: {result['success']}")
        print(f"   Errors: {result['errors']}")
        
        return result
        
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return {"success": 0, "errors": 1}
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON file: {filename}")
        return {"success": 0, "errors": 1}
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return {"success": 0, "errors": 1}

async def export_sample_template():
    """Export sample template for knowledge import"""
    filename = "knowledge_template.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_KNOWLEDGE, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Sample template exported to: {filename}")
    print("📝 Use this template to create your own knowledge data")

async def main():
    """Main function"""
    print("🎓 Knowledge Import Tool for SRM Guide Bot")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Import sample knowledge data")
        print("2. Import from JSON file")
        print("3. Export sample template")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await bulk_import_sample_data()
        elif choice == "2":
            filename = input("Enter JSON filename: ").strip()
            if filename:
                await import_from_json_file(filename)
            else:
                print("❌ Please enter a filename")
        elif choice == "3":
            await export_sample_template()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())



