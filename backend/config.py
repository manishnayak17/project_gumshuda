import os

class Config:
    SECRET_KEY = "gumshuda@2026"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Rahul@localhost/gumshuda"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024