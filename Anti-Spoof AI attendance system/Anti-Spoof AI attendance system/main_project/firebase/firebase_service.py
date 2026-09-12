# Firebase Service Helper Functions
# This file provides wrapper functions for all Firebase operations
# NOTE: No Firebase Storage needed - face embeddings uniquely identify students

import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv, find_dotenv
import numpy as np

# Load .env from project root (searches upward from this file's location)
_dotenv_path = find_dotenv()
load_dotenv(_dotenv_path)

# Project root = folder containing .env (i.e. main_project/)
# Fallback: two levels up from this file (firebase/firebase_service.py → main_project/)
_PROJECT_ROOT = os.path.dirname(_dotenv_path) if _dotenv_path else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def initialize_firebase():
    """
    Initialize Firebase Admin SDK with credentials.
    Only requires Firestore + Authentication - no Storage needed.
    """
    cred_path_raw = os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase/firebase_config.json')

    # Always resolve relative paths against project root, not cwd
    # This fixes issues when scripts are run from subdirectories (e.g. scripts/)
    if not os.path.isabs(cred_path_raw):
        cred_path = os.path.normpath(os.path.join(_PROJECT_ROOT, cred_path_raw))
    else:
        cred_path = cred_path_raw

    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"\n❌ Firebase credentials not found at:\n   {cred_path}\n\n"
            f"   Please download firebase_config.json from:\n"
            f"   Firebase Console → Project Settings → Service Accounts → Generate New Private Key\n"
            f"   Then save it to: main_project/firebase/firebase_config.json"
        )

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()

# --------------------- AUTHENTICATION ---------------------

def create_user(email, password, display_name, role='student'):
    """
    Create a new Firebase Authentication user with custom role claim.
    
    Args:
        email (str): User's email
        password (str): User's password (min 6 chars)
        display_name (str): User's full name
        role (str): 'admin' or 'student'
    
    Returns:
        dict: User info {'uid': str, 'email': str, 'role': str}
    """
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        
        # Set custom claims for role-based access
        auth.set_custom_user_claims(user.uid, {'role': role})
        
        print(f"✅ User created: {email} (UID: {user.uid}, Role: {role})")
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': display_name,
            'role': role
        }
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None

def delete_user(uid):
    """Delete a Firebase Authentication user."""
    try:
        auth.delete_user(uid)
        print(f"✅ User deleted: {uid}")
        return True
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return False

# --------------------- FIRESTORE (DATABASE) ---------------------

def add_admin(db, uid, name, email):
    """
    Add admin profile to Firestore.
    
    Args:
        db: Firestore client
        uid (str): Firebase Auth UID
        name (str): Admin's full name
        email (str): Admin's email
    
    Returns:
        str: Document ID
    """
    doc_ref = db.collection('admins').document(uid)
    doc_ref.set({
        'name': name,
        'email': email,
        'created_at': firestore.SERVER_TIMESTAMP
    })
    print(f"✅ Admin added to Firestore: {name}")
    return uid

def add_student(db, uid, roll_no, name, email, branch='', sem=None):
    """
    Add student profile to Firestore.
    No photo needed - face embedding handles recognition.
    
    Args:
        db: Firestore client
        uid (str): Firebase Auth UID
        roll_no (str): Student roll number (unique)
        name (str): Student's full name
        email (str): Student's email
        branch (str): Department branch (e.g. 'CS', 'EC', 'EEE')
        sem (int): Semester number (1–7)
    
    Returns:
        str: Document ID
    """
    doc_ref = db.collection('students').document(uid)
    doc_ref.set({
        'roll_no': roll_no,
        'name': name,
        'email': email,
        'branch': branch,
        'sem': sem,
        'enrolled_at': firestore.SERVER_TIMESTAMP
    })
    print(f"✅ Student added to Firestore: {name} (Roll No: {roll_no}, Branch: {branch}, Sem: {sem})")
    return uid

def save_embedding(db, student_uid, embedding):
    """
    Save face embedding for a student.
    
    Args:
        db: Firestore client
        student_uid (str): Student's Firebase Auth UID
        embedding (np.ndarray): 512-dim face embedding vector
    
    Returns:
        str: Document ID
    """
    # Convert numpy array to list for Firestore storage
    embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
    
    doc_ref = db.collection('embeddings').document(student_uid)
    doc_ref.set({
        'student_uid': student_uid,
        'embedding': embedding_list,
        'updated_at': firestore.SERVER_TIMESTAMP
    })
    print(f"✅ Embedding saved for student UID: {student_uid}")
    return student_uid

