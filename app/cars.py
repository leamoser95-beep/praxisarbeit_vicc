"""Fahrzeugübersicht und Buchung eines Autos."""
from datetime import date
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from availability import conflicting_booking, is_available, upcoming_bookings
from extensions import db
from models import Booking, Car, Payment

cars_bp = Blueprint("cars", __name__)

PAYMENT_METHODS = ["Kreditkarte", "TWINT", "Rechnung"]


@cars_bp.route("/cars")
@login_required
def list_cars():
    today = date.today()
    cars = Car.query.order_by(Car.price_per_day).all()
    # Pro Auto merken, ob es heute frei ist (für die Anzeige)
    free_today = {car.id: is_available(car.id, today, today) for car in cars}
    return render_template("cars.html", cars=cars, free_today=free_today)


@cars_bp.route("/cars/<int:car_id>/book", methods=["GET", "POST"])
@login_required
def book(car_id):
    car = db.session.get(Car, car_id) or abort(404)

    if request.method == "POST":
        try:
            start = date.fromisoformat(request.form.get("start_date", ""))
            end = date.fromisoformat(request.form.get("end_date", ""))
        except ValueError:
            flash("Bitte ein gültiges Start- und Enddatum wählen.", "error")
            return redirect(url_for("cars.book", car_id=car_id))

        method = request.form.get("method")
        if method not in PAYMENT_METHODS:
            flash("Bitte eine Zahlungsart wählen.", "error")
            return redirect(url_for("cars.book", car_id=car_id))

        if start < date.today():
            flash("Der Mietbeginn darf nicht in der Vergangenheit liegen.", "error")
            return redirect(url_for("cars.book", car_id=car_id))
        if end < start:
            flash("Das Enddatum muss am oder nach dem Startdatum liegen.", "error")
            return redirect(url_for("cars.book", car_id=car_id))

        # Zeile des Autos sperren (SELECT ... FOR UPDATE).
        # Bei mehreren Replicas könnten zwei Instanzen gleichzeitig dasselbe Auto
        # buchen. Die Sperre in der Datenbank sorgt dafür, dass Buchungen pro Auto
        # nacheinander geprüft werden, egal auf welcher Instanz der Request landet.
        db.session.execute(select(Car).where(Car.id == car_id).with_for_update())

        conflict = conflicting_booking(car_id, start, end)
        if conflict:
            db.session.rollback()
            flash(f"Das Auto ist vom {conflict.start_date:%d.%m.%Y} bis "
                  f"{conflict.end_date:%d.%m.%Y} bereits gebucht.", "error")
            return redirect(url_for("cars.book", car_id=car_id))

        days = (end - start).days + 1
        total = Decimal(car.price_per_day) * days

        booking = Booking(car_id=car.id, user_id=current_user.id,
                          start_date=start, end_date=end, total_price=total)
        db.session.add(booking)
        db.session.flush()  # erzeugt booking.id für die Zahlung

        # Zahlung wird nur simuliert (kein echter Payment-Provider)
        db.session.add(Payment(booking_id=booking.id, amount=total, method=method))
        db.session.commit()

        return redirect(url_for("bookings.summary", booking_id=booking.id))

    return render_template("book.html", car=car,
                           taken=upcoming_bookings(car_id),
                           methods=PAYMENT_METHODS,
                           today=date.today().isoformat())
