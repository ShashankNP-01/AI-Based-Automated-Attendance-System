// ─── Firebase Config ──────────────────────────────────────────────────────────
const firebaseConfig = {
  apiKey: "AIzaSyBurhhJjsZh_hpMr5Q2em75AZvyP3xwLF8",
  authDomain: "ai-based-automated-system.firebaseapp.com",
  projectId: "ai-based-automated-system",
  storageBucket: "ai-based-automated-system.firebasestorage.app",
  messagingSenderId: "71146457840",
  appId: "1:71146457840:web:1dd29176c1357a62935035",
  measurementId: "G-9N5J3ER1GM"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// ─── API Base URL ─────────────────────────────────────────────────────────────
const API = '';  // Same origin — Flask serves both API and frontend

// ─── State ────────────────────────────────────────────────────────────────────
let currentToken = null;
let currentRole = null;
let allLogs = [];

// ─── DOM References ───────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

// ─── Helpers ──────────────────────────────────────────────────────────────────
async function apiFetch(url, options = {}) {
  const headers = options.headers || {};
  if (currentToken) headers['Authorization'] = `Bearer ${currentToken}`;
  if (!(options.body instanceof FormData) && options.body) {
    headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(API + url, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function showError(el, msg) {
  el.textContent = msg;
  el.style.display = 'block';
}
function hideError(el) {
  el.textContent = '';
  el.style.display = 'none';
}

// ─── Page Navigation ─────────────────────────────────────────────────────────
function showPage(pageId) {
  ['loading-screen', 'login-page', 'admin-page', 'student-page'].forEach(id => {
    $(id).style.display = 'none';
  });
  $(pageId).style.display = '';
}

// ─── Auth State Listener ─────────────────────────────────────────────────────
auth.onAuthStateChanged(async (user) => {
  if (user) {
    try {
      currentToken = await user.getIdToken();
      const data = await apiFetch('/api/auth/role');
      currentRole = data.role;

      if (currentRole === 'admin') {
        $('admin-email').textContent = user.email;
        showPage('admin-page');
        loadStudents();
      } else {
        $('student-email').textContent = user.email;
        showPage('student-page');
        loadStudentDashboard();
      }
    } catch (e) {
      console.error('Auth error:', e);
      currentRole = null;
      showPage('login-page');
    }
  } else {
    currentToken = null;
    currentRole = null;
    showPage('login-page');
  }
});

// ─── Login ────────────────────────────────────────────────────────────────────
$('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = $('login-btn');
  const errEl = $('login-error');
  hideError(errEl);
  btn.disabled = true;
  btn.textContent = 'Signing in…';

  try {
    const email = $('login-email').value;
    const password = $('login-password').value;
    await auth.signInWithEmailAndPassword(email, password);
    // onAuthStateChanged will handle redirect
  } catch (err) {
    const code = err.code || '';
    if (code.includes('wrong-password') || code.includes('user-not-found') || code.includes('INVALID_LOGIN') || code.includes('invalid-credential')) {
      showError(errEl, 'Invalid email or password.');
    } else if (code.includes('too-many-requests')) {
      showError(errEl, 'Too many attempts. Try again later.');
    } else {
      showError(errEl, err.message || 'Login failed');
    }
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sign In';
  }
});

// ─── Logout ───────────────────────────────────────────────────────────────────
$('admin-logout').addEventListener('click', () => auth.signOut());
$('student-logout').addEventListener('click', () => auth.signOut());

// ─── Tabs ─────────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Update active tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    // Show matching content
    const tabName = tab.dataset.tab;
    document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
    $('tab-' + tabName).style.display = '';

    // Load data for tab
    if (tabName === 'students') loadStudents();
    if (tabName === 'branches') loadBranches();
    if (tabName === 'logs') loadLogs();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
//  ADMIN: Students Tab
// ═══════════════════════════════════════════════════════════════════════════════

const BRANCHES = ['CS','CS-AIML','CS-DS','CS-D','CS-CY','EC','EEE','CE','ME'];
const SEMS = [1, 2, 3, 4, 5, 6, 7];

// ─── Subjects per Branch × Sem ──────────────────────────────────────────────────────
// Sems 1–2 are common across all branches
const COMMON_SEM1 = ['Mathematics I','Physics','Chemistry','Programming Fundamentals','English','Environmental Science','Engineering Graphics'];
const COMMON_SEM2 = ['Mathematics II','Data Structures','Digital Electronics','Electrical Circuits','OOP with Java','Technical Communication','Workshop Practice'];

const SUBJECTS = {
  'CS': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Discrete Mathematics','DAA','Operating Systems','Computer Networks','DBMS','Software Engineering','Microprocessors'],
    4: ['Theory of Computation','Compiler Design','Computer Graphics','Web Technologies','Java EE','Numerical Methods','Mini Project'],
    5: ['Machine Learning','Cloud Computing','Mobile Computing','Information Security','Software Testing','Elective I','Project I'],
    6: ['Deep Learning','Big Data Analytics','IoT','DevOps','Computer Vision','Elective II','Project II'],
    7: ['NLP','Blockchain','Research Methodology','Industry Track','Elective III','Elective IV','Major Project'],
  },
  'CS-AIML': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Discrete Mathematics','DAA','ML Fundamentals','Python for AI','Statistics for ML','DBMS','Operating Systems'],
    4: ['Deep Learning','Neural Networks','Computer Vision I','NLP Basics','Reinforcement Learning','Data Visualization','Mini Project'],
    5: ['Advanced ML','Generative AI','MLOps','Big Data for AI','AI Ethics','Elective I','Project I'],
    6: ['Computer Vision II','Robotics & AI','Explainable AI','AI in Healthcare','Edge AI','Elective II','Project II'],
    7: ['Research in AI','Advanced NLP','Industry Internship','Elective III','Elective IV','Thesis/Seminar','Major Project'],
  },
  'CS-DS': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Statistical Foundations','Python Programming','DBMS','Data Wrangling','Linear Algebra','Operating Systems','DAA'],
    4: ['Machine Learning','Data Visualization','Big Data Technologies','Cloud Computing','Time Series Analysis','Mini Project','Lab'],
    5: ['Deep Learning','NoSQL Databases','NLP','Business Intelligence','Data Ethics','Elective I','Project I'],
    6: ['Advanced Analytics','Recommender Systems','Graph Data','Real-time Analytics','Data Engineering','Elective II','Project II'],
    7: ['Research Methods','Capstone Project','Industry Internship','Elective III','Elective IV','Seminar','Major Project'],
  },
  'CS-D': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Discrete Mathematics','DAA','Operating Systems','Computer Networks','DBMS','Digital Design','Microprocessors'],
    4: ['Compiler Design','Theory of Computation','UI/UX Design','Web Development','Software Architecture','Mini Project','Lab'],
    5: ['Distributed Systems','Cloud Services','Agile Methods','Elective I','Capstone I','Seminar','Project I'],
    6: ['DevOps','System Design','Container Technology','Microservices','Elective II','Elective III','Project II'],
    7: ['Research','Industry Track','Elective IV','Elective V','Seminar','Thesis','Major Project'],
  },
  'CS-CY': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Cryptography','Network Security','OS Security','DBMS','Computer Networks','DAA','System Programming'],
    4: ['Web Security','Digital Forensics','Ethical Hacking','Security Protocols','Malware Analysis','Mini Project','Lab'],
    5: ['Cloud Security','IoT Security','Mobile Security','AI for Security','Security Audit','Elective I','Project I'],
    6: ['Blockchain Security','Zero-Trust Architecture','Incident Response','Security Operations','Elective II','Elective III','Project II'],
    7: ['Research in CyberSec','Advanced Forensics','Industry Internship','Elective IV','Elective V','Seminar','Major Project'],
  },
  'EC': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Signals & Systems','Electronic Circuits','Digital System Design','EM Theory','Analog Electronics','Network Theory','MATLAB'],
    4: ['Communication Systems','VLSI Design','Microprocessors','DSP','Control Systems','Mini Project','Lab'],
    5: ['Wireless Communication','Embedded Systems','Antenna Theory','RF Engineering','CMOS Design','Elective I','Project I'],
    6: ['IoT Systems','5G Networks','Image Processing','FPGA Design','Mixed-Signal Design','Elective II','Project II'],
    7: ['Advanced Communication','Photonics','Industry Internship','Elective III','Elective IV','Seminar','Major Project'],
  },
  'EEE': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Electrical Machines','Power Systems','Control Theory','Electronic Circuits','Electrical Measurements','EM Fields','Lab'],
    4: ['Power Electronics','Microprocessors','DSP','Electric Drives','Power System Analysis','Mini Project','Lab'],
    5: ['Renewable Energy','Smart Grid','HVDC Transmission','Industrial Drives','Energy Management','Elective I','Project I'],
    6: ['Power System Protection','Advanced Machines','PLC & SCADA','IoT in Energy','Power Quality','Elective II','Project II'],
    7: ['Smart Cities','Industry Internship','Elective III','Elective IV','Research Methods','Seminar','Major Project'],
  },
  'CE': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Structural Analysis','Fluid Mechanics','Soil Mechanics','Building Materials','Surveying','Engineering Geology','Lab'],
    4: ['Steel Structure Design','Geo-technical Engineering','Environmental Engineering','Transportation Engineering','Hydrology','Mini Project','Lab'],
    5: ['RCC Design','Water Resource Engineering','Construction Management','Urban Planning','Earthquake Engineering','Elective I','Project I'],
    6: ['Bridge Engineering','Advanced Foundation Design','GIS & Remote Sensing','Green Buildings','Elective II','Elective III','Project II'],
    7: ['Structural Dynamics','Research Methods','Industry Internship','Elective IV','Elective V','Seminar','Major Project'],
  },
  'ME': {
    1: COMMON_SEM1, 2: COMMON_SEM2,
    3: ['Engineering Thermodynamics','Fluid Mechanics','Manufacturing Processes','Theory of Machines','Material Science','Engineering Drawing','Lab'],
    4: ['Heat Transfer','Machine Design','Metrology','CAD/CAM','Dynamics of Machinery','Mini Project','Lab'],
    5: ['IC Engines','Robotics','Industrial Engineering','Refrigeration & AC','Finite Element Analysis','Elective I','Project I'],
    6: ['Automobile Engineering','Mechatronics','Operations Management','Advanced Manufacturing','Elective II','Elective III','Project II'],
    7: ['Product Design','Industry Internship','Elective IV','Elective V','Research Methods','Seminar','Major Project'],
  },
};

