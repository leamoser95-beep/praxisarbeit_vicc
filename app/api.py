"""
Öffentliche JSON-API (Web-API gemäss Aufgabenstellung).

GET /api/health                      Liveness: läuft der Prozess?
GET /api/ready                       Readiness: ist die Datenbank erreichbar?
GET /api/cars                        alle Autos, optional ?from=YYYY-MM-DD&to=YYYY-MM-DD
GET /api/cars/<id>                   ein Auto inkl. belegter Zeiträume

Die API ist bewusst nur lesend und gibt keine Kundendaten heraus.
"""
import socket
from datetime import date

from flask import Blueprint, abort, jsonify, request
from sqlalchemy import text

from availability import is_available, upcoming_bookings
from extensions import db
from models import Car

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Name des Containers/Replicas. Zeigt beim Testen, welche Instanz geantwortet
# hat, und macht so die Lastverteilung zwischen Replicas sichtbar.
INSTANCE = socket.gethostname()


@api_bp.route("/health")
def health():
    # Bewusst OHNE Datenbankprüfung: Ist die DB kurz weg, soll der Container
    # nicht neu gestartet werden (das würde das Problem nicht lösen).
    return jsonify(status="ok", instance=INSTANCE)


@api_bp.route("/ready")
def ready():
    # Readiness: Nur Instanzen mit funktionierender DB-Verbindung erhalten Traffic.
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ready", database="ok", instance=INSTANCE)
    except Exception:
        db.session.rollback()
        return jsonify(status="not ready", database="unreachable", instance=INSTANCE), 503


def _parse_range():
    """Liest ?from= und ?to= aus der URL. Ohne Angabe gilt der heutige Tag."""
    try:
        start = date.fromisoformat(request.args.get("from", date.today().isoformat()))
        end = date.fromisoformat(request.args.get("to", start.isoformat()))
    except ValueError:
        abort(400, description="Datum im Format YYYY-MM-DD angeben.")
    if end < start:
        abort(400, description="'to' muss am oder nach 'from' liegen.")
    return start, end


@api_bp.route("/cars")
def cars():
    start, end = _parse_range()
    result = []
    for car in Car.query.order_by(Car.id).all():
        item = car.to_dict()
        item["available"] = is_available(car.id, start, end)
        result.append(item)
    return jsonify(period={"from": start.isoformat(), "to": end.isoformat()},
                   cars=result, instance=INSTANCE)


@api_bp.route("/cars/<int:car_id>")
def car_detail(car_id):
    car = db.session.get(Car, car_id)
    if car is None:
        abort(404, description="Auto nicht gefunden.")
    item = car.to_dict()
    item["booked_periods"] = [
        {"from": b.start_date.isoformat(), "to": b.end_date.isoformat()}
        for b in upcoming_bookings(car_id)
    ]
    return jsonify(car=item, instance=INSTANCE)


@api_bp.errorhandler(400)
@api_bp.errorhandler(404)
def api_error(err):
    # API-Fehler als JSON statt als HTML-Seite zurückgeben
    return jsonify(error=err.description), err.code
