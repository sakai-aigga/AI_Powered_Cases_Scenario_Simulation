"""
Authentication Controller
Handles user registration, login, profile management, and dashboard sessions.
Database interaction is strictly DML queries (SELECT, INSERT, UPDATE) on existing tables.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "user" in session:
        if session["user"].get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter both your email address and password.", "error")
            return render_template("auth/login.html")

        try:
            user = User.query.filter(db.func.lower(User.email) == email).first()

            if user and user.check_password(password):
                # Update presence status to Active on login (preserve Invisible privacy mode if set)
                if user.is_active != "Invisible":
                    user.is_active = "Active"
                db.session.commit()

                session["user"] = {
                    "user_id": str(user.user_id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active
                }

                # Admins are redirected directly to the Admin Console
                if user.role == "admin":
                    return redirect(url_for("admin.dashboard"))
                return redirect(url_for("auth.dashboard"))
            else:
                flash("The email or password you entered is incorrect.", "error")
        except Exception:
            flash("Database connection error. Please verify PostgreSQL is accessible.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student").strip().lower()

        if not full_name or not email or not password:
            flash("All fields are required. Please fill in your name, email, and password.", "error")
            return render_template("auth/register.html")

        if len(full_name) > 120:
            flash("Full name cannot exceed 120 characters.", "error")
            return render_template("auth/register.html")

        if len(email) > 150:
            flash("Email address cannot exceed 150 characters.", "error")
            return render_template("auth/register.html")

        # Restrict role assignment to student or teacher
        if role not in ("student", "teacher"):
            role = "student"

        try:
            existing = User.query.filter(db.func.lower(User.email) == email).first()
            if existing:
                flash("An account with that email address already exists.", "error")
                return render_template("auth/register.html")

            new_user = User(
                full_name=full_name,
                email=email,
                role=role,
                is_active="Inactive"
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash("Your account has been created successfully. Please sign in.", "success")
            return redirect(url_for("auth.login"))

        except Exception:
            db.session.rollback()
            flash("An error occurred while creating your account. Please try again.", "error")

    return render_template("auth/register.html")


@auth_bp.route("/dashboard")
def dashboard():
    user_session = session.get("user")
    if not user_session:
        return redirect(url_for("auth.login"))

    # Administrator does not use default dashboard; redirected directly to Admin Console
    if user_session.get("role") == "admin":
        return redirect(url_for("admin.dashboard"))

    return render_template("dashboard.html", user=user_session)


@auth_bp.route("/profile")
def profile():
    """Profile page for viewing and editing account information and password."""
    user_session = session.get("user")
    if not user_session:
        flash("Please sign in to access your profile.", "info")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    return render_template("auth/profile.html", user=user)


@auth_bp.route("/profile/update-info", methods=["POST"])
def update_profile_info():
    """Updates full name and assigned email address via direct query."""
    user_session = session.get("user")
    if not user_session:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_session["user_id"])
    if not user:
        return redirect(url_for("auth.login"))

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not full_name or not email:
        flash("Full name and email address cannot be empty.", "error")
        return redirect(url_for("auth.profile"))

    if len(full_name) > 120:
        flash("Full name cannot exceed 120 characters.", "error")
        return redirect(url_for("auth.profile"))

    if len(email) > 150:
        flash("Email address cannot exceed 150 characters.", "error")
        return redirect(url_for("auth.profile"))

    # Check if another user already has this email
    existing = User.query.filter(
        db.func.lower(User.email) == email,
        User.user_id != user.user_id
    ).first()
    if existing:
        flash("That email address is already registered to another account.", "error")
        return redirect(url_for("auth.profile"))

    try:
        user.full_name = full_name
        user.email = email
        db.session.commit()

        # Update session values
        session["user"]["full_name"] = full_name
        session["user"]["email"] = email
        session.modified = True

        flash("Your profile information has been updated successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while updating your profile.", "error")

    return redirect(url_for("auth.profile"))


@auth_bp.route("/profile/change-password", methods=["POST"])
def change_password():
    """Changes user password with current password verification via direct query."""
    user_session = session.get("user")
    if not user_session:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_session["user_id"])
    if not user:
        return redirect(url_for("auth.login"))

    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required.", "error")
        return redirect(url_for("auth.profile"))

    if not user.check_password(current_password):
        flash("The current password you entered is incorrect.", "error")
        return redirect(url_for("auth.profile"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "error")
        return redirect(url_for("auth.profile"))

    if new_password != confirm_password:
        flash("The new password and confirmation password do not match.", "error")
        return redirect(url_for("auth.profile"))

    try:
        user.set_password(new_password)
        db.session.commit()
        flash("Your password has been changed successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while changing your password.", "error")

    return redirect(url_for("auth.profile"))


@auth_bp.route("/profile/update-status", methods=["POST"])
def update_status():
    """Allows users to update their activity status or select a privacy mode."""
    user_session = session.get("user")
    if not user_session:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_session["user_id"])
    if not user:
        return redirect(url_for("auth.login"))

    new_status = request.form.get("status", "").strip()
    allowed_statuses = ("Active", "Inactive", "Away", "Busy", "Invisible")

    if new_status not in allowed_statuses:
        flash("Invalid status selected.", "error")
        return redirect(url_for("auth.profile"))

    try:
        user.is_active = new_status
        db.session.commit()

        # Update in-session state
        session["user"]["is_active"] = new_status
        session.modified = True

        if new_status == "Invisible":
            flash("Status set to Invisible. You now appear offline for privacy.", "success")
        else:
            flash(f"Status updated to {new_status}.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while updating your status.", "error")

    return redirect(url_for("auth.profile"))


@auth_bp.route("/logout")
def logout():
    user_session = session.get("user")
    if user_session and user_session.get("user_id"):
        try:
            user = db.session.get(User, user_session["user_id"])
            if user:
                user.is_active = "Inactive"
                db.session.commit()
        except Exception:
            db.session.rollback()

    session.clear()
    flash("You have successfully signed out.", "info")
    return redirect(url_for("auth.login"))
