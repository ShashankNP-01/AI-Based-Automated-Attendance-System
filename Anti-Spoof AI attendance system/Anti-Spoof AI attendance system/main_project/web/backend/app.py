"""
Flask Backend API for Anti-Spoof AI Attendance System
Handles ML processing + Firebase operations.
Serves the frontend (plain HTML/CSS/JS) from web/frontend/.
"""

import sys
import os
# Force UTF-8 stdout so emoji in print() don't crash on Windows cp1252 terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))  # main_project/

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import cv2
import torch
from PIL import Image
from datetime import datetime
import tempfile
import traceback

# Firebase Admin
from firebase_admin import auth as firebase_auth
from firebase.firebase_service import (
    initialize_firebase,
    create_user,
    add_student,
    save_embedding,
    get_all_embeddings,
    get_student_by_uid,
    log_attendance,
    check_roll_no_exists,
    get_student_attendance
)
from scripts.utils import batch_cosine_similarity, normalize_embedding
from scripts.email_service import notify_absent_students_async

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# ─── Global state (models loaded once at startup) ─────────────────────────────
db = None
yolo_model = None
retinaface_model = None
adaface_model = None
device = None

def _download_hf_model(repo_id, save_path, HF_TOKEN=None):
    """
    Download a HuggingFace model repo to a local folder.
    Uses files.txt manifest if present; always grabs core files.
    """
    import shutil
    from huggingface_hub import hf_hub_download

    os.makedirs(save_path, exist_ok=True)
    files_path = os.path.join(save_path, 'files.txt')

    # Download manifest
    if not os.path.exists(files_path):
        try:
            hf_hub_download(repo_id, 'files.txt', token=HF_TOKEN,
                            local_dir=save_path, local_dir_use_symlinks=False)
        except Exception:
            pass  # some repos don't have files.txt

    # Read extra files listed in manifest
    extra_files = []
    if os.path.exists(files_path):
        with open(files_path, 'r') as f:
            extra_files = [l.strip() for l in f.read().split('\n') if l.strip()]

    core_files = ['config.json', 'wrapper.py', 'model.safetensors', 'pytorch_model.bin']
    for filename in extra_files + core_files:
        dest = os.path.join(save_path, filename)
        if not os.path.exists(dest):
            try:
                hf_hub_download(repo_id, filename, token=HF_TOKEN,
                                local_dir=save_path, local_dir_use_symlinks=False)
            except Exception:
                pass  # file may not exist in this repo


def _load_model_from_local(path):
    """
    Load a HuggingFace model whose code lives inside `path`.
    Temporarily adds path to sys.path so bundled packages (like `aligners`)
    are importable without a separate pip install.
    """
    from transformers import AutoModel
    cwd = os.getcwd()
    try:
        os.chdir(path)
        sys.path.insert(0, path)
        model = AutoModel.from_pretrained(path, trust_remote_code=True)
        return model
    finally:
        os.chdir(cwd)
        if path in sys.path:
            sys.path.remove(path)


def load_models():
    """Load all ML models into memory once at startup."""
    global yolo_model, retinaface_model, adaface_model, device

    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO
    from transformers import PreTrainedModel

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️  Using device: {device}")

    # Patch for transformers >= 4.37.0
    if not hasattr(PreTrainedModel, 'all_tied_weights_keys'):
        PreTrainedModel.all_tied_weights_keys = property(lambda self: {})

    # Resolve models cache directory (main_project/models/)
    MAIN_PROJECT = os.path.join(os.path.dirname(__file__), '..', '..')
    MODELS_DIR = os.path.abspath(os.path.join(MAIN_PROJECT, 'models'))
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("[*] Loading YOLOv8...")
    model_path = hf_hub_download(repo_id='arnabdhar/YOLOv8-Face-Detection', filename='model.pt')
    yolo_model = YOLO(model_path)

    print("[*] Loading RetinaFace (downloading to local cache)...")
    rf_path = os.path.join(MODELS_DIR, 'private_retinaface_resnet50')
    _download_hf_model('minchul/private_retinaface_resnet50', rf_path)
    retinaface_model = _load_model_from_local(rf_path).to(device).eval()

    print("[*] Loading AdaFace (downloading to local cache)...")
    ada_path = os.path.join(MODELS_DIR, 'cvlface_adaface_ir101_webface12m')
    _download_hf_model('minchul/cvlface_adaface_ir101_webface12m', ada_path)
    adaface_model = _load_model_from_local(ada_path).to(device).eval()

    print("[OK] All models loaded!")

