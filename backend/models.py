from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ==========================================================
# USER MODEL
# ==========================================================

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relationships
    lost_items = db.relationship(
        "LostItem",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )

    found_items = db.relationship(
        "FoundItem",
        backref="finder",
        lazy=True,
        cascade="all, delete-orphan"
    )

    claims = db.relationship(
        "Claim",
        backref="claimer",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.name}>"



# ==========================================================
# LOST ITEM MODEL
# ==========================================================
class LostItem(db.Model):
    __tablename__ = "lost_items"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    item_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date_lost = db.Column(
        db.Date,
        nullable=False
    )
    image = db.Column(db.String(255))
    status = db.Column(
        db.String(50),
        default="Pending"
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<LostItem {self.item_name}>"

# ==========================================================
# FOUND ITEM MODEL
# ==========================================================

class FoundItem(db.Model):
    __tablename__ = "found_items"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    item_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date_found = db.Column(
        db.Date,
        nullable=False
    )
    image = db.Column(db.String(255))
    deposit_code = db.Column(db.String(20))
    status = db.Column(
        db.String(50),
        default="Pending Deposit"
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    claims = db.relationship(
        "Claim",
        backref="found_item",
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<FoundItem {self.item_name}>"

# ==========================================================
# CLAIM MODEL
# ==========================================================

class Claim(db.Model):
    __tablename__ = "claims"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    found_item_id = db.Column(
        db.Integer,
        db.ForeignKey("found_items.id"),
        nullable=False
    )
    message = db.Column(
        db.Text,
        nullable=False
    )
    proof = db.Column(db.String(255))
    pickup_code = db.Column(db.String(20))
    status = db.Column(
        db.String(50),
        default="Pending"
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    def __repr__(self):
        return f"<Claim {self.id}>"