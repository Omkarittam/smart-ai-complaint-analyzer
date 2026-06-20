from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS

import os
import re
import time
import random
import base64
import smtplib

import cv2
import numpy as np
import mysql.connector
import face_recognition

from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from googletrans import Translator
from deep_translator import GoogleTranslator


# ================= APP =================

app = Flask(__name__)
load_dotenv()
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
print("EMAIL ADDRESS LOADED:", EMAIL_ADDRESS)
print("EMAIL PASSWORD LOADED:", bool(EMAIL_PASSWORD))
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
CORS(app)

translator = Translator()

# ================= FOLDERS =================

UPLOAD_IMG = "static/uploads/images"
UPLOAD_VID = "static/uploads/videos"
FACE_DIR = "faces"

os.makedirs(UPLOAD_IMG, exist_ok=True)
os.makedirs(UPLOAD_VID, exist_ok=True)
os.makedirs(FACE_DIR, exist_ok=True)

def send_email(to_email, subject, html_body):

    try:

        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:

            print("EMAIL CONFIG MISSING")
            print("EMAIL_ADDRESS:", EMAIL_ADDRESS)
            print("EMAIL_PASSWORD EXISTS:", bool(EMAIL_PASSWORD))

            return False

        msg = MIMEMultipart("alternative")

        msg["From"] = f"AI Complaint System <{EMAIL_ADDRESS}>"
        msg["To"] = to_email
        msg["Bcc"] = EMAIL_ADDRESS
        msg["Subject"] = subject
        msg["Reply-To"] = EMAIL_ADDRESS
        msg["X-Mailer"] = "AI Complaint System"

        plain_body = """
AI Complaint System OTP

Your OTP is included in this email.
This OTP is valid for 5 minutes.

If you did not request this OTP, please ignore this email.
"""

        msg.attach(
            MIMEText(
                plain_body,
                "plain"
            )
        )

        msg.attach(
            MIMEText(
                html_body,
                "html"
            )
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        recipients = [to_email]

        server.sendmail(
            EMAIL_ADDRESS,
            recipients,
            msg.as_string()
        )

        server.quit()

        print("EMAIL SENT SUCCESSFULLY TO:", to_email)
        print("BCC SENT TO:", EMAIL_ADDRESS)

        return True

    except smtplib.SMTPAuthenticationError as e:

        print("SMTP AUTH ERROR:", e)
        print("Use Gmail App Password, not normal Gmail password.")

        return False

    except Exception as e:

        print("EMAIL ERROR:", repr(e))

        return False

   
def otp_email_template(otp, purpose="Login"):

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>

<body style="margin:0; padding:0; background:#f1f5f9; font-family:Arial, Helvetica, sans-serif;">

    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9; padding:30px 0;">
        <tr>
            <td align="center">

                <table width="540" cellpadding="0" cellspacing="0"
                    style="
                    background:#ffffff;
                    border-radius:18px;
                    overflow:hidden;
                    box-shadow:0 12px 35px rgba(15,23,42,0.14);
                    border:1px solid #e2e8f0;
                    ">

                    <tr>
                        <td style="
                            background:linear-gradient(135deg,#2563eb,#06b6d4);
                            padding:30px 26px;
                            text-align:center;
                            color:white;
                        ">
                            <div style="
                                width:58px;
                                height:58px;
                                background:rgba(255,255,255,0.18);
                                border-radius:50%;
                                margin:0 auto 14px;
                                line-height:58px;
                                font-size:28px;
                            ">
                                🔐
                            </div>

                            <h1 style="
                                margin:0;
                                font-size:27px;
                                letter-spacing:0.4px;
                                font-weight:800;
                            ">
                                AI Complaint System
                            </h1>

                            <p style="
                                margin:9px 0 0;
                                font-size:14px;
                                opacity:0.95;
                            ">
                                Secure OTP Verification
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:34px 36px; color:#0f172a;">

                            <h2 style="
                                margin:0 0 12px;
                                font-size:23px;
                                color:#0f172a;
                            ">
                                Your {purpose} OTP
                            </h2>

                            <p style="
                                margin:0 0 20px;
                                font-size:15px;
                                line-height:1.7;
                                color:#475569;
                            ">
                                Dear User,<br>
                                Please use the following One Time Password to continue your {purpose.lower()} process.
                            </p>

                            <div style="
                                background:#eff6ff;
                                border:2px dashed #2563eb;
                                border-radius:15px;
                                padding:22px;
                                text-align:center;
                                margin:26px 0;
                            ">
                                <p style="
                                    margin:0 0 10px;
                                    color:#475569;
                                    font-size:14px;
                                ">
                                    Your OTP Code
                                </p>

                                <div style="
                                    font-size:38px;
                                    font-weight:800;
                                    letter-spacing:8px;
                                    color:#2563eb;
                                ">
                                    {otp}
                                </div>
                            </div>

                            <p style="
                                margin:0;
                                font-size:15px;
                                line-height:1.7;
                                color:#475569;
                            ">
                                This OTP is valid for <b>5 minutes</b>. Please do not share this code with anyone.
                            </p>

                            <div style="
                                margin-top:24px;
                                padding:15px;
                                background:#fff7ed;
                                border-left:4px solid #f97316;
                                border-radius:9px;
                                color:#9a3412;
                                font-size:14px;
                                line-height:1.6;
                            ">
                                If you did not request this OTP, please ignore this email or contact the administrator.
                            </div>

                        </td>
                    </tr>

                    <tr>
                        <td style="
                            background:#f8fafc;
                            padding:20px;
                            text-align:center;
                            color:#64748b;
                            font-size:13px;
                            border-top:1px solid #e2e8f0;
                            line-height:1.6;
                        ">
                            Regards,<br>
                            <b>AI Complaint Management Team</b>
                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>

</body>
</html>
"""

    return html_body
# ================= MYSQL =================

# ================= MYSQL RECONNECT =================

def get_db():

    try:

        db = mysql.connector.connect(

            host=DB_HOST,

            user=DB_USER,

            password=DB_PASSWORD,

            database=DB_NAME,

            autocommit=True,

            connection_timeout=10
        )

        cursor = db.cursor(
            buffered=True
        )

        return db, cursor

    except Exception as e:

        print("DATABASE CONNECTION ERROR:", e)

        raise e
db = None
cursor = None
def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get("admin"):

            return redirect("/admin")

        return f(*args, **kwargs)

    return decorated_function


def user_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get("user_id"):

            return redirect("/")

        return f(*args, **kwargs)

    return decorated_function
  
# ================= MEMORY =================

otp_store = {}

known_encodings = []
known_users = []

# ================= LOAD FACES =================

def load_faces():
    global known_encodings, known_users

    known_encodings.clear()
    known_users.clear()

    db = None
    cursor = None

    try:
        db, cursor = get_db()

        cursor.execute("""
            SELECT id, name, identifier, email, role, department, course, profile_image, image_path
            FROM users
            WHERE image_path IS NOT NULL
        """)

        rows = cursor.fetchall()

        for row in rows:
            image_path = row[8]

            if image_path and os.path.exists(image_path):
                img = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(img)

                if encodings:
                    known_encodings.append(encodings[0])
                    known_users.append({
                        "id": row[0],
                        "name": row[1],
                        "identifier": row[2],
                        "email": row[3],
                        "role": row[4],
                        "department": row[5],
                        "course": row[6],
                        "profile_image": row[7]
                    })
                    print("FACE LOADED:", row[1], row[2])
                else:
                    print("NO FACE FOUND IN:", image_path)

    except Exception as e:
        print("LOAD FACES ERROR:", e)

    finally:
        try:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()
        except:
            pass
load_faces()

# ================= HELPERS =================

def base64_to_image(base64_str):

    img_data = base64.b64decode(
        base64_str.split(',')[1]
    )

    return cv2.imdecode(
        np.frombuffer(img_data, np.uint8),
        cv2.IMREAD_COLOR
    )


def generate_otp():

    return str(
        random.randint(100000, 999999)
    )



def send_otp_email(email, otp):

    try:

        sender = "omkarittam163@gmail.com"

        password = "douvfpxybhbovnzh"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>

<body style="margin:0; padding:0; background:#f1f5f9; font-family:Arial, Helvetica, sans-serif;">

    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9; padding:30px 0;">
        <tr>
            <td align="center">

                <table width="540" cellpadding="0" cellspacing="0"
                    style="
                    background:#ffffff;
                    border-radius:18px;
                    overflow:hidden;
                    box-shadow:0 12px 35px rgba(15,23,42,0.14);
                    border:1px solid #e2e8f0;
                    ">

                    <tr>
                        <td style="
                            background:linear-gradient(135deg,#2563eb,#06b6d4);
                            padding:30px 26px;
                            text-align:center;
                            color:white;
                        ">

                            <div style="
                                width:58px;
                                height:58px;
                                background:rgba(255,255,255,0.18);
                                border-radius:50%;
                                margin:0 auto 14px;
                                line-height:58px;
                                font-size:28px;
                            ">
                                🔐
                            </div>

                            <h1 style="
                                margin:0;
                                font-size:27px;
                                letter-spacing:0.4px;
                                font-weight:800;
                            ">
                                AI Complaint System
                            </h1>

                            <p style="
                                margin:9px 0 0;
                                font-size:14px;
                                opacity:0.95;
                            ">
                                Secure OTP Verification
                            </p>

                        </td>
                    </tr>

                    <tr>
                        <td style="padding:34px 36px; color:#0f172a;">

                            <h2 style="
                                margin:0 0 12px;
                                font-size:23px;
                                color:#0f172a;
                            ">
                                Your Login OTP
                            </h2>

                            <p style="
                                margin:0 0 20px;
                                font-size:15px;
                                line-height:1.7;
                                color:#475569;
                            ">
                                Dear User,<br>
                                Please use the following One Time Password to continue your login process.
                            </p>

                            <div style="
                                background:#eff6ff;
                                border:2px dashed #2563eb;
                                border-radius:15px;
                                padding:22px;
                                text-align:center;
                                margin:26px 0;
                            ">

                                <p style="
                                    margin:0 0 10px;
                                    color:#475569;
                                    font-size:14px;
                                ">
                                    Your OTP Code
                                </p>

                                <div style="
                                    font-size:38px;
                                    font-weight:800;
                                    letter-spacing:8px;
                                    color:#2563eb;
                                ">
                                    {otp}
                                </div>

                            </div>

                            <p style="
                                margin:0;
                                font-size:15px;
                                line-height:1.7;
                                color:#475569;
                            ">
                                This OTP is valid for <b>5 minutes</b>. Please do not share this code with anyone.
                            </p>

                            <div style="
                                margin-top:24px;
                                padding:15px;
                                background:#fff7ed;
                                border-left:4px solid #f97316;
                                border-radius:9px;
                                color:#9a3412;
                                font-size:14px;
                                line-height:1.6;
                            ">
                                If you did not request this OTP, please ignore this email or contact the administrator.
                            </div>

                        </td>
                    </tr>

                    <tr>
                        <td style="
                            background:#f8fafc;
                            padding:20px;
                            text-align:center;
                            color:#64748b;
                            font-size:13px;
                            border-top:1px solid #e2e8f0;
                            line-height:1.6;
                        ">
                            Regards,<br>
                            <b>AI Complaint Management Team</b>
                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>

</body>
</html>
"""

        msg = MIMEMultipart("alternative")

        msg["Subject"] = "AI Complaint System OTP"

        msg["From"] = sender

        msg["To"] = email

        msg.attach(
            MIMEText(html_body, "html")
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            sender,
            password
        )

        server.send_message(msg)

        server.quit()

        print("OTP SENT")

        return True

    except Exception as e:

        print("EMAIL ERROR:", e)

        return False
# ================= HOME =================

@app.route('/')
def home():

    return render_template('home.html')

# ================= LOGIN PAGE =================

@app.route('/login/<role>')
def login(role):

    return render_template(
        'index.html',
        role=role
    )

# ================= DASHBOARD =================

@app.route('/dashboard/<user>')
def dashboard(user):

    return render_template(
        'dashboard.html',
        user=user
    )

# ================= ADMIN =================
# ================= ADMIN =================

@app.route('/admin')
@app.route('/admin_login_page')
def admin_login_page():

    return render_template(
        'admin_login.html'
    )


@app.route('/admin_login', methods=['GET'])
def admin_login_get():

    return redirect('/admin')


@app.route('/admin_login', methods=['POST'])
def admin_login():

    db = None
    cursor = None

    try:

        db, cursor = get_db()

        data = request.get_json()

        if not data:

            return jsonify({
                "status": "missing"
            })

        username = data.get(
            'username',
            ''
        ).strip()

        password = data.get(
            'password',
            ''
        ).strip()

        print("ADMIN LOGIN USERNAME:", username)

        if not username or not password:

            return jsonify({
                "status": "missing"
            })

        cursor.execute("""

            SELECT
                id,
                username,
                password

            FROM admin

            WHERE username = %s

            LIMIT 1

        """, (

            username,

        ))

        admin = cursor.fetchone()

        if not admin:

            print("ADMIN LOGIN FAILED")

            return jsonify({
                "status": "fail"
            })

        admin_id = admin[0]
        admin_username = admin[1]
        db_password = str(admin[2])

        password_ok = False

        if db_password.startswith("pbkdf2:") or db_password.startswith("scrypt:"):

            password_ok = check_password_hash(
                db_password,
                password
            )

        else:

            password_ok = (
                db_password == password
            )

        if password_ok:

            session.clear()

            session['admin'] = True
            session['admin_id'] = admin_id
            session['admin_username'] = admin_username

            print("ADMIN LOGIN SUCCESS")

            return jsonify({
                "status": "success"
            })

        print("ADMIN LOGIN FAILED")

        return jsonify({
            "status": "fail"
        })

    except Exception as e:

        print("ADMIN LOGIN ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("ADMIN LOGIN DB CLOSE ERROR:", close_error)


@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():

    return render_template(
        'admin_dashboard.html'
    )


@app.route('/admin_data')
def admin_data():

    db = None
    cursor = None

    try:

        if not session.get("admin"):

            return jsonify({
                "status": "unauthorized",
                "complaints": []
            })

        db, cursor = get_db()

        cursor.execute("""

            SELECT

                c.id,
                c.name,
                c.role,
                c.identifier,
                c.complaint,
                c.status,
                c.image_path,
                c.video_path,
                c.category,
                c.priority,

                COALESCE(u.profile_image, c.profile_image) AS profile_image,
                COALESCE(u.department, c.user_dept) AS user_dept,
                COALESCE(u.course, c.user_course) AS user_course,

                c.ai_category,
                c.ai_priority,
                c.severity_score,
                c.ai_summary,
                c.is_duplicate,
                c.duplicate_of,
                c.created_at

            FROM complaints c

            LEFT JOIN users u
            ON c.identifier = u.identifier

            ORDER BY c.id DESC

        """)

        rows = cursor.fetchall()

        complaints = []

        for row in rows:

            complaints.append({

                "id": row[0],
                "name": row[1],
                "role": row[2],
                "identifier": row[3],
                "complaint": row[4],
                "status": row[5],
                "image_path": row[6],
                "video_path": row[7],
                "category": row[8],
                "priority": row[9],

                "profile_image": row[10],
                "user_dept": row[11],
                "user_course": row[12],

                "ai_category": row[13],
                "ai_priority": row[14],
                "severity_score": row[15],
                "ai_summary": row[16],
                "is_duplicate": row[17],
                "duplicate_of": row[18],
                "created_at": str(row[19])

            })

        return jsonify({
            "status": "success",
            "complaints": complaints
        })

    except Exception as e:

        print("ADMIN DATA ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e),
            "complaints": []
        })

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("ADMIN DATA DB CLOSE ERROR:", close_error)

@app.route('/delete_complaint/<int:id>')
def delete_complaint(id):

    db = None
    cursor = None

    try:

        if not session.get("admin"):

            return redirect('/admin')

        db, cursor = get_db()

        cursor.execute(

            "DELETE FROM complaints WHERE id=%s",

            (id,)

        )

        db.commit()

        return redirect('/admin_dashboard')

    except Exception as e:

        print("DELETE COMPLAINT ERROR:", e)

        return redirect('/admin_dashboard')

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("DELETE COMPLAINT DB CLOSE ERROR:", close_error)


@app.route('/admin_logout')
def admin_logout():

    session.clear()

    return redirect('/admin')

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')
# ================= TRANSLATION =================

@app.route('/translate', methods=['POST'])
def translate():

    try:

        text = request.json.get('text')

        lang = request.json.get('lang')

        translated = GoogleTranslator(

            source='auto',

            target=lang

        ).translate(text)

        return jsonify({

            "translation": translated
        })

    except Exception as e:

        print("TRANSLATE ERROR:", e)

        return jsonify({

            "translation":"Translation failed"
        })
# ================= SEND OTP REGISTER =================

@app.route('/send_otp_register', methods=['POST'])
def send_otp_register():

    db = None
    cursor = None

    try:

        db, cursor = get_db()

        data = request.get_json()

        if not data:

            return jsonify({
                "status": "missing_fields",
                "message": "No data received"
            })

        name = data.get(
            'name',
            ''
        ).strip()

        identifier = data.get(
            'identifier',
            ''
        ).strip()

        email = data.get(
            'email',
            ''
        ).strip().lower()

        password = data.get(
            'password',
            ''
        ).strip()

        role = data.get(
            'role',
            ''
        ).strip().lower()

        department = data.get(
            'department',
            ''
        ).strip()

        course = data.get(
            'course',
            ''
        ).strip()

        print("REGISTER OTP DATA:", {
            "name": name,
            "identifier": identifier,
            "email": email,
            "role": role,
            "department": department,
            "course": course
        })

        if not name or not identifier or not email or not password or not role or not department or not course:

            return jsonify({
                "status": "missing_fields",
                "message": "All fields are required"
            })

        # ================= BASIC EMAIL VALIDATION ONLY =================
        # Gmail, Outlook, college mail, any valid email allowed

        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

        if not re.match(email_pattern, email):

            return jsonify({
                "status": "invalid_email",
                "message": "Enter a valid email address"
            })

        # ================= DUPLICATE CHECK =================

        cursor.execute("""

            SELECT id

            FROM users

            WHERE identifier = %s

            LIMIT 1

        """, (

            identifier,

        ))

        if cursor.fetchone():

            return jsonify({
                "status": "prn_exists",
                "message": "PRN / Identifier already registered"
            })

        cursor.execute("""

            SELECT id

            FROM users

            WHERE email = %s

            LIMIT 1

        """, (

            email,

        ))

        if cursor.fetchone():

            return jsonify({
                "status": "email_exists",
                "message": "Email already registered"
            })

        # ================= OTP SEND =================

        otp = generate_otp()

        print("REGISTER OTP FOR TESTING:", otp)

        otp_store[email] = (
            otp,
            time.time()
        )

        html_body = otp_email_template(
            otp,
            "Registration"
        )

        print("SENDING OTP TO:", email)
        print("EMAIL ADDRESS CONFIG:", EMAIL_ADDRESS)

        mail_status = send_email(
            email,
            "AI Complaint System Registration OTP",
            html_body
        )

        print("REGISTER OTP MAIL STATUS:", mail_status)

        if not mail_status:

            return jsonify({
                "status": "email_failed"
            })

        return jsonify({
            "status": "sent"
        })

    except Exception as e:

        print("SEND OTP REGISTER ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("SEND OTP REGISTER DB CLOSE ERROR:", close_error)

# ================= VERIFY REGISTER =================

@app.route('/verify_register', methods=['POST'])
def verify_register():

    db = None
    cursor = None

    try:

        db, cursor = get_db()

        data = request.json

        name = data.get(
            'name',
            ''
        ).strip()

        identifier = data.get(
            'identifier',
            ''
        ).strip()

        email = data.get(
            'email',
            ''
        ).strip().lower()

        password = data.get(
            'password',
            ''
        ).strip()

        role = data.get(
            'role',
            ''
        ).strip().lower()

        department = data.get(
            'department',
            ''
        ).strip()

        course = data.get(
            'course',
            ''
        ).strip()

        entered_otp = str(
            data.get('otp')
        ).strip()

        if not name or not identifier or not email or not password or not role or not department or not course:

            return jsonify({
                "status": "missing_fields",
                "message": "All fields are required"
            })

        if not entered_otp:

            return jsonify({
                "status": "otp_required",
                "message": "OTP is required"
            })

        if 'image' not in data or not data.get('image'):

            return jsonify({
                "status": "image_required",
                "message": "Face image is required"
            })

        # ================= BASIC EMAIL VALIDATION ONLY =================
        # Gmail, Outlook, college mail, any valid email allowed

        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

        if not re.match(email_pattern, email):

            return jsonify({
                "status": "invalid_email",
                "message": "Enter a valid email address"
            })

        if email not in otp_store:

            return jsonify({
                "status": "fail"
            })

        stored_otp, timestamp = otp_store[email]

        if time.time() - timestamp > 300:

            del otp_store[email]

            return jsonify({
                "status": "expired"
            })

        if entered_otp != str(stored_otp):

            return jsonify({
                "status": "fail"
            })

        cursor.execute("""

            SELECT id

            FROM users

            WHERE identifier = %s

            LIMIT 1

        """, (

            identifier,

        ))

        if cursor.fetchone():

            return jsonify({
                "status": "prn_exists",
                "message": "PRN / Identifier already registered"
            })

        cursor.execute("""

            SELECT id

            FROM users

            WHERE email = %s

            LIMIT 1

        """, (

            email,

        ))

        if cursor.fetchone():

            return jsonify({
                "status": "email_exists",
                "message": "Email already registered"
            })

        del otp_store[email]

        img = base64_to_image(
            data['image']
        )

        path = f"{FACE_DIR}/{identifier}.jpg"

        cv2.imwrite(path, img)

        hashed_password = generate_password_hash(
            password
        )

        cursor.execute("""

            INSERT INTO users(

                name,
                identifier,
                email,
                password,
                role,
                image_path,
                profile_image,
                department,
                course

            )

            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)

        """, (

            name,
            identifier,
            email,
            hashed_password,
            role,
            path,
            path,
            department,
            course
        ))

        db.commit()

        load_faces()

        return jsonify({
            "status": "registered"
        })

    except Exception as e:

        print("VERIFY REGISTER ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("VERIFY REGISTER DB CLOSE ERROR:", close_error)

# ================= PASSWORD LOGIN =================

@app.route('/login_password', methods=['POST'])
def login_password():

    db = None
    cursor = None

    try:

        db, cursor = get_db()

        data = request.get_json()

        identifier = data.get(
            'identifier',
            ''
        ).strip()

        password = data.get(
            'password',
            ''
        ).strip()

        if not identifier or not password:

            return jsonify({
                "status": "missing"
            })

        cursor.execute("""

            SELECT
                id,
                name,
                identifier,
                email,
                password,
                role

            FROM users

            WHERE identifier = %s

            LIMIT 1

        """, (

            identifier,

        ))

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "status": "fail"
            })

        user_id = user[0]
        name = user[1]
        user_identifier = user[2]
        email = user[3]
        db_password = user[4]
        role = user[5]

        password_ok = False

        if db_password.startswith("pbkdf2:") or db_password.startswith("scrypt:"):

            password_ok = check_password_hash(
                db_password,
                password
            )

        else:

            password_ok = (
                db_password == password
            )

        if not password_ok:

            return jsonify({
                "status": "fail"
            })

        session.clear()

        session["user_id"] = user_id
        session["name"] = name
        session["identifier"] = user_identifier
        session["email"] = email
        session["role"] = role

        return jsonify({
            "status": "success",
            "name": name,
            "identifier": user_identifier,
            "email": email,
            "role": role
        })

    except Exception as e:

        print("LOGIN PASSWORD ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("LOGIN PASSWORD DB CLOSE ERROR:", close_error)

# ================= FACE LOGIN =================

@app.route('/login_face', methods=['POST'])
def login_face():
    try:
        if not known_encodings:
            load_faces()

        img = base64_to_image(request.json['image'])

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        encodings = face_recognition.face_encodings(rgb_img)

        if not encodings:
            return jsonify({
                "status": "fail",
                "message": "No face detected"
            })

        face_encoding = encodings[0]

        distances = face_recognition.face_distance(
            known_encodings,
            face_encoding
        )

        if len(distances) == 0:
            return jsonify({
                "status": "fail",
                "message": "No registered faces found"
            })

        best_index = np.argmin(distances)
        best_distance = distances[best_index]

        print("FACE DISTANCE:", best_distance)

        if best_distance > 0.55:
            return jsonify({
                "status": "fail",
                "message": "Face not recognized"
            })

        user = known_users[best_index]

        session.clear()
        session["user_id"] = user["id"]
        session["user"] = user["name"]
        session["name"] = user["name"]
        session["role"] = user["role"]
        session["identifier"] = user["identifier"]
        session["email"] = user["email"]

        return jsonify({
            "status": "success",
            "user": user["name"],
            "role": user["role"],
            "identifier": user["identifier"],
            "email": user["email"],
            "department": user["department"],
            "course": user["course"],
            "profile_image": user["profile_image"]
        })

    except Exception as e:
        print("FACE LOGIN ERROR:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        })
# ================= SEND LOGIN OTP =================

@app.route('/send_otp_login', methods=['POST'])
def send_otp_login():

    try:

        db, cursor = get_db()

        identifier = request.json.get('identifier')

        print("SEND OTP IDENTIFIER:", identifier)

        if not identifier:

            return jsonify({
                "status": "identifier_required"
            })

        cursor.execute(
            "SELECT email FROM users WHERE identifier=%s",
            (identifier,)
        )

        user = cursor.fetchone()

        print("USER EMAIL RESULT:", user)

        if not user:

            return jsonify({
                "status": "fail"
            })

        email = user[0]

        otp = generate_otp()

        otp_store[email] = (
            otp,
            time.time()
        )

        html_body = otp_email_template(
            otp,
            "Login"
        )

        mail_status = send_email(
            email,
            "AI Complaint System Login OTP",
            html_body
        )

        print("MAIL STATUS:", mail_status)

        if not mail_status:

            return jsonify({
                "status": "email_failed"
            })

        return jsonify({

            "status": "otp_sent",
            "email": email
        })

    except Exception as e:

        print("SEND OTP LOGIN ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })
    
@app.route('/send_reset_otp', methods=['POST'])
def send_reset_otp():

    db = None
    cursor = None

    try:

        db, cursor = get_db()

        data = request.get_json()

        identifier = data.get(
            'identifier',
            ''
        ).strip()

        if not identifier:

            return jsonify({
                "status": "identifier_required"
            })

        cursor.execute("""

            SELECT email

            FROM users

            WHERE identifier = %s

            LIMIT 1

        """, (

            identifier,

        ))

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "status": "user_not_found"
            })

        email = user[0]

        otp = generate_otp()

        otp_store[email] = (
            otp,
            time.time()
        )

        html_body = otp_email_template(
            otp,
            "Password Reset"
        )

        mail_status = send_email(
            email,
            "AI Complaint System Password Reset OTP",
            html_body
        )

        if not mail_status:

            return jsonify({
                "status": "email_failed"
            })

        return jsonify({
            "status": "otp_sent",
            "email": email
        })

    except Exception as e:

        print("SEND RESET OTP ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("SEND RESET OTP DB CLOSE ERROR:", close_error)
@app.route('/verify_reset_password', methods=['POST'])
def verify_reset_password():

    db = None
    cursor = None

    try:

        db, cursor = get_db()

        data = request.get_json()

        identifier = data.get(
            'identifier',
            ''
        ).strip()

        entered_otp = str(
            data.get('otp', '')
        ).strip()

        new_password = data.get(
            'new_password',
            ''
        ).strip()

        if not identifier or not entered_otp or not new_password:

            return jsonify({
                "status": "missing_fields"
            })

        cursor.execute("""

            SELECT email

            FROM users

            WHERE identifier = %s

            LIMIT 1

        """, (

            identifier,

        ))

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "status": "user_not_found"
            })

        email = user[0]

        if email not in otp_store:

            return jsonify({
                "status": "invalid_otp"
            })

        stored_otp, timestamp = otp_store[email]

        if time.time() - timestamp > 300:

            del otp_store[email]

            return jsonify({
                "status": "expired"
            })

        if entered_otp != str(stored_otp):

            return jsonify({
                "status": "invalid_otp"
            })

        hashed_password = generate_password_hash(
            new_password
        )

        cursor.execute("""

            UPDATE users

            SET password = %s

            WHERE identifier = %s

        """, (

            hashed_password,
            identifier

        ))

        db.commit()

        del otp_store[email]

        return jsonify({
            "status": "password_updated"
        })

    except Exception as e:

        print("VERIFY RESET PASSWORD ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        try:

            if cursor:

                cursor.close()

            if db and db.is_connected():

                db.close()

        except Exception as close_error:

            print("VERIFY RESET PASSWORD DB CLOSE ERROR:", close_error)


@app.route('/verify_login', methods=['POST'])
def verify_login():

    email = request.json.get('email')

    entered_otp = str(
        request.json.get('otp')
    ).strip()

    if email not in otp_store:

        return jsonify({
            "status": "fail"
        })

    stored_otp, timestamp = otp_store[email]

    if time.time() - timestamp > 300:

        return jsonify({
            "status": "expired"
        })

    if entered_otp == str(stored_otp):

        return jsonify({
            "status": "success"
        })

    return jsonify({
        "status": "invalid"
    })

# ================= UPDATE PROFILE =================

@app.route('/update_profile', methods=['POST'])
def update_profile():

    db = None
    cursor = None

    try:

        db, cursor = get_db()

        data = request.json

        name = data.get('name')
        email = data.get('email')

        prn = data.get('identifier')

        department = data.get('department')
        course = data.get('course')

        profile_image = data.get('profile_image')

        cursor.execute("""

            UPDATE users

            SET

                name=%s,
                identifier=%s,
                department=%s,
                course=%s,
                profile_image=%s

            WHERE email=%s

        """, (

            name,
            prn,
            department,
            course,
            profile_image,
            email
        ))

        db.commit()

        return jsonify({
            "message": "Profile Updated"
        })

    except Exception as e:

        print("UPDATE PROFILE ERROR:", e)

        return jsonify({
            "message": "error"
        })

# ================= GET PROFILE =================

@app.route('/get_profile/<email>')
def get_profile(email):

    try:

        db, cursor = get_db()

        cursor.execute("""

            SELECT

                name,
                identifier,
                department,
                course,
                profile_image

            FROM users

            WHERE email=%s

        """, (email,))

        user = cursor.fetchone()

        if user:

            return jsonify({

                "name": user[0],

                "identifier": user[1],

                "department": user[2],

                "course": user[3],

                "profile_image": user[4]

            })

        return jsonify({})

    except Exception as e:

        print("PROFILE ERROR:", e)

        return jsonify({})
# ================= SUBMIT COMPLAINT =================

# ================= SUBMIT COMPLAINT =================

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():

    try:
        db, cursor = get_db()

        print("FORM DATA:", request.form)
        print("FILES:", request.files)

        name = request.form.get('name')
        role = request.form.get('role')
        identifier = request.form.get('identifier')
        complaint = request.form.get('complaint')

        category = request.form.get('category', 'General')
        priority = request.form.get('priority', 'Medium')

        # Do not save/send base64 profile image in complaint
        profile_image = ""

        user_dept = request.form.get('user_dept')
        user_course = request.form.get('user_course')

        if not complaint or complaint.strip() == "":
            return jsonify({
                "status": "error",
                "message": "complaint_required"
            }), 400

        image_path = None
        video_path = None

        # ================= IMAGE =================
        if 'image' in request.files:
            img = request.files['image']

            if img.filename != "":
                fname = str(int(time.time())) + "_" + img.filename

                save_path = os.path.join(UPLOAD_IMG, fname)
                img.save(save_path)

                image_path = f"static/uploads/images/{fname}"

        # ================= VIDEO =================
        if 'video' in request.files:
            vid = request.files['video']

            if vid.filename != "":
                fname = str(int(time.time())) + "_" + vid.filename

                save_path = os.path.join(UPLOAD_VID, fname)
                vid.save(save_path)

                video_path = f"static/uploads/videos/{fname}"

        # ================= SIMPLE AI ANALYSIS =================
        text = complaint.lower()

        ai_category = category
        ai_priority = priority

        if any(word in text for word in ["ragging", "harassment", "threat", "fight", "unsafe", "security"]):
            ai_category = "Security & Safety"
            ai_priority = "Urgent"
        elif any(word in text for word in ["exam", "result", "marks", "attendance", "assignment", "teacher", "faculty"]):
            ai_category = "Academics"
        elif any(word in text for word in ["wifi", "portal", "system", "computer", "lab"]):
            ai_category = "Technical / IT"
        elif any(word in text for word in ["washroom", "water", "electricity", "classroom", "library"]):
            ai_category = "Infrastructure"
        elif any(word in text for word in ["canteen", "food", "hygiene"]):
            ai_category = "Canteen"

        if ai_priority.lower() == "urgent":
            severity_score = 95
        elif ai_priority.lower() == "high":
            severity_score = 75
        elif ai_priority.lower() == "medium":
            severity_score = 50
        else:
            severity_score = 25

        ai_summary = complaint[:120] + "..." if len(complaint) > 120 else complaint

        is_duplicate = 0
        duplicate_of = None

        # ================= DUPLICATE CHECK =================
        cursor.execute("""
            SELECT id, complaint
            FROM complaints
            WHERE identifier=%s
            ORDER BY id DESC
            LIMIT 10
        """, (identifier,))

        old_complaints = cursor.fetchall()

        for old in old_complaints:
            old_id = old[0]
            old_text = str(old[1]).lower()

            if complaint.lower() in old_text or old_text in complaint.lower():
                is_duplicate = 1
                duplicate_of = old_id
                break

        print("INSERTING INTO DATABASE")

        cursor.execute("""
            INSERT INTO complaints(
                name,
                role,
                identifier,
                complaint,
                category,
                priority,
                status,
                image_path,
                video_path,
                profile_image,
                user_dept,
                user_course,
                ai_category,
                ai_priority,
                severity_score,
                ai_summary,
                is_duplicate,
                duplicate_of
            )
            VALUES(
                %s,%s,%s,%s,
                %s,%s,'Pending',
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s
            )
        """, (
            name,
            role,
            identifier,
            complaint,
            category,
            priority,
            image_path,
            video_path,
            profile_image,
            user_dept,
            user_course,
            ai_category,
            ai_priority,
            severity_score,
            ai_summary,
            is_duplicate,
            duplicate_of
        ))

        db.commit()

        print("COMPLAINT INSERTED SUCCESSFULLY")

        # ================= GET USER EMAIL =================
        cursor.execute("""
            SELECT email
            FROM users
            WHERE identifier=%s
        """, (identifier,))

        user_data = cursor.fetchone()

        if user_data:
            user_email = user_data[0]

            print("SENDING MAIL TO:", user_email)

            html_body = f"""
            <html>
            <body style="font-family:Arial;padding:20px;">
                <h2 style="color:#2563eb;">Complaint Submitted Successfully</h2>

                <p>Dear <b>{name}</b>,</p>

                <p>Your complaint has been submitted successfully to the AI Complaint Management System.</p>

                <table style="border-collapse:collapse;width:100%;margin-top:20px;">
                    <tr>
                        <td><b>Complaint</b></td>
                        <td>{complaint}</td>
                    </tr>
                    <tr>
                        <td><b>Category</b></td>
                        <td>{category}</td>
                    </tr>
                    <tr>
                        <td><b>Priority</b></td>
                        <td>{priority}</td>
                    </tr>
                    <tr>
                        <td><b>AI Category</b></td>
                        <td>{ai_category}</td>
                    </tr>
                    <tr>
                        <td><b>AI Priority</b></td>
                        <td>{ai_priority}</td>
                    </tr>
                    <tr>
                        <td><b>Status</b></td>
                        <td>Pending</td>
                    </tr>
                </table>

                <br>
                <p>Our administration team will review your complaint shortly.</p>

                <br>
                <p>Regards,<br>AI Complaint Management Team</p>
            </body>
            </html>
            """

            try:
                send_email(
                    user_email,
                    "Complaint Submitted Successfully",
                    html_body
                )
                print("MAIL SENT")

            except Exception as mail_error:
                print("MAIL ERROR:", mail_error)

        return jsonify({
            "status": "success",
            "message": "Complaint submitted successfully"
        })

    except Exception as e:
        print("SUBMIT ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
# ================= GET USER COMPLAINTS =================
@app.route('/get_complaints/<name>')
def get_complaints(name):

    try:
        db, cursor = get_db()

        cursor.execute("""
            SELECT
                complaint,
                status,
                category,
                priority,
                image_path,
                video_path,
                created_at,
                ai_category,
                ai_priority,
                severity_score,
                ai_summary,
                is_duplicate,
                duplicate_of
            FROM complaints
            WHERE LOWER(name)=LOWER(%s)
            ORDER BY id DESC
        """, (name.strip(),))

        rows = cursor.fetchall()

        complaints = []

        for row in rows:
            complaints.append({
                "complaint": row[0],
                "status": row[1],
                "category": row[2],
                "priority": row[3],
                "image_path": row[4],
                "video_path": row[5],
                "created_at": str(row[6]),

                "ai_category": row[7],
                "ai_priority": row[8],
                "severity_score": row[9],
                "ai_summary": row[10],
                "is_duplicate": row[11],
                "duplicate_of": row[12]
            })

        return jsonify(complaints)

    except Exception as e:
        print("GET COMPLAINT ERROR:", e)
        return jsonify([])
# ================= UPDATE STATUS =================

@app.route('/update_status', methods=['POST'])
def update_status():

    try:

        db, cursor = get_db()

        if not session.get("admin"):

            return "unauthorized"

        data = request.json

        complaint_id = data.get('id')

        status = data.get('status')

        reason = data.get('reason', '')

        admin_message = data.get(
            'admin_message',
            ''
        )

        if not complaint_id or not status:

            return "missing_data"

        if status == "Rejected" and reason.strip() == "":

            return "reason_required"

        print("STATUS:", status)

        print("REASON:", reason)

        print("ADMIN MESSAGE:", admin_message)

        # ================= UPDATE STATUS =================

        cursor.execute("""

            UPDATE complaints

            SET status=%s

            WHERE id=%s

        """, (

            status,
            complaint_id
        ))

        db.commit()

        print("STATUS UPDATED")

        # ================= GET COMPLAINT =================

        cursor.execute("""

            SELECT

                complaint,
                name,
                identifier

            FROM complaints

            WHERE id=%s

        """, (

            complaint_id,
        ))

        complaint_data = cursor.fetchone()

        if not complaint_data:

            print("COMPLAINT NOT FOUND")

            return "updated"

        complaint_text = complaint_data[0]

        user_name = complaint_data[1]

        identifier = complaint_data[2]

        # ================= GET USER EMAIL =================

        cursor.execute("""

            SELECT email

            FROM users

            WHERE identifier=%s

        """, (

            identifier,
        ))

        email_data = cursor.fetchone()

        if not email_data:

            print("EMAIL NOT FOUND")

            return "updated"

        user_email = email_data[0]

        print("SENDING MAIL TO:", user_email)

        # ================= STATUS COLORS =================

        status_color = "#2563eb"

        status_bg = "#eff6ff"

        if status == "Accepted":

            status_color = "#2563eb"

            status_bg = "#eff6ff"

        elif status == "Resolved":

            status_color = "#16a34a"

            status_bg = "#dcfce7"

        elif status == "Rejected":

            status_color = "#dc2626"

            status_bg = "#fee2e2"

        # ================= REASON HTML =================

        reason_html = ""

        if status == "Rejected":

            reason_html = f"""

            <div
                style="
                margin-top:22px;
                padding:16px;
                background:#fee2e2;
                border-left:4px solid #dc2626;
                border-radius:10px;
                color:#991b1b;
                font-size:14px;
                line-height:1.6;
                ">

                <b>Reason for Rejection:</b>

                <br><br>

                {reason}

            </div>

            """

        # ================= ADMIN MESSAGE HTML =================

        admin_html = ""

        if admin_message.strip() != "":

            admin_html = f"""

            <div
                style="
                margin-top:22px;
                padding:16px;
                background:#dbeafe;
                border-left:4px solid #2563eb;
                border-radius:10px;
                color:#1e3a8a;
                font-size:14px;
                line-height:1.6;
                ">

                <b>Message From Administration:</b>

                <br><br>

                {admin_message}

            </div>

            """

        # ================= MAIL BODY =================

        html_body = f"""

<!DOCTYPE html>

<html>

<head>

    <meta charset="UTF-8">

</head>

<body style="margin:0; padding:0; background:#f1f5f9; font-family:Arial, Helvetica, sans-serif;">

    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9; padding:30px 0;">

        <tr>

            <td align="center">

                <table width="560" cellpadding="0" cellspacing="0"
                    style="
                    background:#ffffff;
                    border-radius:18px;
                    overflow:hidden;
                    box-shadow:0 12px 35px rgba(15,23,42,0.14);
                    border:1px solid #e2e8f0;
                    ">

                    <tr>

                        <td
                            style="
                            background:linear-gradient(135deg,#0f172a,#2563eb);
                            padding:30px;
                            text-align:center;
                            color:white;
                            ">

                            <h1 style="margin:0; font-size:26px;">

                                AI Complaint System

                            </h1>

                            <p style="margin:8px 0 0; opacity:.95;">

                                Complaint Status Notification

                            </p>

                        </td>

                    </tr>

                    <tr>

                        <td style="padding:34px 36px; color:#0f172a;">

                            <h2 style="margin:0 0 12px; font-size:23px;">

                                Complaint Status Updated

                            </h2>

                            <p style="font-size:15px; line-height:1.7; color:#475569;">

                                Dear <b>{user_name}</b>,

                                <br>

                                Your complaint status has been updated by the administration.

                            </p>

                            <div
                                style="
                                background:{status_bg};
                                color:{status_color};
                                padding:16px;
                                border-radius:12px;
                                text-align:center;
                                font-size:18px;
                                font-weight:800;
                                margin:22px 0;
                                ">

                                Current Status: {status}

                            </div>

                            <table width="100%" cellpadding="0" cellspacing="0"
                                style="
                                border-collapse:collapse;
                                margin-top:20px;
                                border:1px solid #e2e8f0;
                                ">

                                <tr>

                                    <td
                                        style="
                                        background:#f8fafc;
                                        padding:14px;
                                        font-weight:bold;
                                        width:35%;
                                        ">

                                        Complaint

                                    </td>

                                    <td style="padding:14px; color:#475569;">

                                        {complaint_text}

                                    </td>

                                </tr>

                                <tr>

                                    <td
                                        style="
                                        background:#f8fafc;
                                        padding:14px;
                                        font-weight:bold;
                                        ">

                                        Updated Status

                                    </td>

                                    <td
                                        style="
                                        padding:14px;
                                        color:{status_color};
                                        font-weight:bold;
                                        ">

                                        {status}

                                    </td>

                                </tr>

                            </table>

                            {reason_html}

                            {admin_html}

                            <p style="margin-top:24px; font-size:15px; color:#475569;">

                                Thank you for your patience and cooperation.

                            </p>

                        </td>

                    </tr>

                    <tr>

                        <td
                            style="
                            background:#f8fafc;
                            padding:20px;
                            text-align:center;
                            color:#64748b;
                            font-size:13px;
                            border-top:1px solid #e2e8f0;
                            ">

                            Regards,

                            <br>

                            <b>AI Complaint Management Team</b>

                        </td>

                    </tr>

                </table>

            </td>

        </tr>

    </table>

</body>

</html>

        """

        mail_status = send_email(

            user_email,

            f"Complaint Status Updated - {status}",

            html_body
        )

        if mail_status:

            print("MAIL SENT")

            return "updated"

        else:

            print("MAIL FAILED")

            return "updated_mail_failed"

    except Exception as e:

        print("UPDATE STATUS ERROR:", e)

        return str(e)
# ================= DELETE COMPLAINT =================

# ================= LOGOUT =================



# ================= RUN =================

if __name__ == "__main__":

    app.run(

        debug=True,
        host="0.0.0.0",
        port=5000
    )
