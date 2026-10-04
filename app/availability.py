"""
Verfügbarkeitsprüfung, wird von Web-Oberfläche und API gemeinsam genutzt.

Ein Auto ist in einem Zeitraum frei, wenn es keine bestätigte Buchung gibt,
die sich mit diesem Zeitraum überschneidet.
"""
from datetime import date

from models import Booking


def conflicting_booking(car_id: int, start: date, end: date):
    """Liefert die erste überschneidende Buchung oder None."""
    return (
        Booking.query
        .filter(Booking.car_id == car_id,
                Booking.status == "confirmed",
                Booking.start_date <= end,
                Booking.end_date >= start)
        .first()
    )


def is_available(car_id: int, start: date, end: date) -> bool:
    return conflicting_booking(car_id, start, end) is None


def upcoming_bookings(car_id: int):
    """Belegte Zeiträume ab heute (ohne Kundendaten), für Anzeige und API."""
    return (
        Booking.query
        .filter(Booking.car_id == car_id,
                Booking.status == "confirmed",
                Booking.end_date >= date.today())
        .order_by(Booking.start_date)
        .all()
    )
