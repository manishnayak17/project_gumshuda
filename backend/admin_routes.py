from functools import wraps
import secrets
import string
from flask import render_template

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session
)

from models import (
    db,
    User,
    LostItem,
    FoundItem,
    Claim
)

import csv
from io import StringIO
from flask import Response
from flask import Blueprint, jsonify
from models import User, LostItem, FoundItem, Claim



# ==========================================================
# ADMIN BLUEPRINT
# ==========================================================

admin = Blueprint("admin", __name__)

def generate_pickup_code():
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))

# ==========================================================
# ADMIN AUTHENTICATION DECORATOR
# ==========================================================

def admin_required(func):
    """
    Ensures that only logged-in administrators
    can access admin routes.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        # User not logged in
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401

        # Fetch logged in user
        user = User.query.get(session["user_id"])

        # Invalid session
        if user is None:
            session.clear()
            return jsonify({
                "success": False,
                "message": "Invalid session."
            }), 401

        # Not an admin
        if not user.is_admin:
            return jsonify({
                "success": False,
                "message": "Access denied."
            }), 403

        return func(*args, **kwargs)

    return wrapper

# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@admin.route("/api/admin/dashboard")
@admin_required
def admin_dashboard():
    """
    Load Admin Dashboard with all required data.
    """
    # Dashboard Metrics
    metrics = {
        "users": User.query.count(),
        "lost_items": LostItem.query.count(),
        "found_items": FoundItem.query.count(),
        "pending_claims": Claim.query.filter_by(status="Pending").count(),
        "approved_claims": Claim.query.filter_by(status="Approved").count()
    }
    # Fetch Data
    users = User.query.order_by(User.created_at.desc()).all()
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
    return render_template(
        "admin_dashboard.html",
        metrics=metrics,
        users=users,
        lost_items=lost_items,
        found_items=found_items,
        claims=claims,
        completed_claims=completed_claims
    )

# ==========================================================
# DASHBOARD METRICS API
# ==========================================================

@admin.route("/api/admin/dashboard-metrics", methods=["GET"])
def dashboard_metrics():

    metrics = {
        "users": User.query.count(),
        "lost_items": LostItem.query.count(),
        "found_items": FoundItem.query.count(),
        "pending_claims": Claim.query.filter_by(status="Pending").count(),
        "approved_claims": Claim.query.filter_by(status="Approved").count()
    }

    return jsonify(metrics)

# ==========================================================
# GET ALL LOST ITEMS
# ==========================================================

@admin.route("/api/admin/lost-items", methods=["GET"])
@admin_required
def get_lost_items():

    items = LostItem.query.order_by(
        LostItem.created_at.desc()
    ).all()

    data = []

    for item in items:

        data.append({
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "description": item.description,
            "location": item.location,
            "date_lost": str(item.date_lost),
            "status": item.status,
            "image": item.image,
            "image_url": f"/static/uploads/{item.image}" if item.image else "",
            "owner": item.owner.name,
            "created_at": item.created_at.strftime("%d-%m-%Y %H:%M")
        })

    return jsonify({
        "success": True,
        "items": data
    })

# ==========================================================
# SEARCH LOST ITEMS
# ==========================================================

@admin.route("/api/admin/search-lost", methods=["GET"])
@admin_required
def search_lost():

    query = request.args.get("q", "")

    items = LostItem.query.filter(
        LostItem.item_name.ilike(f"%{query}%")
    ).all()

    result = []

    for item in items:

        result.append({

            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "location": item.location,
            "status": item.status,
            "image": item.image,
            "image_url": f"/static/uploads/{item.image}" if item.image else "",
            "owner": item.owner.name

        })

    return jsonify(result)

# ==========================================================
# ARCHIVE LOST ITEM
# ==========================================================

@admin.route("/api/admin/lost-items/<int:item_id>/archive", methods=["PUT"])
@admin_required
def archive_lost_item(item_id):
    item = LostItem.query.get(item_id)
    if item is None:
        return jsonify({
            "success": False,
            "message": "Lost item not found."
        }), 404
    item.status = "Archived"
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Lost item archived successfully."
    })

# ==========================================================
# DELETE LOST ITEM
# ==========================================================

@admin.route("/api/admin/lost-items/<int:item_id>", methods=["DELETE"])
@admin_required
def delete_lost_item(item_id):
    item = LostItem.query.get(item_id)
    if item is None:
        return jsonify({
            "success": False,
            "message": "Lost item not found."
        }), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Lost item deleted successfully."
    })

# ==========================================================
# GET ALL FOUND ITEMS
# ==========================================================

@admin.route("/api/admin/found-items", methods=["GET"])
@admin_required
def get_found_items():
    items = FoundItem.query.order_by(
        FoundItem.created_at.desc()
    ).all()
    data = []
    for item in items:
        data.append({
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "description": item.description,
            "location": item.location,
            "date_found": str(item.date_found),
            "status": item.status,
            "image": item.image,
            "image_url": f"/static/uploads/{item.image}" if item.image else "",
            "finder": item.finder.name,
            "created_at": item.created_at.strftime("%d-%m-%Y %H:%M")
        })
    return jsonify({
        "success": True,
        "items": data
    })

# ==========================================================
# SEARCH FOUND ITEMS
# ==========================================================

@admin.route("/api/admin/search-found", methods=["GET"])
@admin_required
def search_found():

    query = request.args.get("q", "")

    items = FoundItem.query.filter(
        FoundItem.item_name.ilike(f"%{query}%")
    ).all()

    data = []

    for item in items:

        data.append({

            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "location": item.location,
            "status": item.status,
            "image": item.image,
            "image_url": f"/static/uploads/{item.image}" if item.image else "",
            "owner": item.finder.name

        })

    return jsonify(data)

# ==========================================================
# VERIFY FOUND ITEM DEPOSIT
# ==========================================================

@admin.route("/api/admin/found-items/<int:item_id>/receive", methods=["PUT"])
@admin_required
def receive_found_item(item_id):
    item = FoundItem.query.get(item_id)
    if item is None:
        return jsonify({
            "success": False,
            "message": "Found item not found."
        }), 404

    code = (request.json or {}).get("deposit_code", "").strip().upper()

    if item.status != "Pending Deposit":
        return jsonify({
            "success": False,
            "message": "Only pending deposit items can be received."
        }), 400

    if not item.deposit_code or code != item.deposit_code:
        return jsonify({
            "success": False,
            "message": "Invalid deposit code."
        }), 400

    item.status = "Available"
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Found item received at hub and is now available in search."
    })

# ==========================================================
# DELETE FOUND ITEM
# ==========================================================

@admin.route("/api/admin/delete-found/<int:item_id>", methods=["DELETE"])
@admin_required
def delete_found(item_id):

    item = FoundItem.query.get(item_id)

    if not item:
        return jsonify({
            "success": False,
            "message": "Item not found"
        }), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Found report deleted successfully"
    })

# ==========================================================
# GET ALL CLAIMS
# ==========================================================

@admin.route("/api/admin/claims", methods=["GET"])
@admin_required
def get_claims():
    claims = Claim.query.filter(
        Claim.status.in_(["Pending", "Approved"])
    ).order_by(
        Claim.created_at.desc()
    ).all()
    updated_pickup_codes = False
    data = []
    for claim in claims:
        if claim.status == "Approved" and not claim.pickup_code:
            claim.pickup_code = generate_pickup_code()
            updated_pickup_codes = True

        data.append({
            "id": claim.id,
            "claimer": claim.claimer.name,
            "email": claim.claimer.email,
            "phone": claim.claimer.phone,
            "item_id": claim.found_item.id,
            "item_name": claim.found_item.item_name,
            "category": claim.found_item.category,
            "message": claim.message,
            "proof": claim.proof,
            "status": claim.status,
            "created_at": claim.created_at.strftime("%d-%m-%Y %H:%M")
        })
    if updated_pickup_codes:
        db.session.commit()
    return jsonify({
        "success": True,
        "claims": data
    })

# ==========================================================
# GET CLAIM DETAILS
# ==========================================================

@admin.route("/api/admin/claims/<int:claim_id>/details", methods=["GET"])
@admin_required
def get_claim_details(claim_id):
    claim = Claim.query.get(claim_id)
    if claim is None:
        return jsonify({
            "success": False,
            "message": "Claim not found."
        }), 404

    found_item = claim.found_item
    claimer = claim.claimer
    finder = found_item.finder if found_item else None

    if found_item is None:
        return jsonify({
            "success": False,
            "message": "Linked found item no longer exists."
        }), 404

    if claim.status == "Approved" and not claim.pickup_code:
        claim.pickup_code = generate_pickup_code()
        db.session.commit()

    return jsonify({
        "success": True,
        "claim": {
            "id": claim.id,
            "message": claim.message,
            "proof": claim.proof,
            "proof_url": f"/static/uploads/{claim.proof}" if claim.proof else "",
            "status": claim.status,
            "created_at": claim.created_at.strftime("%d-%m-%Y %H:%M")
        },
        "claimer": {
            "name": claimer.name,
            "email": claimer.email,
            "phone": claimer.phone,
            "roll_number": claimer.roll_number,
            "department": claimer.department,
            "year": claimer.year
        },
        "item": {
            "id": found_item.id,
            "item_name": found_item.item_name,
            "category": found_item.category,
            "description": found_item.description,
            "location": found_item.location,
            "date_found": str(found_item.date_found),
            "status": found_item.status,
            "image": found_item.image,
            "image_url": f"/static/uploads/{found_item.image}" if found_item.image else ""
        },
        "finder": {
            "name": finder.name if finder else "",
            "email": finder.email if finder else "",
            "phone": finder.phone if finder else "",
            "roll_number": finder.roll_number if finder else ""
        }
    })

# ==========================================================
# APPROVE CLAIM
# ==========================================================

@admin.route("/api/admin/claims/<int:claim_id>/approve", methods=["PUT"])
@admin_required
def approve_claim(claim_id):
    claim = Claim.query.get(claim_id)
    if claim is None:
        return jsonify({
            "success": False,
            "message": "Claim not found."
        }), 404
    if claim.status == "Rejected":
        return jsonify({
            "success": False,
            "message": "Rejected claim cannot be approved."
        }), 400
    if claim.status == "Completed":
        return jsonify({
            "success": False,
            "message": "Completed claim is already handed over."
        }), 400
    if not claim.pickup_code:
        claim.pickup_code = generate_pickup_code()
    claim.status = "Approved"
    claim.found_item.status = "Claimed"
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Claim approved. The pickup code is now visible to the user."
    })

# ==========================================================
# COMPLETE CLAIM HANDOVER
# ==========================================================

@admin.route("/api/admin/claims/<int:claim_id>/complete", methods=["PUT"])
@admin_required
def complete_claim(claim_id):
    claim = Claim.query.get(claim_id)
    if claim is None:
        return jsonify({
            "success": False,
            "message": "Claim not found."
        }), 404

    code = (request.json or {}).get("pickup_code", "").strip().upper()

    if claim.status != "Approved":
        return jsonify({
            "success": False,
            "message": "Only approved claims can be completed."
        }), 400

    if not claim.pickup_code or code != claim.pickup_code:
        return jsonify({
            "success": False,
            "message": "Invalid pickup code."
        }), 400

    claim.status = "Completed"
    claim.found_item.status = "Collected"
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Handover completed. Item marked as collected."
    })

# ==========================================================
# REJECT CLAIM
# ==========================================================

@admin.route("/api/admin/claims/<int:claim_id>/reject", methods=["PUT"])
@admin_required
def reject_claim(claim_id):
    claim = Claim.query.get(claim_id)
    if claim is None:
        return jsonify({
            "success": False,
            "message": "Claim not found."
        }), 404
    if claim.status == "Completed":
        return jsonify({
            "success": False,
            "message": "Completed claim cannot be rejected."
        }), 400
    claim.status = "Rejected"
    claim.found_item.status = "Available"
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Claim rejected."
    })

# ==========================================================
# DELETE CLAIM
# ==========================================================

@admin.route("/api/admin/claims/<int:claim_id>", methods=["DELETE"])
@admin_required
def delete_claim(claim_id):
    claim = Claim.query.get(claim_id)
    if claim is None:
        return jsonify({
            "success": False,
            "message": "Claim not found."
        }), 404
    db.session.delete(claim)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Claim deleted successfully."
    })

# ==========================================================
# GET ALL USERS
# ==========================================================

@admin.route("/api/admin/users", methods=["GET"])
@admin_required
def get_users():
    users = User.query.order_by(
        User.created_at.desc()
    ).all()
    data = []
    for user in users:
        data.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "roll_number": user.roll_number,
            "department": user.department,
            "year": user.year,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "created_at": user.created_at.strftime("%d-%m-%Y %H:%M")
        })
    return jsonify({
        "success": True,
        "users": data
    })

# ==========================================================
# SEARCH USERS
# ==========================================================

@admin.route("/api/admin/users/search")
@admin_required
def search_users():
    keyword = request.args.get("q", "")
    users = User.query.filter(
        User.name.ilike(f"%{keyword}%")
    ).all()
    data = []
    for user in users:
        data.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "department": user.department,
            "year": user.year,
            "is_admin": user.is_admin,
            "is_active": user.is_active
        })
    return jsonify({
        "success": True,
        "users": data
    })

# ==========================================================
# DELETE USER
# ==========================================================

@admin.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404
    if user.is_admin:
        return jsonify({
            "success": False,
            "message": "Admin account cannot be deleted."
        }), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "User deleted successfully."
    })

# ==========================================================
# DEACTIVATE USER
# ==========================================================

@admin.route("/api/admin/users/<int:user_id>/deactivate", methods=["PUT"])
@admin_required
def deactivate_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404
    if user.is_admin:
        return jsonify({
            "success": False,
            "message": "Admin account cannot be deactivated."
        }), 400
    user.is_active = False
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "User deactivated successfully."
    })

# ==========================================================
# ACTIVATE USER
# ==========================================================

@admin.route("/api/admin/users/<int:user_id>/activate", methods=["PUT"])
@admin_required
def activate_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404
    user.is_active = True
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "User activated successfully."
    })

# ==========================================================
# MAKE ADMIN
# ==========================================================

@admin.route("/api/admin/users/<int:user_id>/make-admin", methods=["PUT"])
@admin_required
def make_admin(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404
    user.is_admin = True
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "User promoted to Admin."
    })

# ==========================================================
# REMOVE ADMIN
# ==========================================================

@admin.route("/api/admin/users/<int:user_id>/remove-admin", methods=["PUT"])
@admin_required
def remove_admin(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404
    if user.email == "admin@gumshuda.com":
        return jsonify({
            "success": False,
            "message": "Default Admin cannot be modified."
        }), 400
    user.is_admin = False
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Admin access removed."
    })

# ==========================================================
# DASHBOARD SUMMARY
# ==========================================================

@admin.route("/api/admin/dashboard-summary", methods=["GET"])
@admin_required
def dashboard_summary():
    summary = {
        "users": User.query.count(),
        "lost_items": LostItem.query.count(),
        "found_items": FoundItem.query.count(),
        "claims": Claim.query.count(),
        "pending_claims":
            Claim.query.filter_by(
                status="Pending"
            ).count(),
        "approved_claims":
            Claim.query.filter_by(
                status="Approved"
            ).count(),
        "completed_claims":
            Claim.query.filter_by(
                status="Completed"
            ).count(),
        "rejected_claims":
            Claim.query.filter_by(
                status="Rejected"
            ).count()
    }
    return jsonify({
        "success": True,
        "summary": summary
    })

# ==========================================================
# RECENT ACTIVITIES
# ==========================================================

@admin.route("/api/admin/recent-activities")
@admin_required
def recent_activities():
    activities = []
    lost = LostItem.query.order_by(
        LostItem.created_at.desc()
    ).limit(5).all()
    for item in lost:
        activities.append({
            "type": "Lost Item",
            "title": item.item_name,
            "user": item.owner.name,
            "time": item.created_at.strftime("%d-%m-%Y %H:%M")
        })
    found = FoundItem.query.order_by(
        FoundItem.created_at.desc()
    ).limit(5).all()
    for item in found:
        activities.append({
            "type": "Found Item",
            "title": item.item_name,
            "user": item.finder.name,
            "time": item.created_at.strftime("%d-%m-%Y %H:%M")
        })
    activities.sort(
        key=lambda x: x["time"],
        reverse=True
    )
    return jsonify({
        "success": True,
        "activities": activities[:10]
    })

# ==========================================================
# CATEGORY ANALYTICS
# ==========================================================

@admin.route("/api/admin/category-stats")
@admin_required
def category_stats():
    categories = {}
    items = LostItem.query.all()
    for item in items:
        if item.category not in categories:
            categories[item.category] = 0
        categories[item.category] += 1
    return jsonify({
        "success": True,
        "categories": categories
    })

# ==========================================================
# LOST ITEM STATUS
# ==========================================================

@admin.route("/api/admin/lost-status")
@admin_required
def lost_status():
    data = {
        "Pending":
            LostItem.query.filter_by(
                status="Pending"
            ).count(),
        "Found":
            LostItem.query.filter_by(
                status="Found"
            ).count(),
        "Archived":
            LostItem.query.filter_by(
                status="Archived"
            ).count()
    }
    return jsonify({
        "success": True,
        "status": data
    })

# ==========================================================
# FOUND ITEM STATUS
# ==========================================================

@admin.route("/api/admin/found-status")
@admin_required
def found_status():
    data = {
        "Available":
            FoundItem.query.filter_by(
                status="Available"
            ).count(),
        "Claimed":
            FoundItem.query.filter_by(
                status="Claimed"
            ).count(),
        "Collected":
            FoundItem.query.filter_by(
                status="Collected"
            ).count()
    }
    return jsonify({
        "success": True,
        "status": data
    })

# ==========================================================
# CLAIM STATUS
# ==========================================================

@admin.route("/api/admin/claim-status")
@admin_required
def claim_status():
    data = {
        "Pending":
            Claim.query.filter_by(
                status="Pending"
            ).count(),
        "Approved":
            Claim.query.filter_by(
                status="Approved"
            ).count(),
        "Rejected":
            Claim.query.filter_by(
                status="Rejected"
            ).count(),
        "Completed":
            Claim.query.filter_by(
                status="Completed"
            ).count()
    }
    return jsonify({
        "success": True,
        "status": data
    })

# ==========================================================
# EXPORT USERS CSV
# ==========================================================

@admin.route("/api/admin/export/users")
@admin_required
def export_users():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID",
        "Name",
        "Email",
        "Phone",
        "Department",
        "Year",
        "Role"
    ])
    users = User.query.all()
    for user in users:
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.phone,
            user.department,
            user.year,
            "Admin" if user.is_admin else "User"
        ])
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=users.csv"
        }
    )

# ==========================================================
# EXPORT LOST ITEMS
# ==========================================================

@admin.route("/api/admin/export/lost")
@admin_required
def export_lost():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Item",
        "Category",
        "Owner",
        "Status",
        "Location"
    ])
    for item in LostItem.query.all():
        writer.writerow([
            item.item_name,
            item.category,
            item.owner.name,
            item.status,
            item.location
        ])
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=lost_items.csv"
        }
    )

# ==========================================================
# EXPORT FOUND ITEMS
# ==========================================================

@admin.route("/api/admin/export/found")
@admin_required
def export_found():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Item",
        "Category",
        "Finder",
        "Status",
        "Location"
    ])
    for item in FoundItem.query.all():
        writer.writerow([
            item.item_name,
            item.category,
            item.finder.name,
            item.status,
            item.location
        ])
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=found_items.csv"
        }
    )

# ==========================================================
# GLOBAL SEARCH
# ==========================================================

@admin.route("/api/admin/search")
@admin_required
def global_search():
    keyword = request.args.get("q", "")
    lost = LostItem.query.filter(
        LostItem.item_name.ilike(f"%{keyword}%")
    ).all()
    found = FoundItem.query.filter(
        FoundItem.item_name.ilike(f"%{keyword}%")
    ).all()
    users = User.query.filter(
        User.name.ilike(f"%{keyword}%")
    ).all()
    return jsonify({
        "success": True,
        "lost_items": len(lost),
        "found_items": len(found),
        "users": len(users)
    })

# ==========================================================
# ADMIN PROFILE
# ==========================================================

@admin.route("/api/admin/profile")
@admin_required
def admin_profile():
    admin_user = User.query.get(session["user_id"])
    return jsonify({
        "success": True,
        "profile": {
            "name": admin_user.name,
            "email": admin_user.email,
            "phone": admin_user.phone,
            "department": admin_user.department,
            "year": admin_user.year
        }
    })

# ==========================================================
# REFRESH DASHBOARD
# ==========================================================

@admin.route("/api/admin/refresh")
@admin_required
def refresh_dashboard():
    return jsonify({
        "success": True,
        "message": "Dashboard refreshed."
    })


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def serialize_lost(item):
    return {
        "id": item.id,
        "item_name": item.item_name,
        "category": item.category,
        "description": item.description,
        "location": item.location,
        "date_lost": str(item.date_lost),
        "status": item.status,
        "owner": item.owner.name,
        "email": item.owner.email,
        "phone": item.owner.phone
    }


def serialize_found(item):
    return {
        "id": item.id,
        "item_name": item.item_name,
        "category": item.category,
        "description": item.description,
        "location": item.location,
        "date_found": str(item.date_found),
        "status": item.status,
        "owner": item.finder.name,
        "email": item.finder.email,
        "phone": item.finder.phone
    }