import os
import uuid
import secrets
import string
from datetime import datetime

from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    current_app
)

from werkzeug.utils import secure_filename

# Ensure your models match these exactly in models.py
from models import (
    db,
    User,
    LostItem,
    FoundItem,
    Claim
)

user = Blueprint("user", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def logged_in():
    return "user_id" in session

def generate_pickup_code():
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))

# ==========================================================
# FIXED: My Activity & Statistics Counts
# ==========================================================
@user.route("/api/my-activity", methods=["GET"])
def my_activity():
    if not logged_in():
        return jsonify({"success": False, "message": "Login Required"}), 401

    uid = session["user_id"]

    try:
        # Fetch individual records to build statistics counts for dashboard cards
        lost_items = LostItem.query.filter_by(user_id=uid).all()
        found_items = FoundItem.query.filter_by(user_id=uid).all()
        claims_submitted = Claim.query.filter_by(user_id=uid).all()

        lost_reports = []
        found_reports = []
        activity = []

        for item in lost_items:
            report = {
                "id": item.id,
                "type": "Lost",
                "item_name": item.item_name,
                "category": item.category,
                "location": item.location,
                "status": item.status,
                "date": item.date_lost.strftime("%d-%m-%Y") if item.date_lost else "",
                "sort_date": item.created_at.isoformat() if item.created_at else ""
            }
            lost_reports.append(report)
            activity.append(report)

        for item in found_items:
            report = {
                "id": item.id,
                "type": "Found",
                "item_name": item.item_name,
                "category": item.category,
                "location": item.location,
                "status": item.status,
                "deposit_code": item.deposit_code or "",
                "date": item.date_found.strftime("%d-%m-%Y") if item.date_found else "",
                "sort_date": item.created_at.isoformat() if item.created_at else ""
            }
            found_reports.append(report)
            activity.append(report)

        activity.sort(key=lambda x: x["sort_date"], reverse=True)

        # Retaining your structural activity output while including requested counters
        return jsonify({
            "success": True,
            "lost_count": len(lost_items),
            "found_count": len(found_items),
            "claim_count": len(claims_submitted),
            "lost_reports": lost_reports,
            "found_reports": found_reports,
            "activity": activity[:10]
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==========================================================
# MISSING API ROUTE ADDED: My Claims Table
# ==========================================================
@user.route("/api/my-claims", methods=["GET"])
def my_claims():
    if not logged_in():
        return jsonify({"success": False, "message": "Login Required"}), 401

    try:
        uid = session["user_id"]
        user_claims = Claim.query.filter_by(user_id=uid).all()
        
        data = []
        updated_pickup_codes = False
        for claim in user_claims:
            if claim.status == "Approved" and not claim.pickup_code:
                claim.pickup_code = generate_pickup_code()
                updated_pickup_codes = True

            # Safely verify if relation model parameters link successfully
            item_name = claim.found_item.item_name if claim.found_item else "Unknown Item"
            category = claim.found_item.category if claim.found_item else "N/A"
            
            data.append({
                "item_name": item_name,
                "category": category,
                "owner": "Campus Hub Admin",
                "date": claim.created_at.strftime("%d-%m-%Y") if claim.created_at else "",
                "status": claim.status if claim.status else "Pending",
                "pickup_code": claim.pickup_code or "",
                "instruction": (
                    "Your claim is approved. Collect your item from the hub and share this code with the hub admin."
                    if claim.status == "Approved" and claim.pickup_code
                    else ""
                ),
                "message": claim.message if claim.message else "No message attached."
            })
        if updated_pickup_codes:
            db.session.commit()
        return jsonify(data)
    except Exception as e:
        return jsonify([])

# ==========================================================
# MISSING API ROUTE ADDED: My Reports Table
# ==========================================================
@user.route("/api/my-reports", methods=["GET"])
def my_reports():
    if not logged_in():
        return jsonify({"success": False, "message": "Login Required"}), 401

    try:
        uid = session["user_id"]
        lost_items = LostItem.query.filter_by(user_id=uid).all()
        found_items = FoundItem.query.filter_by(user_id=uid).all()

        reports = []
        for item in lost_items:
            reports.append({
                "type": "Lost",
                "item_name": item.item_name,
                "category": item.category,
                "location": item.location,
                "date": item.date_lost.strftime("%d-%m-%Y") if item.date_lost else "",
                "status": item.status
            })

        for item in found_items:
            reports.append({
                "type": "Found",
                "item_name": item.item_name,
                "category": item.category,
                "location": item.location,
                "date": item.date_found.strftime("%d-%m-%Y") if item.date_found else "",
                "status": item.status,
                "deposit_code": item.deposit_code or ""
            })

        return jsonify(reports)
    except Exception as e:
        return jsonify([])

# ==========================================================
# FILE UPLOAD UTILITY
# ==========================================================
def upload_image(file):
    if file is None or file.filename == "":
        return None
    if not allowed_file(file.filename):
        raise Exception("Invalid image format.")
    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1]
    new_filename = f"{uuid.uuid4()}.{extension}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, new_filename)
    file.save(save_path)
    return new_filename

# ==========================================================
# SEARCH FOUND ITEMS
# ==========================================================
@user.route("/api/search/assets", methods=["GET"])
def search_assets():
    if not logged_in():
        return jsonify({"success": False, "message": "Login Required"}), 401

    item_type = request.args.get("type", "found").lower()
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    if item_type != "found":
        return jsonify([])

    items_query = FoundItem.query.filter_by(status="Available")

    if query:
        items_query = items_query.filter(
            FoundItem.item_name.ilike(f"%{query}%")
        )

    if category:
        items_query = items_query.filter(
            FoundItem.category.ilike(f"%{category}%")
        )

    items = items_query.order_by(
        FoundItem.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "description": item.description,
            "location": item.location,
            "date": item.date_found.strftime("%d-%m-%Y") if item.date_found else "",
            "status": item.status,
            "image": item.image
        }
        for item in items
    ])

