#!/bin/sh
# Startskript des Containers:
# 1. Datenbank initialisieren (idempotent, per Advisory Lock gegen parallele Starts geschützt)
# 2. Gunicorn als produktiven WSGI-Server starten (statt Flask-Entwicklungsserver)
set -e

flask --app app init-db

# WEB_WORKERS: Anzahl Prozesse pro Container (Standard 2, passend zu 0.5 vCPU)
exec gunicorn "app:create_app()" \
  --bind 0.0.0.0:8000 \
  --workers "${WEB_WORKERS:-2}" \
  --access-logfile - \
  --error-logfile -