# ─── Auth Middleware ───────────────────────────────────────────────────────────
def verify_token(req):
    """
    Verify Firebase ID token from Authorization header.
    Returns (uid, role) or raises an exception.
    """
    auth_header = req.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise PermissionError("Missing Authorization header")

    id_token = auth_header.split('Bearer ')[1]
    decoded = firebase_auth.verify_id_token(id_token)
    uid = decoded['uid']
    role = decoded.get('role', 'student')
    return uid, role

def require_admin(req):
    uid, role = verify_token(req)
    if role != 'admin':
        raise PermissionError("Admin access required")
    return uid

# ─── Helper: Process face from image ──────────────────────────────────────────
def process_face(image_np_bgr):
    """
    Given a BGR numpy image of a face region, returns normalized 512-dim embedding.
    """
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image_np_bgr, cv2.COLOR_BGR2RGB)
    
    # Convert to tensor and normalize to [-1, 1]
    image_tensor = torch.from_numpy(image_rgb).float().permute(2, 0, 1) / 255.0
    image_tensor = (image_tensor - 0.5) / 0.5
    image_tensor = image_tensor.unsqueeze(0).to(device)
    
    with torch.no_grad():
        # RetinaFace returns tuple: (aligned_x, orig_ldmks, aligned_ldmks, score, thetas, bbox)
        aligned_output = retinaface_model(image_tensor)
        aligned_face = aligned_output[0] if isinstance(aligned_output, tuple) else aligned_output
        
        # AdaFace expects 112x112 face tensor
        embedding = adaface_model(aligned_face)
    emb = embedding.cpu().numpy().flatten()
    return normalize_embedding(emb)

# ─── Routes ───────────────────────────────────────────────────────────────────

# ─── Serve Frontend ────────────────────────────────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'models_loaded': yolo_model is not None})


# ---------- AUTH ----------

@app.route('/api/auth/role', methods=['GET'])
def get_role():
    """Return the role of the authenticated user."""
    try:
        uid, role = verify_token(request)
        return jsonify({'uid': uid, 'role': role})
    except Exception as e:
        return jsonify({'error': str(e)}), 401


