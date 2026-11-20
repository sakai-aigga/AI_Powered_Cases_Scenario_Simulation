"""
Database Models
Defines the User entity matching the PostgreSQL schema:
Table users {
  user_id uuid [pk, default: `gen_random_uuid()`]
  full_name varchar(120) [not null]
  email varchar(150) [unique, not null]
  password_hash varchar(255) [not null]
  role user_role [not null, default: 'student']
  is_active boolean [default: true]
  created_at timestamp [default: `now()`]
}
"""

import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID, ENUM
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define the PostgreSQL user_role enum
user_role_enum = ENUM(
    "student", "teacher", "admin",
    name="user_role",
    create_type=False
)


class User(db.Model):
    """User account model matching the PostgreSQL schema."""
    __tablename__ = "users"

    user_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()")
    )
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        user_role_enum,
        nullable=False,
        default="student",
        server_default="student"
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        server_default=db.text("true")
    )
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=db.text("now()")
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_teacher(self) -> bool:
        return self.role == "teacher"

    def is_student(self) -> bool:
        return self.role == "student"

    def __repr__(self):
        return f"<User {self.full_name} ({self.email}) [{self.role}]>"