# ==========================================================
# SUBMIT CLAIM API ROUTE
# ==========================================================
@user.route("/api/claims/submit", methods=["POST"])
def submit_claim():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Login Required"
        }), 401

    try:
        found_item_id = request.form.get("item_id")
        message = request.form.get("claim_reason", "").strip()

        if not found_item_id or not message:
            return jsonify({
                "success": False,
                "message": "Item and claim reason are required."
            }), 400

        found_item = FoundItem.query.get(found_item_id)

        if found_item is None:
            return jsonify({
                "success": False,
                "message": "Found item not found."
            }), 404

        proof = ""
        if "proof_document" in request.files:
            file = request.files["proof_document"]
            if file.filename != "":
                proof = upload_image(file)

        claim = Claim(
            user_id=session["user_id"],
            found_item_id=found_item.id,
            message=message,
            proof=proof,
            status="Pending"
        )

        found_item.status = "Claimed"

        db.session.add(claim)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Claim submitted successfully."
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ==========================================================
# REPORT LOST ITEM
# ==========================================================
@user.route("/api/reports/lost", methods=["POST"])
def report_lost():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login Required"}), 401
    try:
        image = ""
        if "item_image" in request.files:
            file = request.files["item_image"]
            if file.filename != "":
                image = upload_image(file)
        report = LostItem(
            user_id=session["user_id"],
            item_name=request.form["item_name"],
            category=request.form["category"],
            description=request.form["description"],
            location=request.form["location"],
            date_lost=datetime.now().date(),
            image=image,
            status="Pending"
        )
        db.session.add(report)
        db.session.commit()
        return jsonify({"success": True, "message": "Lost Item Submitted Successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    
# ==========================================================
# REPORT FOUND ITEM
# ==========================================================

@user.route("/api/reports/found", methods=["POST"])
def report_found():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login Required"}), 401
    try:
        image = ""
        if "item_image" in request.files:
            file = request.files["item_image"]
            if file.filename != "":
                image = upload_image(file)
        deposit_code = generate_pickup_code()
        report = FoundItem(
            user_id=session["user_id"],
            item_name=request.form["item_name"],
            category=request.form["category"],
            description=request.form["description"],
            location=request.form["location"],
            date_found=datetime.now().date(),
            image=image,
            deposit_code=deposit_code,
            status="Pending Deposit"
        )
        db.session.add(report)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": (
                "Found item submitted. Deposit it at the hub and share this "
                f"deposit code with admin: {deposit_code}"
            ),
            "deposit_code": deposit_code
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500