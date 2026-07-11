import os
from functools import wraps

from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    session,
    url_for
)

from werkzeug.security import generate_password_hash

from config import Config
from database import initialize_database
from models import (
    db,
    User,
    LostItem,
    FoundItem,
    Claim
)

# Blueprints
from auth import auth
from user_routes import logged_in, user
from admin_routes import admin


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

app = Flask(__name__)
app.config.from_object(Config)

initialize_database(app)

# ==========================================================
# CREATE UPLOAD DIRECTORY
# ==========================================================

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)

# ==========================================================
# CREATE DEFAULT ADMIN
# ==========================================================
with app.app_context():

    admin_user = User.query.filter_by(
        email="admin@gumshuda.com"
    ).first()

    if admin_user is None:
        admin_user = User(
            name="Administrator",
            email="admin@gumshuda.com",
            phone="0000000000",
            roll_number="ADMIN001",
            department="Administration",
            year="Staff",
            password=generate_password_hash("admin123"),
            is_admin=True
        )

        db.session.add(admin_user)
        db.session.commit()

        print("Default Admin Created")
    else:
        print("Admin Already Exists")

# ==========================================================
# REGISTER BLUEPRINTS
# ==========================================================
app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(admin)

# ==========================================================
# LOGIN DECORATOR
# ==========================================================
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return func(*args, **kwargs)
    return wrapper

# ==========================================================
# ADMIN DECORATOR
# ==========================================================
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        user = User.query.get(
            session["user_id"]
        )
        if user is None:
            session.clear()
            return redirect(
                url_for("login_page")
            )
        if not user.is_admin:
            return redirect(
                url_for("dashboard")
            )
        return func(*args, **kwargs)
    return wrapper

# ==========================================================
# WEBSITE PAGES
# ==========================================================
@app.route("/")
def home():
    return render_template("Index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get(
        session["user_id"]
    )
    return render_template(
        "dashboard.html",
        user=user
    )

from models import User, LostItem, FoundItem, Claim

@app.route("/admin")
@admin_required
def admin_dashboard():

    metrics = {
        "users": User.query.count(),
        "lost_items": LostItem.query.count(),
        "pending_claims": Claim.query.filter_by(status="Pending").count(),
        "approved_claims": Claim.query.filter_by(status="Approved").count()
    }

    lost_items = LostItem.query.order_by(
        LostItem.created_at.desc()
    ).all()

    found_items = FoundItem.query.order_by(
        FoundItem.created_at.desc()
    ).all()

    claims = Claim.query.filter(
        Claim.status.in_(["Pending", "Approved"])
    ).order_by(
        Claim.created_at.desc()
    ).all()

    completed_claims = Claim.query.filter(
        Claim.status.in_(["Completed", "Rejected"])
    ).order_by(
        Claim.created_at.desc()
    ).all()

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",
        metrics=metrics,
        lost_items=lost_items,
        found_items=found_items,
        claims=claims,
        completed_claims=completed_claims,
        users=users
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        url_for("home")
    )

# ==========================================================
# ERROR PAGES
# ==========================================================
@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "404.html"
    ), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template(
        "500.html"
    ), 500


# for rule in app.url_map.iter_rules():
#     print(rule)



# ==========================================================
# RUN SERVER
# ==========================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )