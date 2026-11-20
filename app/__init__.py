"""
Flask Application Factory with PostgreSQL Connection
"""

import os
from flask import Flask
from dotenv import load_dotenv
from app.models import db

# Load environment variables from .env file if present
load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "simul-secret-key-2026")

    # PostgreSQL Database URL
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Defaults to local PostgreSQL on port 5432 with database cbs_project
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        db_url or "postgresql://postgres:Password@localhost:5432/cbs_project"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Auto-create tables in PostgreSQL on startup
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Database table initialization deferred: {e}")

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app
