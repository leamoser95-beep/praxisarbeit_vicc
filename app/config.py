"""
Konfiguration der Anwendung.

Alle umgebungsabhängigen Werte (Datenbank, Secret Key, Cookie-Einstellungen)
kommen aus Umgebungsvariablen. So läuft dasselbe Container-Image lokal,
in Azure oder bei einem anderen Anbieter, ohne dass der Code geändert wird
(12-Factor-Prinzip). Passwörter stehen dadurch nie im Git-Repository.
"""
import os
import secrets


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Fallback für schnelle lokale Tests ohne Postgres
        return "sqlite:///local.db"
    # Manche Anbieter liefern "postgres://", SQLAlchemy erwartet "postgresql://"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    # Der Secret Key signiert die Session-Cookies. Alle Replicas müssen
    # denselben Key verwenden, sonst ist ein Login nur auf einer Instanz gültig.
    # In Azure wird er von Terraform als Secret gesetzt.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pool_pre_ping erkennt abgebrochene DB-Verbindungen (z.B. nach einem
    # Neustart oder Failover der verwalteten Datenbank) und baut sie neu auf.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    # Cookie-Härtung. COOKIE_SECURE=true in der Cloud (HTTPS),
    # lokal false, weil dort ohne HTTPS getestet wird.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