function populateSubjectDropdown() {
  const branch  = $('att-branch')  ? $('att-branch').value  : '';
  const sem     = $('att-sem')     ? $('att-sem').value     : '';
  const sel     = $('att-subject');
  if (!sel) return;

  sel.innerHTML = '';
  const subjects = (branch && sem && SUBJECTS[branch] && SUBJECTS[branch][parseInt(sem)])
    ? SUBJECTS[branch][parseInt(sem)]
    : [];

  if (subjects.length === 0) {
    sel.innerHTML = '<option value="">-- Select Branch &amp; Sem first --</option>';
  } else {
    sel.innerHTML = '<option value="">-- Select Subject --</option>' +
      subjects.map(s => `<option value="${s}">${s}</option>`).join('');
  }
}

async function loadStudents() {
  const tbody = $('students-tbody');
  tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:24px;">Loading…</td></tr>';

  try {
    const data = await apiFetch('/api/students');
    const filterBranch = $('branch-filter').value;
    const filterSem = $('sem-filter').value;
    let students = data.students || [];

    if (filterBranch) students = students.filter(s => s.branch === filterBranch);
    if (filterSem)   students = students.filter(s => String(s.sem) === filterSem);
    $('student-count').textContent = students.length;

    if (students.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:24px;">No students found.</td></tr>';
      return;
    }

    tbody.innerHTML = students.map(s => `
      <tr>
        <td>${esc(s.name)}</td>
        <td><span class="badge badge-info">${esc(s.roll_no)}</span></td>
        <td><span class="badge branch-badge" style="background:${branchColor(s.branch)};">${esc(s.branch || '—')}</span></td>
        <td><span class="badge sem-badge">${s.sem ? 'Sem ' + esc(String(s.sem)) : '—'}</span></td>
        <td style="color:var(--text-muted);">${esc(s.email)}</td>
        <td><button class="btn btn-danger btn-sm" onclick="deleteStudent('${esc(s.uid)}', '${esc(s.name)}')">Delete</button></td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="error-msg">${esc(err.message)}</td></tr>`;
  }
}

function branchColor(branch) {
  const map = {
    'CS':      'rgba(99,102,241,0.25)',
    'CS-AIML': 'rgba(168,85,247,0.25)',
    'CS-DS':   'rgba(236,72,153,0.25)',
    'CS-D':    'rgba(14,165,233,0.25)',
    'CS-CY':   'rgba(20,184,166,0.25)',
    'EC':      'rgba(234,179,8,0.25)',
    'EEE':     'rgba(249,115,22,0.25)',
    'CE':      'rgba(34,197,94,0.25)',
    'ME':      'rgba(239,68,68,0.25)',
  };
  return map[branch] || 'rgba(160,100,220,0.2)';
}

// Branch filter change
$('branch-filter').addEventListener('change', loadStudents);
$('sem-filter').addEventListener('change', loadStudents);

function esc(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function deleteStudent(uid, name) {
  if (!confirm(`Delete ${name}? This cannot be undone.`)) return;
  try {
    await apiFetch(`/api/students/${uid}`, { method: 'DELETE' });
    loadStudents();
  } catch (err) {
    alert(err.message || 'Delete failed.');
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  ADMIN: Branches Tab
// ═══════════════════════════════════════════════════════════════════════════════

async function loadBranches() {
  const grid = $('branches-grid');
  grid.innerHTML = '<p style="color:var(--text-muted);padding:24px;">Loading…</p>';

  try {
    const data = await apiFetch('/api/students');
    const students = data.students || [];

    // Count per branch × sem
    const counts = {};
    BRANCHES.forEach(b => {
      counts[b] = { total: 0 };
      SEMS.forEach(s => counts[b][s] = 0);
    });
    students.forEach(s => {
      if (s.branch && counts[s.branch] !== undefined) {
        counts[s.branch].total++;
        if (s.sem) counts[s.branch][s.sem] = (counts[s.branch][s.sem] || 0) + 1;
      }
    });

    grid.innerHTML = BRANCHES.map(b => {
      const semPills = SEMS.map(sem => {
        const n = counts[b][sem] || 0;
        return `<span class="sem-pill" title="${n} student${n!==1?'s':''}" onclick="viewBranchSem('${b}','${sem}')">
          S${sem}<em>${n}</em>
        </span>`;
      }).join('');
      return `
      <div class="branch-card" style="--bc:${branchColor(b)};">
        <div class="branch-abbr">${b}</div>
        <div class="branch-count">${counts[b].total}</div>
        <div class="branch-label">student${counts[b].total !== 1 ? 's' : ''}</div>
        <div class="branch-sems">${semPills}</div>
        <button class="btn btn-ghost btn-sm branch-view-btn" onclick="viewBranch('${b}')">All Students</button>
      </div>`;
    }).join('');
  } catch (err) {
    grid.innerHTML = `<p class="error-msg">${esc(err.message)}</p>`;
  }
}

function viewBranch(branch) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelector('[data-tab="students"]').classList.add('active');
  document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
  $('tab-students').style.display = '';
  $('branch-filter').value = branch;
  $('sem-filter').value = '';
  loadStudents();
}

function viewBranchSem(branch, sem) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelector('[data-tab="students"]').classList.add('active');
  document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
  $('tab-students').style.display = '';
  $('branch-filter').value = branch;
  $('sem-filter').value = sem;
  loadStudents();
}

// ─── Enroll Modal ─────────────────────────────────────────────────────────────
$('enroll-btn').addEventListener('click', () => {
  $('enroll-form').reset();
  hideError($('enroll-error'));
  $('enroll-modal').style.display = '';
});

$('enroll-close').addEventListener('click', () => $('enroll-modal').style.display = 'none');
$('enroll-cancel').addEventListener('click', () => $('enroll-modal').style.display = 'none');
$('enroll-modal').addEventListener('click', (e) => {
  if (e.target === $('enroll-modal')) $('enroll-modal').style.display = 'none';
});

$('enroll-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = $('enroll-submit');
  const errEl = $('enroll-error');
  hideError(errEl);
  btn.disabled = true;
  btn.textContent = 'Enrolling…';

  try {
    const fd = new FormData();
    fd.append('name', $('enroll-name').value.trim());
    fd.append('roll_no', $('enroll-roll').value.trim());
    fd.append('branch', $('enroll-branch').value.trim());
    fd.append('sem', $('enroll-sem').value.trim());
    fd.append('email', $('enroll-email').value.trim());
    fd.append('password', $('enroll-password').value.trim());
    fd.append('photo', $('enroll-photo').files[0]);

    if (!$('enroll-branch').value) {
      showError(errEl, 'Please select a branch.');
      btn.disabled = false;
      btn.textContent = 'Enroll Student';
      return;
    }
    if (!$('enroll-sem').value) {
      showError(errEl, 'Please select a semester.');
      btn.disabled = false;
      btn.textContent = 'Enroll Student';
      return;
    }

    await apiFetch('/api/students/enroll', { method: 'POST', body: fd });
    $('enroll-modal').style.display = 'none';
    loadStudents();
  } catch (err) {
    showError(errEl, err.message || 'Enrollment failed.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Enroll Student';
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
//  ADMIN: Attendance Tab
// ═══════════════════════════════════════════════════════════════════════════════

// Set default date to today
$('att-date').value = new Date().toISOString().split('T')[0];

// Populate subjects when branch or sem changes
$('att-branch').addEventListener('change', populateSubjectDropdown);
$('att-sem').addEventListener('change', populateSubjectDropdown);

$('attendance-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = $('att-submit');
  const errEl = $('att-error');
  const resultDiv = $('att-result');
  hideError(errEl);
  resultDiv.innerHTML = '';
  btn.disabled = true;
  btn.textContent = 'Processing… (may take ~30s)';

  try {
    const fd = new FormData();
    fd.append('photo', $('att-photo').files[0]);
    fd.append('date', $('att-date').value);
    if ($('att-branch').value)  fd.append('branch', $('att-branch').value);
    if ($('att-sem').value)     fd.append('sem', $('att-sem').value);
    if ($('att-subject').value) fd.append('subject', $('att-subject').value);

    if (!$('att-subject').value) {
      showError(errEl, 'Please select a subject before marking attendance.');
      btn.disabled = false;
      btn.textContent = 'Mark Attendance';
      return;
    }

    const data = await apiFetch('/api/attendance/mark', { method: 'POST', body: fd });

    let html = '';

    // Summary banner
    html += `<div class="result-banner success">
      ✓ <strong>${esc(data.subject || '')}</strong> &nbsp;|
      Detected ${data.faces_detected} face(s) — ${data.present_count} present, ${data.absent_count} absent
    </div>`;

    // Present students
    const present = (data.present_students || []);
    if (present.length > 0) {
      html += `<h3 style="margin-bottom:12px;font-size:0.9rem;color:var(--text-muted);">PRESENT (${present.length})</h3>`;
      html += `<div class="table-wrap" style="margin-bottom:20px;"><table>
        <thead><tr><th>Name</th><th>Roll No</th><th>Confidence</th></tr></thead><tbody>`;
      present.forEach(s => {
        html += `<tr>
          <td>${esc(s.name)}</td>
          <td><span class="badge badge-info">${esc(s.roll_no)}</span></td>
          <td><span class="badge badge-success">${(s.confidence * 100).toFixed(1)}%</span></td>
        </tr>`;
      });
      html += '</tbody></table></div>';
    }

    // Absent students
    const absent = (data.all_students || []).filter(s => s.status === 'absent');
    if (absent.length > 0) {
      html += `<h3 style="margin-bottom:12px;font-size:0.9rem;color:var(--text-muted);">ABSENT (${absent.length})</h3>`;
      html += `<div class="table-wrap"><table>
        <thead><tr><th>Name</th><th>Roll No</th></tr></thead><tbody>`;
      absent.forEach(s => {
        html += `<tr>
          <td>${esc(s.name)}</td>
          <td><span class="badge badge-danger">${esc(s.roll_no)}</span></td>
        </tr>`;
      });
      html += '</tbody></table></div>';
    }

    resultDiv.innerHTML = html;

  } catch (err) {
    showError(errEl, err.message || 'Failed to mark attendance.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Mark Attendance';
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
//  ADMIN: Logs Tab
// ═══════════════════════════════════════════════════════════════════════════════

async function loadLogs() {
  const tbody = $('logs-tbody');
  tbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-muted);text-align:center;padding:24px;">Loading…</td></tr>';

  try {
    const data = await apiFetch('/api/attendance/logs');
    allLogs = data.logs || [];

    // Populate subject filter
    const subjectSel = $('log-filter-subject');
    const uniqueSubjects = [...new Set(allLogs.map(l => l.subject).filter(Boolean))].sort();
    subjectSel.innerHTML = '<option value="">All Subjects</option>' +
      uniqueSubjects.map(s => `<option value="${esc(s)}">${esc(s)}</option>`).join('');

    renderLogs();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="error-msg">${esc(err.message)}</td></tr>`;
  }
}

function renderLogs() {
  const tbody = $('logs-tbody');

  // Flatten logs into rows
  let rows = [];
  allLogs.forEach(log => {
    (log.present_students || []).forEach(s => {
      rows.push({
        date: log.date,
        subject: log.subject || '—',
        name: s.name,
        roll_no: s.roll_no,
        confidence: s.confidence
      });
    });
  });

  // Apply filters
  const filterDate    = $('log-filter-date').value;
  const filterSubject = $('log-filter-subject').value;
  if (filterDate)    rows = rows.filter(r => r.date === filterDate);
  if (filterSubject) rows = rows.filter(r => r.subject === filterSubject);

  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-muted);text-align:center;padding:24px;">No logs found.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${esc(r.date)}</td>
      <td><span class="badge subject-badge">${esc(r.subject)}</span></td>
      <td>${esc(r.name)}</td>
      <td><span class="badge badge-info">${esc(r.roll_no)}</span></td>
      <td><span class="badge badge-success">${(r.confidence * 100).toFixed(1)}%</span></td>
    </tr>
  `).join('');
}

$('log-filter-date').addEventListener('change', renderLogs);
$('log-filter-subject').addEventListener('change', renderLogs);

// ═══════════════════════════════════════════════════════════════════════════════
//  STUDENT DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════

async function loadStudentDashboard() {
  const statsGrid     = $('student-stats');
  const subjGrid      = $('subject-stats-grid');
  const tbody         = $('student-records-tbody');
  const badgeEl       = $('student-attendance-badge');

  statsGrid.innerHTML = '';
  subjGrid.innerHTML  = '<p style="color:var(--text-muted);padding:12px 4px;">Loading…</p>';
  tbody.innerHTML     = '<tr><td colspan="4" style="color:var(--text-muted);text-align:center;padding:24px;">Loading…</td></tr>';

  try {
    const data = await apiFetch('/api/attendance/my');

    const student      = data.student      || {};
    const records      = data.records      || [];
    const totalPresent = data.total_present || 0;
    const subjectStats = data.subject_stats || {};

    // ── Profile stat cards ──────────────────────────────────────
    const totalSubjects = Object.keys(subjectStats).length;
    const overallPct = totalSubjects > 0
      ? Math.round(Object.values(subjectStats).reduce((s, v) => s + v.pct, 0) / totalSubjects)
      : 0;

    statsGrid.innerHTML = `
      <div class="stat-card"><div class="stat-label">Name</div><div class="stat-value" style="font-size:1.1rem;">${esc(student.name || '—')}</div></div>
      <div class="stat-card"><div class="stat-label">Roll Number</div><div class="stat-value" style="font-size:1.1rem;">${esc(student.roll_no || '—')}</div></div>
      <div class="stat-card"><div class="stat-label">Branch</div><div class="stat-value" style="font-size:1.1rem;">${esc(student.branch || '—')}</div></div>
      <div class="stat-card"><div class="stat-label">Semester</div><div class="stat-value" style="font-size:1.1rem;">${student.sem ? 'Sem ' + esc(String(student.sem)) : '—'}</div></div>
      <div class="stat-card"><div class="stat-label">Classes Attended</div><div class="stat-value green">${totalPresent}</div></div>
      <div class="stat-card"><div class="stat-label">Overall Attendance</div><div class="stat-value" style="color:${overallPct>=75?'#86efac':overallPct>=50?'#fde047':'#fca5a5'}">${overallPct}%</div></div>
    `;

    // Badge
    badgeEl.innerHTML = totalPresent > 0
      ? `<span class="badge badge-success">Active</span>`
      : `<span class="badge badge-danger">No Records</span>`;

    // ── Subject attendance cards ────────────────────────────────
    if (Object.keys(subjectStats).length === 0) {
      subjGrid.innerHTML = '<p style="color:var(--text-muted);padding:12px 4px;">No subject data yet. Attendance will appear here after classes are marked.</p>';
    } else {
      subjGrid.innerHTML = Object.entries(subjectStats)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([subj, st]) => {
          const pct  = st.pct;
          const deg  = Math.round(pct * 3.6); // 0..360
          const ringColor = pct >= 75 ? '#22c55e' : pct >= 50 ? '#eab308' : '#ef4444';
          const pillCls   = pct >= 75 ? 'ok' : pct >= 50 ? 'warn' : 'low';
          const pillTxt   = pct >= 75 ? 'Good' : pct >= 50 ? 'Average' : 'Low';
          return `
            <div class="subj-card">
              <div class="subj-name">${esc(subj)}</div>
              <div class="subj-ring-wrap">
                <div class="subj-ring" style="--ring-pct:${deg}deg;--ring-color:${ringColor}">
                  <span class="subj-pct">${pct}%</span>
                </div>
              </div>
              <div class="subj-counts">${st.present} / ${st.total} classes</div>
              <span class="subj-pill ${pillCls}">${pillTxt}</span>
            </div>`;
        }).join('');
    }

    // ── Detail log table ────────────────────────────────────────
    if (records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="color:var(--text-muted);text-align:center;padding:24px;">No attendance records yet.</td></tr>';
      return;
    }
    // Sort by date descending
    records.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    tbody.innerHTML = records.map(r => `
      <tr>
        <td>${esc(r.date || '—')}</td>
        <td><span class="badge subject-badge">${esc(r.subject || '—')}</span></td>
        <td>${r.status === 'absent'
          ? '<span class="badge badge-danger">Absent</span>'
          : '<span class="badge badge-success">Present</span>'}</td>
        <td style="color:var(--text-muted);font-size:0.8rem;">${r.status === 'absent' ? '—' : esc(r.timestamp || '—')}</td>
      </tr>
    `).join('');

  } catch (err) {
    statsGrid.innerHTML = `<div class="result-banner error">${esc(err.message)}</div>`;
    subjGrid.innerHTML  = '';
    tbody.innerHTML     = '';
  }
}
