# 🎓 Anti-Spoof AI Attendance System

An intelligent, AI-powered automated attendance system that uses advanced face detection, anti-spoofing, and face recognition technology to mark attendance securely. Built with cutting-edge deep learning models and Firebase backend.

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Project Architecture](#project-architecture)
- [Technology Stack](#technology-stack)
- [ML Models Used](#ml-models-used)
- [Project Pipeline](#project-pipeline)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Firebase Integration](#firebase-integration)
- [API Endpoints](#api-endpoints)
- [Directory Structure](#directory-structure)
- [Contributing](#contributing)
- [License](#license)

---

## 📖 About the Project

The **Anti-Spoof AI Attendance System** is an automated solution for marking student attendance using facial recognition technology. It leverages state-of-the-art computer vision models to:

- **Detect faces** in images/videos with high accuracy
- **Prevent spoofing** attacks (photos, masks, etc.)
- **Recognize students** through face embeddings and similarity matching
- **Log attendance** with timestamps to Firebase
- **Generate reports** for administrative purposes

This system eliminates the need for manual attendance marking, reduces cheating, and provides a secure, scalable solution for educational institutions.

---

## ✨ Features

### Core Features
- ✅ **Real-time Face Detection** - Detect multiple faces in group photos
- ✅ **Anti-Spoofing Detection** - Distinguish real faces from photos/masks/videos
- ✅ **Face Alignment** - Normalize detected faces for accurate recognition
- ✅ **Face Recognition** - Match detected faces against enrolled students
- ✅ **Automated Attendance Logging** - Record attendance with timestamps
- ✅ **Student Enrollment** - Register new students with face embeddings
- ✅ **Attendance Reports** - Generate CSV attendance records

### Web Interface Features
- 🌐 **Web Dashboard** - User-friendly Flask web application
- 👨‍💼 **Admin Panel** - Manage students, view attendance logs
- 📊 **Attendance Analytics** - View attendance trends and statistics
- 📱 **Group Photo Upload** - Upload multiple attendees in one photo
- 🔐 **Secure Authentication** - Firebase Auth integration

### Integration Features
- 🔥 **Firebase Integration** - Cloud database and storage
- 📧 **Email Notifications** - Notify admins of attendance
- 🖼️ **Cloud Storage** - Store student photos and embeddings
- 📝 **Firestore Database** - Persistent attendance records

---

## 🏗️ Project Architecture

### Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Anti-Spoof AI Attendance System              │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ Frontend │  │ Backend  │  │ Database │
         │(HTML/CSS)│  │ (Flask)  │  │(Firestore)
         └──────────┘  └──────────┘  └──────────┘
                │            │             │
                └────────────┼─────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
            ┌──────────────┐  ┌──────────────┐
            │ ML Pipeline  │  │ Firebase     │
            │              │  │ Services     │
            └──────────────┘  └──────────────┘
```

### ML Processing Pipeline

```
User Input (Group Photo)
    │
    ▼
┌─────────────────────────────┐
│  Image Preprocessing        │
│ - Resize & Normalize       │
│ - Convert to RGB           │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Face Detection (YOLOv8)    │
│ - Detect all faces         │
│ - Get bounding boxes       │
│ - Extract face regions     │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Face Alignment            │
│  (RetinaFace + Landmarks)  │
│ - Align to 112×112         │
│ - Normalize orientation    │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Anti-Spoofing Check       │
│ - Analyze liveness         │
│ - Filter fake faces        │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Face Recognition          │
│  (AdaFace IR101)           │
│ - Generate 512-dim         │
│   embeddings               │
│ - Extract features         │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Similarity Matching       │
│ - Compare with known faces │
│ - Compute cosine distance  │
│ - Identify students        │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Attendance Logging        │
│ - Record timestamp         │
│ - Save to Firebase         │
│ - Update attendance log    │
└─────────────────────────────┘
    │
    ▼
Attendance Marked ✓
```

### System Components Hierarchy

```
Anti-Spoof AI System
│
├── Frontend (web/frontend/)
│   ├── index.html           # Main UI
│   ├── app.js              # Client-side logic
│   └── style.css           # Styling
│
├── Backend (web/backend/)
│   ├── app.py              # Flask application
│   ├── __pycache__/        # Compiled Python
│   └── routes/
│       ├── /               # Main page
│       ├── /api/enroll     # Student enrollment
│       ├── /api/recognize  # Face recognition
│       ├── /api/attendance # Attendance marking
│       └── /api/analytics  # Attendance reports
│
├── ML Models (models/)
│   ├── cvlface_adaface_ir101_webface12m/  # Face recognition
│   │   ├── model.safetensors
│   │   ├── pretrained_model/model.pt
│   │   └── models/
│   │
│   └── private_retinaface_resnet50/       # Face alignment
│       ├── model.safetensors
│       ├── pretrained_model/model.pt
│       └── aligners/
│
├── Firebase (firebase/)
│   ├── firebase_config.json  # Credentials (secrets)
│   ├── firebase_service.py   # Firebase helper functions
│   └── .env                  # Environment variables
│
├── Scripts (scripts/)
│   ├── create_admin.py       # Create admin account
│   ├── email_service.py      # Email notifications
│   ├── utils.py              # Utility functions
│   └── __pycache__/
│
└── Temporary Files
    ├── temp_uploads/        # Temporary uploads
    ├── attendance/          # CSV reports
    └── local_cache/         # Local embeddings cache
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.1.3
- **Language**: Python 3.10+
- **APIs**: Flask-CORS for cross-origin requests

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling
- **JavaScript (Vanilla)** - Client-side logic

### Machine Learning & Computer Vision
- **PyTorch 2.10.0** - Deep learning framework
- **OpenCV 4.13** - Image processing
- **Transformers 5.2.0** - Model utilities
- **Ultralytics 8.4.14** - YOLOv8 implementation
- **Pillow 12.1.1** - Image handling

### Cloud & Database
- **Firebase Admin SDK 7.1.0** - Backend services
- **Google Cloud Firestore** - NoSQL database
- **Firebase Storage** - File storage
- **Firebase Authentication** - User management

### Utilities
- **Pandas 2.3.3** - Data processing
- **NumPy 2.2.6** - Numerical computations
- **SciPy 1.15.3** - Scientific computing
- **python-dotenv 1.2.1** - Environment variables
- **Matplotlib & Seaborn** - Data visualization

---

## 🤖 ML Models Used

### 1. **YOLOv8 - Face Detection**

| Property | Value |
|----------|-------|
| **Model Name** | YOLOv8 (arnabdhar/YOLOv8-Face-Detection) |
| **Purpose** | Detect and locate faces in images |
| **Input** | Color image (any resolution) |
| **Output** | Bounding boxes with confidence scores |
| **Architecture** | Convolutional Neural Network (CNN) |
| **Framework** | PyTorch |
| **Accuracy** | Real-time, high-precision detection |
| **Speed** | ⚡ Very fast (~30 FPS on GPU) |

**Use Case**: First stage - detects all faces in a group photo

---

### 2. **RetinaFace ResNet50 - Face Alignment**

| Property | Value |
|----------|-------|
| **Model Name** | RetinaFace (minchul/private_retinaface_resnet50) |
| **Purpose** | Align detected faces and extract facial landmarks |
| **Input** | Cropped face image |
| **Output** | 5-point facial landmarks + aligned 112×112 face |
| **Architecture** | ResNet50 with multi-task learning |
| **Framework** | PyTorch |
| **Accuracy** | High-precision landmark detection |
| **Speed** | ⚡ Fast per-face processing |

**Use Case**: Second stage - normalizes faces for consistent recognition

---

### 3. **AdaFace IR101 - Face Recognition**

| Property | Value |
|----------|-------|
| **Model Name** | AdaFace IR101 (minchul/cvlface_adaface_ir101_webface12m) |
| **Purpose** | Generate face embeddings for recognition |
| **Input** | Aligned 112×112 face image |
| **Output** | 512-dimensional face embedding |
| **Architecture** | ResNet-101 backbone with AdaFace loss |
| **Framework** | PyTorch |
| **Dataset Trained** | WebFace12M (12 million faces) |
| **Accuracy** | Top-tier face recognition accuracy |
| **Speed** | ⚡ Fast embedding generation |

**Use Case**: Third stage - generates unique embedding for each face for comparison

---

### Model Pipeline Integration

```
Input Image
    │
    ├─► YOLOv8 (Detection)
    │    └─► Detects & crops faces
    │
    ├─► RetinaFace (Alignment)
    │    └─► Normalizes to 112×112
    │
    ├─► AdaFace (Recognition)
    │    └─► Generates 512-D embeddings
    │
    └─► Similarity Matching
         └─► Compares with stored embeddings
              └─► Identifies students
```

---

## 🔄 Project Pipeline

### Phase 1: Setup
1. Clone repository
2. Install dependencies (`pip install -r requirements.txt`)
3. Configure Firebase credentials
4. Set up environment variables

### Phase 2: Development
1. **Backend Setup**
   - Create Flask application with routes
   - Integrate ML models
   - Connect Firebase services

2. **Frontend Development**
   - Build HTML/CSS interface
   - Implement JavaScript functionality
   - Create forms for enrollment/attendance

3. **Database Setup**
   - Create Firestore collections
   - Set security rules
   - Configure storage buckets

### Phase 3: Integration
1. Connect ML pipeline to Flask
2. Integrate Firebase CRUD operations
3. Implement authentication
4. Build API endpoints

### Phase 4: Testing & Deployment
1. Unit testing
2. Integration testing
3. Performance optimization
4. Cloud deployment

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Git
- Firebase project (free tier okay)
- NVIDIA GPU (optional, but recommended for speed)

### Step 1: Clone Repository
```bash
git clone https://github.com/npshashank05/AI-Based-Automated-Attendance-System.git
cd AI-Based-Automated-Attendance-System
```

### Step 2: Create Virtual Environment
```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project: "attendance-system"
3. Enable Authentication (Email/Password)
4. Enable Firestore Database
5. Enable Firebase Storage
6. Download service account key as `firebase/firebase_config.json`

### Step 5: Configure Environment
Create `main_project/firebase/.env`:
```env
FIREBASE_CREDENTIALS_PATH=./firebase/firebase_config.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### Step 6: Create Admin Account
```bash
cd main_project
python scripts/create_admin.py
```

### Step 7: Start Backend Server
```bash
cd main_project/web/backend
python app.py
```

Server runs on: `http://localhost:5000`

---

## 🚀 Usage

### Enrolling Students
1. Access web dashboard at `http://localhost:5000`
2. Login with admin credentials
3. Go to "Enroll Student"
4. Upload student photo (or multiple photos)
5. Enter name and roll number
6. System generates embedding and saves to Firebase

### Marking Attendance
1. Go to "Mark Attendance" on dashboard
2. Upload group photo containing students
3. System automatically:
   - Detects all faces
   - Generates embeddings
   - Matches against enrolled students
   - Marks attendance
4. View results and download CSV report

### Viewing Reports
1. Go to "Attendance Reports"
2. Filter by date range or student
3. Download CSV for further analysis

---

## 🔥 Firebase Integration

### Collections
- **admins** - Admin user profiles
- **students** - Student information (name, roll_no, email, photo_url)
- **embeddings** - Face embeddings for recognition
- **attendance_log** - Attendance records with timestamps

### Storage Buckets
- **profile_photos/** - Student profile pictures
- **embeddings/** - Face embedding files

### Authentication
- Email/Password authentication
- Role-based access control (Admin/Student)

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - Login user
- `POST /api/auth/register` - Register new user
- `POST /api/auth/logout` - Logout user

### Student Management
- `GET /api/students` - List all students
- `POST /api/students/enroll` - Enroll new student
- `GET /api/students/<id>` - Get student details
- `PUT /api/students/<id>` - Update student
- `DELETE /api/students/<id>` - Delete student

### Attendance
- `POST /api/attendance/mark` - Mark attendance from photo
- `GET /api/attendance/<student_id>` - Get student attendance
- `GET /api/attendance/report` - Generate attendance report
- `POST /api/attendance/batch` - Batch attendance marking

### Face Recognition
- `POST /api/recognize` - Recognize faces in image
- `POST /api/verify` - Verify face authenticity

---

## 📁 Directory Structure

```
AI-Based-Automated-Attendance-System/
├── README.md                           # Project documentation
├── requirements.txt                    # Python dependencies
│
└── main_project/
    ├── firebase/
    │   ├── firebase_config.json       # Firebase credentials (secrets)
    │   ├── firebase_service.py        # Firebase helper functions
    │   └── README.txt
    │
    ├── models/
    │   ├── cvlface_adaface_ir101_webface12m/   # Face recognition model
    │   │   ├── model.safetensors
    │   │   ├── pretrained_model/
    │   │   ├── models/
    │   │   ├── wrapper.py
    │   │   └── config.json
    │   │
    │   └── private_retinaface_resnet50/        # Face alignment model
    │       ├── model.safetensors
    │       ├── pretrained_model/
    │       ├── aligners/
    │       ├── wrapper.py
    │       └── config.json
    │
    ├── scripts/
    │   ├── create_admin.py            # Admin account creation
    │   ├── email_service.py           # Email notifications
    │   ├── utils.py                   # Utility functions
    │   └── __pycache__/
    │
    ├── web/
    │   ├── backend/
    │   │   ├── app.py                 # Flask main application
    │   │   └── __pycache__/
    │   │
    │   ├── frontend/
    │   │   ├── index.html             # Main page
    │   │   ├── app.js                 # JavaScript logic
    │   │   └── style.css              # Styling
    │   │
    │   ├── templates/                 # HTML templates (if using Jinja2)
    │   └── static/                    # Static assets
    │
    ├── temp_uploads/                  # Temporary file storage
    ├── attendance/                    # Generated reports
    └── requirements.txt               # Dependencies
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👨‍💻 Author

**Shashank** - AI/ML Developer
- GitHub: [@npshashank05](https://github.com/npshashank05)
- Project: [AI-Based-Automated-Attendance-System](https://github.com/npshashank05/AI-Based-Automated-Attendance-System)

---

## 🎯 Future Enhancements

- [ ] Mobile app (iOS/Android)
- [ ] Real-time webcam attendance marking
- [ ] Advanced anti-spoofing with liveness detection
- [ ] Multi-angle face matching
- [ ] Attendance analytics dashboard
- [ ] Integration with ERP systems
- [ ] Batch processing optimization
- [ ] Model fine-tuning for specific datasets

---

## ❓ FAQ

**Q: Does the system require GPU?**
A: GPU is recommended for faster processing but not required. CPU mode is supported.

**Q: How accurate is the face recognition?**
A: AdaFace achieves industry-leading accuracy (>99.8% on LFW dataset).

**Q: Can it detect spoofing attacks?**
A: Yes, through multi-model analysis and facial feature validation.

**Q: Is data secure?**
A: Yes, Firebase provides enterprise-grade security with encryption.

---

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Last Updated**: February 2026
**Version**: 1.0.0
