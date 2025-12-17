#!/usr/bin/env python3
"""
Database Migration: Add role and is_active to users table
"""
from dotenv import load_dotenv
load_dotenv()

from database import DBManager
from sqlalchemy import text

def main():
    print("=" * 60)
    print("MIGRATING DATABASE: Adding role and is_active columns")
    print("=" * 60)
    
    db_manager = DBManager()
    session = db_manager.get_session()
    
    try:
        # Add role column
        print("\n1. Adding 'role' column...")
        session.execute(text("""
            ALTER TABLE users 
            ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'
        """))
        print("   ✅ Role column added")
        
        # Add is_active column
        print("\n2. Adding 'is_active' column...")
        session.execute(text("""
            ALTER TABLE users 
            ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE
        """))
        print("   ✅ is_active column added")
        
        # Set admin user to role='admin'
        print("\n3. Setting admin user role...")
        session.execute(text("""
            UPDATE users 
            SET role = 'admin' 
            WHERE username = 'admin'
        """))
        print("   ✅ Admin user role set")
        
        session.commit()
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Verify
        print("\nVerifying users:")
        result = session.execute(text("SELECT username, role, is_active FROM users"))
        for row in result:
            status = "Active" if row[2] else "Inactive"
            print(f"  - {row[0]}: {row[1]} ({status})")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ MIGRATION FAILED: {e}")
        print("Note: If columns already exist, this is expected.")
    finally:
        db_manager.close_session(session)
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