# ---------- STUDENTS ----------

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all enrolled students. Admin only. Optional ?branch= filter."""
    try:
        require_admin(request)
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403

    try:
        branch_filter = request.args.get('branch', '').strip()
        sem_filter = request.args.get('sem', '').strip()
        query = db.collection('students')
        if branch_filter:
            query = query.where('branch', '==', branch_filter)
        if sem_filter:
            query = query.where('sem', '==', int(sem_filter))
        docs = query.stream()
        students = []
        for doc in docs:
            data = doc.to_dict()
            data['uid'] = doc.id
            data.pop('password', None)
            if 'enrolled_at' in data and data['enrolled_at']:
                data['enrolled_at'] = str(data['enrolled_at'])
            students.append(data)
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/enroll', methods=['POST'])
def enroll_student():
    """
    Enroll a new student.
    Expects multipart/form-data:
      - name, roll_no, email, password (text fields)
      - photo (file)
    """
    try:
        require_admin(request)
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403

    try:
        name = request.form.get('name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        branch = request.form.get('branch', '').strip()
        sem_raw = request.form.get('sem', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        photo = request.files.get('photo')

        # Validate
        if not all([name, roll_no, branch, sem_raw, email, password, photo]):
            return jsonify({'error': 'All fields (name, roll_no, branch, sem, email, password, photo) are required'}), 400
        valid_branches = ['CS','CS-AIML','CS-DS','CS-D','CS-CY','EC','EEE','CE','ME']
        if branch not in valid_branches:
            return jsonify({'error': 'Invalid branch. Must be one of: ' + ', '.join(valid_branches)}), 400
        try:
            sem = int(sem_raw)
            if sem < 1 or sem > 7:
                raise ValueError()
        except ValueError:
            return jsonify({'error': 'Invalid semester. Must be 1–7.'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        if check_roll_no_exists(db, roll_no):
            return jsonify({'error': f'Roll number {roll_no} already exists'}), 409

        # Save photo to temp file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            photo.save(tmp.name)
            tmp_path = tmp.name

        # Load image
        image = Image.open(tmp_path).convert('RGB')
        image_np = np.array(image)

        # Detect face with YOLOv8
        results = yolo_model.predict(source=tmp_path, conf=0.4, verbose=False)
        os.unlink(tmp_path)

        if len(results[0].boxes) == 0:
            return jsonify({'error': 'No face detected in photo. Please use a clear front-facing photo.'}), 400

        # Crop face
        box = results[0].boxes[0].xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, box)
        face_crop = image_np[y1:y2, x1:x2]
        face_bgr = cv2.cvtColor(face_crop, cv2.COLOR_RGB2BGR)

        # Generate embedding
        embedding = process_face(face_bgr)

        # Create Firebase Auth user
        user = create_user(email, password, name, role='student')
        if not user:
            return jsonify({'error': 'Failed to create user account. Email may already be registered.'}), 409

        student_uid = user['uid']

        # Save to Firestore
        add_student(db, student_uid, roll_no, name, email, branch=branch, sem=sem)
        save_embedding(db, student_uid, embedding)

        return jsonify({
            'message': f'Student {name} enrolled successfully!',
            'uid': student_uid,
            'roll_no': roll_no,
            'name': name,
            'email': email,
            'branch': branch,
            'sem': sem
        }), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<uid>', methods=['DELETE'])
def delete_student(uid):
    """Delete a student. Admin only."""
    try:
        require_admin(request)
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403

    try:
        # Delete from Auth
        firebase_auth.delete_user(uid)
        # Delete from Firestore
        db.collection('students').document(uid).delete()
        db.collection('embeddings').document(uid).delete()
        return jsonify({'message': 'Student deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- ATTENDANCE ----------

@app.route('/api/attendance/mark', methods=['POST'])
def mark_attendance():
    """
    Mark attendance from a group photo.
    Expects multipart/form-data:
      - photo (file)
      - date (optional, defaults to today)
    """
    try:
        require_admin(request)
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403

    try:
        photo = request.files.get('photo')
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
        branch_filter = request.form.get('branch', '').strip()
        sem_filter = request.form.get('sem', '').strip()
        subject = request.form.get('subject', '').strip()

        if not subject:
            return jsonify({'error': 'Subject is required to mark attendance'}), 400

        if not photo:
            return jsonify({'error': 'No photo provided'}), 400

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            photo.save(tmp.name)
            tmp_path = tmp.name

        # Load image
        image = Image.open(tmp_path).convert('RGB')
        image_np = np.array(image)

        # Detect all faces
        results = yolo_model.predict(source=tmp_path, conf=0.4, verbose=False)
        os.unlink(tmp_path)

        boxes = results[0].boxes.xyxy.cpu().numpy()

        if len(boxes) == 0:
            return jsonify({'error': 'No faces detected in the photo'}), 400

        # Get all enrolled embeddings
        enrolled_embeddings = get_all_embeddings(db)
        if len(enrolled_embeddings) == 0:
            return jsonify({'error': 'No students enrolled yet'}), 400

        # Filter by branch if requested
        if branch_filter:
            branch_docs = db.collection('students').where('branch', '==', branch_filter).stream()
            branch_uids = {doc.id for doc in branch_docs}
            enrolled_embeddings = {uid: emb for uid, emb in enrolled_embeddings.items() if uid in branch_uids}

        # Filter by semester if requested
        if sem_filter:
            sem_docs = db.collection('students').where('sem', '==', int(sem_filter)).stream()
            sem_uids = {doc.id for doc in sem_docs}
            enrolled_embeddings = {uid: emb for uid, emb in enrolled_embeddings.items() if uid in sem_uids}

        student_uids = list(enrolled_embeddings.keys())
        enrolled_matrix = np.array([enrolled_embeddings[uid] for uid in student_uids])

        # Process each detected face
        detected_embeddings = []
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            face_crop = image_np[y1:y2, x1:x2]
            if face_crop.size == 0:
                continue
            face_bgr = cv2.cvtColor(face_crop, cv2.COLOR_RGB2BGR)
            try:
                emb = process_face(face_bgr)
                detected_embeddings.append(emb)
            except Exception:
                continue

        if not detected_embeddings:
            return jsonify({'error': 'Could not process any faces'}), 400

        # Match faces against enrolled students
        detected_matrix = np.array(detected_embeddings)
        similarity_matrix = batch_cosine_similarity(detected_matrix, enrolled_matrix)

        THRESHOLD = 0.4
        attendance_records = []
        matched_uids = set()

        for similarities in similarity_matrix:
            best_idx = np.argmax(similarities)
            best_score = float(similarities[best_idx])
            if best_score >= THRESHOLD:
                matched_uid = student_uids[best_idx]
                if matched_uid not in matched_uids:
                    matched_uids.add(matched_uid)
                    attendance_records.append({
                        'student_uid': matched_uid,
                        'confidence': round(best_score, 4)
                    })

        # Save to Firestore — always log the session even if nobody was detected
        # present, so absent students can see the class in their dashboard.
        log_id = log_attendance(db, date, attendance_records, subject=subject,
                                branch=branch_filter or '', sem=int(sem_filter) if sem_filter else None)

        # Build response with student names
        present_students = []
        for record in attendance_records:
            student = get_student_by_uid(db, record['student_uid'])
            if student:
                present_students.append({
                    'uid': record['student_uid'],
                    'name': student['name'],
                    'roll_no': student['roll_no'],
                    'confidence': record['confidence']
                })

        # All students for absent list
        all_students = []
        absent_list_for_email = []
        for uid in student_uids:
            student = get_student_by_uid(db, uid)
            if student:
                status = 'present' if uid in matched_uids else 'absent'
                all_students.append({
                    'uid': uid,
                    'name': student['name'],
                    'roll_no': student['roll_no'],
                    'status': status
                })
                if status == 'absent':
                    absent_list_for_email.append({
                        'name': student['name'],
                        'email': student.get('email', '')
                    })

        # Send absence notification emails (non-blocking background thread)
        class_name = os.getenv('EMAIL_CLASS_NAME', 'Lecture')
        notify_absent_students_async(absent_list_for_email, date, subject=class_name)

        return jsonify({
            'log_id': log_id,
            'date': date,
            'subject': subject,
            'faces_detected': len(boxes),
            'total_students': len(student_uids),
            'present_count': len(attendance_records),
            'absent_count': len(student_uids) - len(attendance_records),
            'present_students': present_students,
            'all_students': all_students
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/logs', methods=['GET'])
def get_attendance_logs():
    """Get all attendance logs. Admin only."""
    try:
        require_admin(request)
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403

    try:
        docs = db.collection('attendance_log').order_by('date', direction='DESCENDING').stream()
        logs = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            if 'timestamp' in data and data['timestamp']:
                data['timestamp'] = str(data['timestamp'])
            # Enrich with student names
            enriched = []
            for record in data.get('detected_students', []):
                student = get_student_by_uid(db, record['student_uid'])
                if student:
                    enriched.append({
                        'uid': record['student_uid'],
                        'name': student['name'],
                        'roll_no': student['roll_no'],
                        'confidence': record.get('confidence', 0)
                    })
            data['present_students'] = enriched
            data.setdefault('subject', '')
            logs.append(data)
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/my', methods=['GET'])
def get_my_attendance():
    """Get attendance records for the logged-in student."""
    try:
        uid, role = verify_token(request)
    except Exception as e:
        return jsonify({'error': str(e)}), 401

    try:
        records, subject_stats = get_student_attendance(db, uid)
        # Convert timestamps
        for r in records:
            if 'timestamp' in r and r['timestamp']:
                r['timestamp'] = str(r['timestamp'])
        student = get_student_by_uid(db, uid)
        return jsonify({
            'student': student,
            'records': records,
            'total_present': len(records),
            'subject_stats': subject_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Start ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("[*] Initializing Firebase...")
    db = initialize_firebase()
    print("[*] Loading ML Models (this may take a minute)...")
    load_models()
    print("\n[OK] Backend ready! Running on http://localhost:5000\n")
    app.run(debug=True, port=5000, use_reloader=False)
