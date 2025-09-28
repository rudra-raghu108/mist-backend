#!/usr/bin/env python3
"""
Database initialization script for SRM Guide Bot
"""

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import create_tables, init_db
import asyncio

def main():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    
    try:
        # Create tables
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Initialize database (async)
        asyncio.run(init_db())
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
