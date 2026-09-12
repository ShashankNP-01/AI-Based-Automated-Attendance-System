# Anti-Spoof AI Attendance System

An automated attendance system using face detection and recognition with Firebase backend.

## 📁 Project Structure

```
main_project/
├── firebase/           # Firebase configuration and service files
│   ├── firebase_config.json (download from Firebase Console)
│   ├── firebase_service.py (Firebase helper functions)
│   └── .env (environment variables)
├── models/            # Cached model weights from HuggingFace
├── local_cache/       # Local cache for embeddings (optional)
├── temp_uploads/      # Temporary storage before Firebase upload
├── attendance/        # Generated attendance CSV reports
├── notebooks/         # Jupyter notebooks
│   ├── enrollment.ipynb (enroll students)
│   └── attendance.ipynb (mark attendance from group photo)
├── scripts/           # Python scripts for automation
│   ├── enroll_student.py
│   ├── run_attendance.py
│   └── utils.py
├── web/               # Web interface (Flask/Streamlit)
│   ├── app.py
│   ├── templates/
│   └── static/
├── docs/              # Documentation
└── requirements.txt   # Python dependencies
```

## 🚀 Getting Started

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project: "attendance-system"
3. Enable **Authentication** (Email/Password method)
4. Enable **Firestore Database** (production mode)
5. Enable **Firebase Storage**
6. Set **Firestore Security Rules** (see `project_pipeline.txt` lines 726-763)
7. Set **Storage Security Rules** (see `project_pipeline.txt` lines 765-786)
8. Download Admin SDK credentials:
   - Project Settings → Service Accounts → Generate New Private Key
   - Save as `firebase/firebase_config.json`

### Step 3: Environment Variables
Create `firebase/.env` file:
```
FIREBASE_CREDENTIALS_PATH=./firebase/firebase_config.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### Step 4: Initialize Admin Account
```python
# Run this in Python/Jupyter to create your first admin account
python scripts/create_admin.py
```

### Step 5: Enroll Students
Open `notebooks/enrollment.ipynb` and follow the steps to:
- Add student photos
- Generate face embeddings
- Save to Firebase (Firestore + Storage + Auth)

### Step 6: Mark Attendance
Open `notebooks/attendance.ipynb` and:
- Upload a group photo
- System automatically detects faces
- Matches against enrolled students
- Saves attendance log to Firebase
- Generates CSV report

### Step 7: Launch Web Interface (Optional)
```bash
streamlit run web/app.py
# OR
python web/app.py  # if using Flask
```

## 🤖 Models Used

| Purpose | Model | Input | Output |
|---------|-------|-------|--------|
| Face Detection | YOLOv8 | Group Photo (any size) | Bounding boxes |
| Face Alignment | RetinaFace ResNet50 | Cropped face | 112×112 aligned face |
| Face Recognition | AdaFace IR101 | 112×112 face | 512-dim embedding |

## 🔒 Authentication

- **Admin**: Full access (enroll students, mark attendance, view all logs)
- **Student**: View own attendance only

## 📊 Firebase Collections

1. **admins**: Admin user profiles
2. **students**: Student profiles (name, roll_no, email, photo_url)
3. **embeddings**: Face embeddings for recognition
4. **attendance_log**: Attendance records with timestamps

## 📖 Documentation

See `docs/` folder for:
- `model.txt`: Model recommendations
- `about_model.txt`: Technical Q&A
- `project_pipeline.txt`: Complete development guide

## 🎯 Next Steps

1. ✅ Folder structure created
2. ⏳ Set up Firebase project
3. ⏳ Create Firebase service helper
4. ⏳ Build enrollment system
5. ⏳ Build attendance system
6. ⏳ Build web interface
7. ⏳ Deploy to production

---
**Note**: This system does NOT require training/fine-tuning. Just enroll students by running their photos through the models and saving embeddings!
