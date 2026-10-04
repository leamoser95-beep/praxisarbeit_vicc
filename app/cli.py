"""
CLI-Befehl `flask init-db`: Tabellen anlegen und die fünf Mietautos eintragen.

Wird beim Start jedes Containers ausgeführt (siehe entrypoint.sh) und ist
idempotent: bestehende Tabellen und Autos bleiben unverändert.

Starten mehrere Replicas gleichzeitig, sorgt ein PostgreSQL Advisory Lock dafür,
dass nur eine Instanz zur gleichen Zeit initialisiert. Die anderen warten und
stellen danach fest, dass nichts mehr zu tun ist.
"""
from decimal import Decimal

import click
from sqlalchemy import text

from extensions import db
from models import Car

# Beliebige, aber feste Zahl als Name für den Advisory Lock
INIT_LOCK_ID = 4711

FLEET = [
    dict(brand="Toyota", model="Yaris Hybrid", category="Kleinwagen", seats=5,
         fuel="Hybrid", plate="SG 104 211", price_per_day=Decimal("69.00")),
    dict(brand="VW", model="Golf", category="Kompaktklasse", seats=5,
         fuel="Benzin", plate="SG 218 734", price_per_day=Decimal("79.00")),
    dict(brand="Škoda", model="Octavia Combi 4x4", category="Kombi", seats=5,
         fuel="Diesel", plate="SG 330 125", price_per_day=Decimal("95.00")),
    dict(brand="Tesla", model="Model 3", category="Mittelklasse", seats=5,
         fuel="Elektro", plate="SG 457 902", price_per_day=Decimal("129.00")),
    dict(brand="VW", model="Multivan", category="Kleinbus", seats=7,
         fuel="Diesel", plate="SG 561 048", price_per_day=Decimal("149.00")),
]


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Tabellen anlegen und Fahrzeugflotte eintragen (idempotent)."""
        if db.engine.dialect.name == "postgresql":
            # Transaktions-Lock: wird beim Commit automatisch wieder freigegeben
            db.session.execute(text(f"SELECT pg_advisory_xact_lock({INIT_LOCK_ID})"))

        # Tabellen innerhalb derselben Transaktion anlegen (nur fehlende)
        db.metadata.create_all(bind=db.session.connection())

        added = 0
        for data in FLEET:
            if not Car.query.filter_by(plate=data["plate"]).first():
                db.session.add(Car(**data))
                added += 1

        db.session.commit()
        click.echo(f"Datenbank bereit, {added} Fahrzeug(e) neu eingetragen.")
