# Fünf Wagen – Autovermietung in Azure

Praxisarbeit VICC (Virtualisierung und Cloud Computing), ipso / IFA, HFINFP 3. Studienjahr.

Eine kleine Autovermietung mit fünf Autos: Konto erstellen, Auto für einen
Zeitraum buchen, Buchungen stornieren, Zahlungen ansehen. Zusätzlich gibt es
eine öffentliche JSON-API.

## Aufbau

| Ordner | Inhalt |
|---|---|
| `app/` | Flask-Anwendung, Dockerfile, Startskript |
| `infra/` | Terraform-Code für die komplette Azure-Infrastruktur |
| `.github/workflows/` | Pipeline: Image bauen und auf Docker Hub veröffentlichen |
| `docker-compose.yml` | lokale Testumgebung mit Postgres |

Azure-Ressourcen (alle per Terraform erstellt): Resource Group, Log Analytics
Workspace, Azure Database for PostgreSQL Flexible Server, Container Apps
Environment, Container App.

Container-Image: `docker.io/<DOCKERHUB-NAME>/autovermietung` (öffentlich)

## Web-API

| Aufruf | Beschreibung |
|---|---|
| `GET /api/health` | Lebenszeichen, zeigt die antwortende Instanz |
| `GET /api/ready` | prüft zusätzlich die Datenbankverbindung |
| `GET /api/cars` | alle Autos mit Verfügbarkeit heute |
| `GET /api/cars?from=2026-10-01&to=2026-10-05` | Verfügbarkeit für einen Zeitraum |
| `GET /api/cars/<id>` | ein Auto mit belegten Zeiträumen |

## Nachbauen

Voraussetzungen: Azure CLI, Terraform ≥ 1.6, Azure-Subscription.

```bash
az login
cd infra
cp terraform.tfvars.example terraform.tfvars   # Werte eintragen
terraform init
terraform apply
```

Die Ausgabe `app_url` enthält die öffentliche Adresse. Beim ersten Start legt
die App die Tabellen an und trägt die fünf Autos ein.

Neue Version ausrollen (Tag = Commit-Hash aus der Pipeline):

```bash
terraform apply -var="image_tag=<commit-hash>"
```

Alles wieder entfernen: `terraform destroy`

Hinweise für Azure for Students:
- Meldet Terraform `RequestDisallowedByAzure` oder dass die Region für
  PostgreSQL gesperrt ist, eine andere Region in `terraform.tfvars` setzen
  (z.B. `germanywestcentral`, `northeurope` oder `westeurope`).
- Meldet Terraform `MissingSubscriptionRegistration`:
  `az provider register --namespace Microsoft.App`
  (ebenso `Microsoft.DBforPostgreSQL` und `Microsoft.OperationalInsights`).

## Lokal testen

```bash
docker compose up --build
```

Danach ist die App unter http://localhost:8000 erreichbar.
