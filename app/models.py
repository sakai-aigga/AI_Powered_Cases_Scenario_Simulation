"""
Database Models
Defines the User and LLMConfiguration entities for querying and data management.
Schema definitions match the existing PostgreSQL tables:
- users
- llm_configurations
"""

import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID, ENUM
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Existing PostgreSQL user_role enum
user_role_enum = ENUM(
    "student", "teacher", "admin",
    name="user_role",
    create_type=False
)


class User(db.Model):
    """User account entity for students, teachers, and administrators."""
    __tablename__ = "users"

    user_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        user_role_enum,
        nullable=False,
        default="student"
    )
    is_active = db.Column(db.String(30), nullable=False, default="Inactive")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(
        self,
        full_name: str = "",
        email: str = "",
        role: str = "student",
        is_active: str = "Inactive",
        password_hash: str = "",
        password: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.full_name = full_name
        self.email = email
        self.role = role
        self.is_active = is_active
        if password:
            self.set_password(password)
        elif password_hash:
            self.password_hash = password_hash

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_teacher(self) -> bool:
        return self.role == "teacher"

    def is_student(self) -> bool:
        return self.role == "student"

    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.full_name} ({self.email}) [{self.role}]>"


class LLMConfiguration(db.Model):
    """LLM Provider and fallback configurations managed by Admin (per proposal sections 4.4, 5)."""
    __tablename__ = "llm_configurations"

    config_id = db.Column(db.Integer, primary_key=True)
    active_provider = db.Column(db.String(50), nullable=False, default="gemini")  # 'gemini' or 'groq'
    fallback_provider = db.Column(db.String(50), nullable=False, default="groq")
    fallback_enabled = db.Column(db.Boolean, nullable=False, default=True)
    gemini_api_key = db.Column(db.String(255), default="")
    gemini_model = db.Column(db.String(100), nullable=False, default="gemini-1.5-flash")
    groq_api_key = db.Column(db.String(255), default="")
    groq_model = db.Column(db.String(100), nullable=False, default="llama-3.3-70b-versatile")
    temperature = db.Column(db.Numeric(3, 2), nullable=False, default=0.70)
    max_tokens = db.Column(db.Integer, nullable=False, default=1024)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<LLMConfiguration active={self.active_provider} fallback={self.fallback_provider}>"