def get_all_embeddings(db):
    """
    Retrieve all student embeddings from Firestore.
    
    Args:
        db: Firestore client
    
    Returns:
        dict: {student_uid: embedding_vector}
    """
    embeddings = {}
    docs = db.collection('embeddings').stream()
    
    for doc in docs:
        data = doc.to_dict()
        embeddings[data['student_uid']] = np.array(data['embedding'])
    
    print(f"✅ Retrieved {len(embeddings)} embeddings from Firestore")
    return embeddings

def log_attendance(db, date, detected_students, subject='', branch='', sem=None):
    """
    Save attendance record to Firestore.

    Args:
        db: Firestore client
        date (str): Date in 'YYYY-MM-DD' format
        detected_students (list): List of dicts [{'student_uid': str, 'confidence': float}]
        subject (str): Subject name for this attendance session
        branch (str): Branch filter used when marking attendance
        sem (int|None): Semester filter used when marking attendance

    Returns:
        str: Document ID
    """
    doc_ref = db.collection('attendance_log').document()
    doc_ref.set({
        'date': date,
        'subject': subject,
        'branch': branch,
        'sem': sem,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'detected_students': detected_students,
        'total_present': len(detected_students)
    })
    print(f"✅ Attendance logged for {date} ({subject}): {len(detected_students)} students present")
    return doc_ref.id

def get_student_attendance(db, student_uid):
    """
    Get all attendance records for a specific student.
    
    Args:
        db: Firestore client
        student_uid (str): Student's Firebase Auth UID
    
    Returns:
        list: List of attendance records
    """
    records = []
    # subject_stats: { subject: { present: int, total: int } }
    subject_stats = {}

    # First get the student's branch and sem for total-class counting
    student_doc = db.collection('students').document(student_uid).get()
    student_data = student_doc.to_dict() if student_doc.exists else {}
    s_branch = student_data.get('branch', '')
    s_sem = student_data.get('sem', None)

    docs = db.collection('attendance_log').stream()

    for doc in docs:
        data = doc.to_dict()
        subject = data.get('subject', '')
        if not subject:
            continue

        log_branch = data.get('branch', '')
        log_sem = data.get('sem', None)

        # Only count logs that have an explicit branch+sem stored AND match
        # this student. Old logs without branch/sem fields are ignored so they
        # don't inflate "total classes" for subjects the student never had.
        if log_branch != s_branch or log_sem != s_sem:
            continue

        # Track total classes per subject
        if subject not in subject_stats:
            subject_stats[subject] = {'present': 0, 'total': 0}
        subject_stats[subject]['total'] += 1

        detected = data.get('detected_students', [])
        was_present = False
        for entry in detected:
            if entry['student_uid'] == student_uid:
                records.append({
                    'date': data['date'],
                    'subject': subject,
                    'status': 'present',
                    'timestamp': data.get('timestamp'),
                    'confidence': entry['confidence']
                })
                subject_stats[subject]['present'] += 1
                was_present = True
                break

        if not was_present:
            records.append({
                'date': data['date'],
                'subject': subject,
                'status': 'absent',
                'timestamp': data.get('timestamp'),
                'confidence': None
            })

    # Compute percentages
    for subj, stats in subject_stats.items():
        total = stats['total']
        present = stats['present']
        stats['pct'] = round((present / total) * 100, 1) if total > 0 else 0.0

    print(f"✅ Retrieved {len(records)} attendance records for student {student_uid}")
    return records, subject_stats

# --------------------- UTILITY FUNCTIONS ---------------------

def get_student_by_uid(db, student_uid):
    """Get student profile by UID."""
    doc = db.collection('students').document(student_uid).get()
    if doc.exists:
        return doc.to_dict()
    return None

def get_student_by_roll_no(db, roll_no):
    """Get student profile by roll number."""
    docs = db.collection('students').where('roll_no', '==', roll_no).limit(1).stream()
    for doc in docs:
        data = doc.to_dict()
        data['uid'] = doc.id
        return data
    return None

def check_roll_no_exists(db, roll_no):
    """Check if roll number already exists."""
    return get_student_by_roll_no(db, roll_no) is not None

# --------------------- EXAMPLE USAGE ---------------------

if __name__ == '__main__':
    # Initialize Firebase
    db = initialize_firebase()
    
    print("Firebase Service Helper loaded successfully!")
    print("\nExample usage:")
    print("  db = initialize_firebase()")
    print("  user = create_user('student@example.com', 'password123', 'John Doe', 'student')")
    print("  add_student(db, user['uid'], 'CS001', 'John Doe', 'student@example.com')")
    print("  save_embedding(db, user['uid'], embedding_vector)   # embedding = unique ID!")
    print("  embeddings = get_all_embeddings(db)")
