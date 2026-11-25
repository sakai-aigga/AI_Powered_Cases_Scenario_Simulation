"""
Admin Controller
Features implemented per project proposal (pp.txt):
- Section 4.4 / Line 89 & 91: Admin manages lower-level users and sets LLM configurations.
- Section 5 / Line 143: Groq API and Gemini API provider selection, routing, and fallback.
- Section 6 / Line 154: Admin dashboard with user management and LLM configurations.
- Direct query execution: SELECT, UPDATE, DELETE on PostgreSQL without DDL or table altering.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import db, User, LLMConfiguration

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to restrict view access strictly to administrators."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_session = session.get("user")
        if not user_session or user_session.get("role") != "admin":
            flash("Administrator access required.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("")
@admin_bp.route("/")
@admin_required
def dashboard():
    """Admin Dashboard: user management, stats, and LLM configuration."""
    users = User.query.order_by(User.created_at.desc()).all()
    llm_config = LLMConfiguration.query.first()

    # User statistics
    total_users = len(users)
    student_count = sum(1 for u in users if u.role == "student")
    teacher_count = sum(1 for u in users if u.role == "teacher")
    admin_count = sum(1 for u in users if u.role == "admin")
    active_count = sum(1 for u in users if u.is_active in ("Active", "Away", "Busy"))

    stats = {
        "total_users": total_users,
        "students": student_count,
        "teachers": teacher_count,
        "admins": admin_count,
        "active_users": active_count
    }

    return render_template(
        "admin/admin_dashboard.html",
        user=session.get("user"),
        users=users,
        llm_config=llm_config,
        stats=stats
    )


@admin_bp.route("/user/<uuid:user_id>/update-role", methods=["POST"])
@admin_required
def update_user_role(user_id):
    """Updates a user's role via direct query. Admins cannot have their role changed."""
    new_role = request.form.get("role", "").strip().lower()
    if new_role not in ("student", "teacher", "admin"):
        flash("Invalid role specified.", "error")
        return redirect(url_for("admin.dashboard"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.dashboard"))

    # Administrator roles cannot be changed
    if user.role == "admin":
        flash("Administrator roles are protected and cannot be changed.", "error")
        return redirect(url_for("admin.dashboard"))

    current_admin_id = session.get("user", {}).get("user_id")
    if str(user.user_id) == str(current_admin_id):
        flash("You cannot change your own administrative role.", "error")
        return redirect(url_for("admin.dashboard"))

    user.role = new_role
    db.session.commit()

    flash(f"Updated role for {user.full_name} to {new_role.capitalize()}.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/user/<uuid:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id):
    """Toggles user status between Active and Inactive via direct query."""
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.dashboard"))

    # Prevent admin from deactivating their own currently logged-in account
    current_admin_id = session.get("user", {}).get("user_id")
    if str(user.user_id) == str(current_admin_id):
        flash("Please update your personal status through Profile Settings.", "info")
        return redirect(url_for("admin.dashboard"))

    if user.is_active in ("Active", "Away", "Busy"):
        user.is_active = "Inactive"
    else:
        user.is_active = "Active"

    db.session.commit()

    flash(f"Status for {user.full_name} set to {user.is_active}.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/user/<uuid:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Deletes a user account from PostgreSQL via direct DELETE query."""
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.dashboard"))

    # Prevent admin from deleting their own currently logged-in account
    current_admin_id = session.get("user", {}).get("user_id")
    if str(user.user_id) == str(current_admin_id):
        flash("You cannot delete your own administrative account.", "error")
        return redirect(url_for("admin.dashboard"))

    deleted_name = user.full_name
    db.session.delete(user)
    db.session.commit()

    flash(f"User account '{deleted_name}' has been permanently deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/llm-config", methods=["POST"])
@admin_required
def update_llm_config():
    """Updates external LLM API settings (Gemini / Groq) via direct query."""
    config = LLMConfiguration.query.first()
    if not config:
        config = LLMConfiguration()
        db.session.add(config)

    config.active_provider = request.form.get("active_provider", "gemini").strip().lower()
    config.fallback_provider = request.form.get("fallback_provider", "groq").strip().lower()
    config.fallback_enabled = bool(request.form.get("fallback_enabled"))

    config.gemini_api_key = request.form.get("gemini_api_key", "").strip()
    config.gemini_model = request.form.get("gemini_model", "gemini-1.5-flash").strip()

    config.groq_api_key = request.form.get("groq_api_key", "").strip()
    config.groq_model = request.form.get("groq_model", "llama-3.3-70b-versatile").strip()

    try:
        config.temperature = float(request.form.get("temperature", 0.70))
        config.max_tokens = int(request.form.get("max_tokens", 1024))
    except (ValueError, TypeError):
        pass

    db.session.commit()
    flash("LLM configuration parameters saved successfully.", "success")
    return redirect(url_for("admin.dashboard"))
