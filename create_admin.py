#!/usr/bin/env python3
"""
Create Default Admin User
Run this script to create the default admin account
"""
from dotenv import load_dotenv
load_dotenv()

from database import DBManager

def main():
    print("=" * 60)
    print("CREATE DEFAULT ADMIN USER")
    print("=" * 60)
    
    db_manager = DBManager()
    
    # Create default admin
    success = db_manager.create_default_admin()
    
    if success:
        print("\n✅ Default admin user created successfully!")
        print("\nLogin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠️  IMPORTANT: Change these credentials after first login!")
    else:
        print("\n❌ Failed to create admin user")
        print("Check logs for details")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
