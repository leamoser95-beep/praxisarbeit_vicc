"""
Einstiegspunkt der Anwendung (Application Factory).

Lokal starten:  flask --app app init-db && flask --app app run
Im Container:   gunicorn "app:create_app()"  (siehe entrypoint.sh)
"""
from datetime import date

from flask import Flask, redirect, render_template, url_for
from flask_login import current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix

from api import api_bp
from auth import auth_bp
from bookings import bookings_bp
from cars import cars_bp
from cli import register_cli
from config import Config
from extensions import db, login_manager
from models import Booking
from payments import payments_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Azure Container Apps beendet HTTPS am Ingress und leitet per HTTP an den
    # Container weiter. ProxyFix übernimmt die X-Forwarded-Header, damit Flask
    # korrekte https-Links und die echte Client-IP kennt.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(cars_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(api_bp)
    register_cli(app)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("auth.login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        # Nächste bzw. laufende Buchung der angemeldeten Person
        next_booking = (Booking.query
                        .filter(Booking.user_id == current_user.id,
                                Booking.status == "confirmed",
                                Booking.end_date >= date.today())
                        .order_by(Booking.start_date)
                        .first())
        return render_template("dashboard.html", next_booking=next_booking,
                               today=date.today())

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html", message="Diese Seite gibt es nicht."), 404

    # Datumsformat für die Templates (Schweizer Schreibweise)
    @app.template_filter("chdate")
    def chdate(value):
        return value.strftime("%d.%m.%Y") if value else "–"

    @app.template_filter("chf")
    def chf(value):
        return f"{value:,.2f}".replace(",", "’") if value is not None else "–"

    return app
