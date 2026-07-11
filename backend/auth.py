from flask import Blueprint, request, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

auth = Blueprint("auth", __name__)

# ==========================================================
# REGISTER
# ==========================================================

@auth.route("/api/register", methods=["POST"])
def register():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone") or request.form.get("mobile_number", "").strip()
    roll_number = request.form.get("roll_number", "").strip()
    department = (
        request.form.get("department")
        or request.form.get("class_stream")
        or "Not specified"
    ).strip()
    year = request.form.get("year", "Not specified").strip() or "Not specified"
    password = request.form.get("password", "")

    if not all([name, email, phone, roll_number, password]):
        return jsonify({
            "success": False,
            "message": "Please fill in all required fields."
        }), 400

    # Check existing email
    if User.query.filter_by(email=email).first():
        return jsonify({
            "success": False,
            "message": "Email already registered."
        }), 400

    # Check existing roll number
    if User.query.filter_by(roll_number=roll_number).first():
        return jsonify({
            "success": False,
            "message": "Roll Number already exists."
        }), 400

    user = User(
        name=name,
        email=email,
        phone=phone,
        roll_number=roll_number,
        department=department,
        year=year,
        password=generate_password_hash(password),
        is_admin=False
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Registration successful. You can now log in."
    })

# ==========================================================
# LOGIN
# ==========================================================

@auth.route("/api/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and Password required."
        }), 400

    user = User.query.filter_by(
        email=email
    ).first()

    if user is None:
        return jsonify({
            "success": False,
            "message": "Invalid Email"
        }), 401
    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "Your account has been deactivated. Please contact admin."
        }), 403
    if not check_password_hash(
            user.password,
            password
    ):
        return jsonify({
            "success": False,
            "message": "Incorrect Password"
        }), 401
    # Create Session
    session["user_id"] = user.id
    session["name"] = user.name
    session["email"] = user.email
    session["is_admin"] = user.is_admin

    if user.is_admin:
        redirect_url = url_for("admin_dashboard")
    else:
        redirect_url = url_for("dashboard")
    return jsonify({
        "success": True,
        "message": "Login Successful",
        "redirect": redirect_url
    })

# ==========================================================
# LOGOUT
# ==========================================================

@auth.route("/api/logout")
def logout():
    session.clear()
    return jsonify({
        "success": True,
        "message": "Logged Out"
    })

# ==========================================================
# CURRENT USER
# ==========================================================

@auth.route("/api/user")
def current_user():
    if "user_id" not in session:
        return jsonify({
            "logged_in": False
        })
    return jsonify({
        "logged_in": True,
        "id": session["user_id"],
        "name": session["name"],
        "email": session["email"],
        "is_admin": session["is_admin"]
    })