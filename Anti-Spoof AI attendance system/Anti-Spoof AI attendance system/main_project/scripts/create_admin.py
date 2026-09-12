"""
Create the first admin account for the attendance system.
Run this script after setting up Firebase.
"""

import sys
sys.path.append('..')  # Add parent directory to path

from firebase.firebase_service import initialize_firebase, create_user, add_admin

def create_first_admin():
    """Create the first admin account."""
    print("=" * 50)
    print("CREATE FIRST ADMIN ACCOUNT")
    print("=" * 50)
    
    # Get admin details from user
    name = input("\nEnter admin name: ").strip()
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password (min 6 chars): ").strip()
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters!")
        return
    
    # Confirm
    print("\n📋 Admin Details:")
    print(f"  Name: {name}")
    print(f"  Email: {email}")
    confirm = input("\nProceed? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Cancelled.")
        return
    
    # Initialize Firebase
    print("\n🔥 Initializing Firebase...")
    db = initialize_firebase()
    
    # Create user account
    print("\n👤 Creating admin user...")
    user = create_user(email, password, name, role='admin')
    
    if user:
        # Add to Firestore
        print("\n💾 Adding to Firestore...")
        add_admin(db, user['uid'], name, email)
        
        print("\n" + "=" * 50)
        print("✅ ADMIN CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"\n📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"🆔 UID: {user['uid']}")
        print("\n⚠️  Save these credentials securely!")
    else:
        print("\n❌ Failed to create admin account.")

if __name__ == '__main__':
    try:
        create_first_admin()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. Firebase credentials are in firebase/firebase_config.json")
        print("  2. .env file is configured")
        print("  3. Firebase Authentication is enabled in console")
