"""
Authentication Controller
Handles user registration, login, and dashboard sessions using the updated PostgreSQL schema:
- user_id (uuid)
- full_name (varchar 120)
- email (varchar 150, unique)
- password_hash (varchar 255)
- role (user_role enum)
- is_active (boolean)
- created_at (timestamp)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "user" in session:
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter both your email address and password.", "error")
            return render_template("login.html")

        try:
            user = User.query.filter(db.func.lower(User.email) == email).first()

            if user and user.check_password(password):
                if not user.is_active:
                    flash("Your account has been deactivated. Please contact an instructor.", "error")
                    return render_template("login.html")

                session["user"] = {
                    "user_id": str(user.user_id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role
                }
                return redirect(url_for("auth.dashboard"))
            else:
                flash("The email or password you entered is incorrect.", "error")
        except Exception as e:
            flash("Database connection error. Please verify PostgreSQL is accessible.", "error")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student").strip().lower()

        if not full_name or not email or not password:
            flash("All fields are required. Please fill in your name, email, and password.", "error")
            return render_template("register.html")

        if len(full_name) > 120:
            flash("Full name cannot exceed 120 characters.", "error")
            return render_template("register.html")

        if len(email) > 150:
            flash("Email address cannot exceed 150 characters.", "error")
            return render_template("register.html")

        # Restrict role assignment to student or teacher
        if role not in ("student", "teacher"):
            role = "student"

        try:
            existing = User.query.filter(db.func.lower(User.email) == email).first()
            if existing:
                flash("An account with that email address already exists.", "error")
                return render_template("register.html")

            new_user = User(
                full_name=full_name,
                email=email,
                role=role,
                is_active=True
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash("Your account has been created successfully. Please sign in.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while creating your account. Please try again.", "error")

    return render_template("register.html")


@auth_bp.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))

    return render_template("dashboard.html", user=user)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have successfully signed out.", "info")
    return redirect(url_for("auth.login"))
