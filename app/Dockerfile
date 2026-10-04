# Container-Image der Autovermietung
FROM python:3.12-slim

# Keine .pyc-Dateien, Logs sofort ausgeben (wichtig für Log Analytics)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Abhängigkeiten zuerst kopieren: Dieser Layer wird gecacht, solange sich
# requirements.txt nicht ändert. Das beschleunigt die Builds in der Pipeline.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nicht als root laufen (Sicherheits-Best-Practice)
RUN chmod +x entrypoint.sh && useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
