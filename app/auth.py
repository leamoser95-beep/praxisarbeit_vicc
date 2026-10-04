"""Registrierung, Login und Logout (Session-basiert über Flask-Login)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager
from models import User

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    # Wird bei jedem Request aufgerufen: die User-ID steht im signierten
    # Session-Cookie, der User selbst wird aus der Datenbank geladen.
    # Dadurch braucht keine Instanz lokalen Zustand (wichtig für Skalierung).
    return db.session.get(User, int(user_id))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 8:
            flash("Bitte alle Felder ausfüllen. Das Passwort braucht mindestens 8 Zeichen.", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("Benutzername oder E-Mail ist bereits registriert.", "error")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        flash("Konto erstellt. Du kannst dich jetzt anmelden.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("E-Mail oder Passwort ist falsch.", "error")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Du bist abgemeldet.", "success")
    return redirect(url_for("auth.login"))
