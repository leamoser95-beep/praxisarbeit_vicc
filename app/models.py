"""
Datenmodell der Autovermietung.

User     – Kundenkonto (Login)
Car      – eines der fünf Mietautos
Booking  – Buchung eines Autos für einen Zeitraum (ganze Tage)
Payment  – simulierte Zahlung bzw. Rückerstattung zu einer Buchung
"""
from datetime import datetime, timezone

from flask_login import UserMixin

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    bookings = db.relationship("Booking", back_populates="user")


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(40), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    fuel = db.Column(db.String(20), nullable=False)
    plate = db.Column(db.String(20), unique=True, nullable=False)
    price_per_day = db.Column(db.Numeric(8, 2), nullable=False)

    bookings = db.relationship("Booking", back_populates="car")

    @property
    def name(self):
        return f"{self.brand} {self.model}"

    def to_dict(self):
        """Darstellung für die JSON-API."""
        return {
            "id": self.id,
            "brand": self.brand,
            "model": self.model,
            "category": self.category,
            "seats": self.seats,
            "fuel": self.fuel,
            "plate": self.plate,
            "price_per_day": float(self.price_per_day),
        }


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    # Mietdauer in ganzen Tagen, beide Tage inklusive
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmed")  # confirmed / cancelled
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    car = db.relationship("Car", back_populates="bookings")
    user = db.relationship("User", back_populates="bookings")
    payments = db.relationship("Payment", back_populates="booking")

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # negativ = Rückerstattung
    method = db.Column(db.String(30), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=utcnow)

    booking = db.relationship("Booking", back_populates="payments")
