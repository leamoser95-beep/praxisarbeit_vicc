"""Übersicht der eigenen Zahlungen und Rückerstattungen."""
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models import Booking, Payment

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/payments")
@login_required
def list_payments():
    # Nur Zahlungen zu eigenen Buchungen anzeigen
    payments = (Payment.query
                .join(Booking)
                .filter(Booking.user_id == current_user.id)
                .order_by(Payment.timestamp.desc())
                .all())
    return render_template("payments.html", payments=payments)
