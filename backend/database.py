from models import db
from sqlalchemy import inspect, text

def initialize_database(app):

    db.init_app(app)
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        user_columns = [
            column["name"]
            for column in inspector.get_columns("users")
        ]

        if "is_active" not in user_columns:
            db.session.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"
                )
            )
            db.session.commit()

        claim_columns = [
            column["name"]
            for column in inspector.get_columns("claims")
        ]

        if "pickup_code" not in claim_columns:
            db.session.execute(
                text(
                    "ALTER TABLE claims "
                    "ADD COLUMN pickup_code VARCHAR(20)"
                )
            )
            db.session.commit()

        found_item_columns = [
            column["name"]
            for column in inspector.get_columns("found_items")
        ]

        if "deposit_code" not in found_item_columns:
            db.session.execute(
                text(
                    "ALTER TABLE found_items "
                    "ADD COLUMN deposit_code VARCHAR(20)"
                )
            )
            db.session.commit()

        print("=" * 50)
        print("Database initialized successfully.")
        print("=" * 50)