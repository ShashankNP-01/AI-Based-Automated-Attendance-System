"""
Email Notification Service
Sends absence notification emails to students via Gmail SMTP.

Setup:
  1. Use a Gmail account
  2. Enable 2-Factor Authentication on that Gmail account
  3. Generate an App Password:
       Google Account → Security → 2-Step Verification → App Passwords
       Select "Mail" + "Windows Computer" → Generate
  4. Set in .env:
       EMAIL_SENDER=your_gmail@gmail.com
       EMAIL_PASSWORD=your_16_char_app_password
       EMAIL_ENABLED=true
"""

import smtplib
import ssl
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

load_dotenv(find_dotenv())

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL port

EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_ENABLED  = os.getenv("EMAIL_ENABLED", "false").lower() == "true"


def _build_absence_html(student_name: str, date: str, subject: str = "Class") -> str:
    """Build a styled HTML email body for absence notification."""
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 30px auto; background: #ffffff;
                  border-radius: 8px; overflow: hidden;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background-color: #e53e3e; padding: 24px 32px; color: #fff; }}
    .header h1 {{ margin: 0; font-size: 22px; }}
    .body {{ padding: 32px; color: #333; }}
    .body p {{ line-height: 1.7; margin: 0 0 16px; }}
    .highlight {{ background: #fff5f5; border-left: 4px solid #e53e3e;
                  padding: 12px 16px; border-radius: 4px; margin: 20px 0; }}
    .footer {{ padding: 16px 32px; background: #f8f8f8; font-size: 12px;
               color: #888; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>&#9888; Absence Notification</h1>
    </div>
    <div class="body">
      <p>Dear <strong>{student_name}</strong>,</p>
      <p>
        This is an automated notification from the
        <strong>AI Attendance System</strong>.
        Our system has recorded your absence for the following session:
      </p>
      <div class="highlight">
        <strong>Subject/Class:</strong> {subject}<br>
        <strong>Date:</strong> {date}
      </div>
      <p>
        If you believe this is an error or if you were present but not detected,
        please contact your class administrator immediately.
      </p>
      <p>
        Maintaining regular attendance is important for your academic progress.
        Please ensure your attendance is up to date.
      </p>
      <p>Regards,<br><strong>AI Attendance System</strong></p>
    </div>
    <div class="footer">
      This is an automated message. Please do not reply to this email.
    </div>
  </div>
</body>
</html>
"""


def send_absence_email(student_name: str, student_email: str,
                       date: str, subject: str = "Class") -> bool:
    """
    Send a single absence notification email.

    Args:
        student_name  : Student's full name
        student_email : Student's email address
        date          : Date string (e.g. '2026-02-21')
        subject       : Class / subject name shown in the email

    Returns:
        True on success, False on failure
    """
    if not EMAIL_ENABLED:
        print(f"📧 [Email disabled] Would notify {student_name} <{student_email}> for absence on {date}")
        return False

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("⚠️  EMAIL_SENDER / EMAIL_PASSWORD not set in .env — skipping email")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Absence Notice – {date}"
        msg["From"]    = f"AI Attendance System <{EMAIL_SENDER}>"
        msg["To"]      = student_email

        # Plain-text fallback
        plain_text = (
            f"Dear {student_name},\n\n"
            f"You were marked ABSENT for '{subject}' on {date}.\n\n"
            f"If this is an error, please contact your administrator.\n\n"
            f"Regards,\nAI Attendance System"
        )

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(_build_absence_html(student_name, date, subject), "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, student_email, msg.as_string())

        print(f"✅ Absence email sent to {student_name} <{student_email}> for {date}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Email auth failed — check EMAIL_SENDER and EMAIL_PASSWORD in .env")
        return False
    except Exception as e:
        print(f"❌ Failed to send email to {student_email}: {e}")
        return False


def notify_absent_students_async(absent_students: list, date: str, subject: str = "Class"):
    """
    Send absence notification emails to all absent students in a background thread.
    Non-blocking — the API response is returned immediately while emails send.

    Args:
        absent_students : list of dicts [{'name': str, 'email': str}, ...]
        date            : attendance date string
        subject         : class / subject name
    """
    if not absent_students:
        return

    def _send_all():
        print(f"📧 Sending {len(absent_students)} absence notification(s) for {date}...")
        success = 0
        for student in absent_students:
            ok = send_absence_email(
                student_name=student.get('name', 'Student'),
                student_email=student.get('email', ''),
                date=date,
                subject=subject
            )
            if ok:
                success += 1
        print(f"📧 Email summary: {success}/{len(absent_students)} sent successfully")

    thread = threading.Thread(target=_send_all, daemon=True)
    thread.start()
