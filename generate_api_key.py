#!/usr/bin/env python3
"""
Script to generate API key for ESP32/Node-RED
Run this script to create a new API key for your IoT devices
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DBManager

def main():
    print("=" * 60)
    print("API Key Generator for ESP32/Node-RED")
    print("=" * 60)
    
    # Get API key name from user
    name = input("\nEnter a name for this API key (e.g., 'Node-RED Production'): ").strip()
    
    if not name:
        print("Error: Name cannot be empty")
        return
    
    # Create database manager
    db_manager = DBManager()
    
    # Create API key
    print(f"\nCreating API key '{name}'...")
    key_obj = db_manager.create_api_key(name)
    
    if not key_obj:
        print("Error: Failed to create API key")
        return
    
    # Display the API key
    print("\n" + "=" * 60)
    print("✅ API Key Created Successfully!")
    print("=" * 60)
    print(f"\nName: {key_obj.name}")
    print(f"API Key: {key_obj.key}")
    print(f"Created: {key_obj.created_at}")
    print(f"Rate Limit: {key_obj.rate_limit} requests/minute")
    
    print("\n" + "⚠️  IMPORTANT" + " " * 47)
    print("=" * 60)
    print("This is the ONLY time you will see the full API key.")
    print("Please save it securely now!")
    print("\nTo use this API key in Node-RED:")
    print("1. Open your Node-RED flow")
    print("2. Edit the HTTP Request node (POST to /api/predict)")
    print("3. Add a header:")
    print(f"   Name: X-API-Key")
    print(f"   Value: {key_obj.key}")
    print("=" * 60)
    
    # Ask if user wants to save to file
    save = input("\nDo you want to save this API key to a file? (y/n): ").strip().lower()
    
    if save == 'y':
        filename = f"api_key_{name.replace(' ', '_').lower()}.txt"
        with open(filename, 'w') as f:
            f.write(f"API Key Name: {key_obj.name}\n")
            f.write(f"API Key: {key_obj.key}\n")
            f.write(f"Created: {key_obj.created_at}\n")
            f.write(f"\nNode-RED Header Configuration:\n")
            f.write(f"Header Name: X-API-Key\n")
            f.write(f"Header Value: {key_obj.key}\n")
        
        print(f"\n✅ API key saved to: {filename}")
        print("⚠️  Keep this file secure and delete it after configuring Node-RED!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
