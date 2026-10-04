"""Eigene Buchungen anzeigen und stornieren."""
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Booking, Payment

bookings_bp = Blueprint("bookings", __name__)


def _own_booking_or_404(booking_id):
    """Kundinnen und Kunden dürfen nur ihre eigenen Buchungen sehen."""
    booking = db.session.get(Booking, booking_id)
    if booking is None or booking.user_id != current_user.id:
        abort(404)
    return booking


@bookings_bp.route("/bookings")
@login_required
def my_bookings():
    bookings = (Booking.query
                .filter_by(user_id=current_user.id)
                .order_by(Booking.start_date.desc())
                .all())
    return render_template("bookings.html", bookings=bookings, today=date.today())


@bookings_bp.route("/bookings/<int:booking_id>")
@login_required
def summary(booking_id):
    return render_template("booking_summary.html", booking=_own_booking_or_404(booking_id))


@bookings_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel(booking_id):
    booking = _own_booking_or_404(booking_id)

    # Stornieren ist nur vor Mietbeginn möglich
    if booking.status != "confirmed" or booking.start_date <= date.today():
        flash("Diese Buchung kann nicht mehr storniert werden.", "error")
        return redirect(url_for("bookings.my_bookings"))

    booking.status = "cancelled"
    # Rückerstattung als negative Zahlung erfassen
    db.session.add(Payment(booking_id=booking.id, amount=-booking.total_price,
                           method="Rückerstattung"))
    db.session.commit()

    flash("Buchung storniert. Der Betrag wird zurückerstattet.", "success")
    return redirect(url_for("bookings.my_bookings"))
