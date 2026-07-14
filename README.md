<p align="center">
  <img src="static/img/wonderland-erp-banner.png" alt="Wonderland ERP" width="100%">
</p>

<p align="center">
  Internes Verwaltungstool für den Etsy-Shop Wonderland Diorama.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-unlicensed-lightgrey" alt="License">
  <img src="https://img.shields.io/badge/self--hosted-yes-orange" alt="Self-hosted">
  <img src="https://img.shields.io/badge/docker-ready-2496ED" alt="Docker ready">
  <a href="https://github.com/xXJimnyCricketXx/wonderland-erp/actions/workflows/docker-publish.yml">
    <img src="https://github.com/xXJimnyCricketXx/wonderland-erp/actions/workflows/docker-publish.yml/badge.svg" alt="Build status">
  </a>
</p>

## Überblick

Wonderland ERP bündelt Artikel, Bestellungen, Kontakte und Finanzen (inkl. SKR03-Zuordnung)
an einem Ort und macht daraus ein auswertbares Dashboard mit Diagrammen - als in sich
geschlossene App auf dem eigenen Server, ohne dass Daten das Haus verlassen.

## Inhalt

- [Funktionsumfang](#funktionsumfang)
- [Schnellstart (Docker Compose)](#schnellstart-docker-compose)
- [Unraid](#unraid)
- [Konfiguration](#konfiguration)
- [Tech-Stack](#tech-stack)
- [Entwicklung](#entwicklung)
- [Lizenz](#lizenz)

## Funktionsumfang

- **Dashboard** — Kennzahlen, Diagramme (Einnahmen/Ausgaben, SKR03-Aufschlüsselung,
  Vorjahresvergleich, Top-5-Artikel), Kunden-Weltkarte, Aufgaben-/Termin-Übersicht,
  filterbar nach Jahr/Quartal/Monat (Mehrfachauswahl)
- **Artikel & Wunschliste** — Katalog inkl. Varianten, Lagerbestand, Etsy-Listing-Zuordnung
- **Bestellungen** — inkl. Etsy-Import (Sold Orders/Order Items), Bewertungen
- **Kontakte** — Kunden und Lieferanten getrennt verwaltet
- **Finanzen** — Einnahmen/Ausgaben mit SKR03-Kontenzuordnung, Etsy-Rohdaten/Statement-Import,
  USt-Berichte, SKR03-Übersicht
- **Aufgaben & Termine** — Kanban-Board mit Drag & Drop, Kalender (Monat/Woche/Liste)
- **Infothek** — Materialkategorien, Verpackungsarten, Verpackungslizenz (LUCID),
  Heilstein-Lexikon
- **Dokumente** — zentrale Ablage für Rechnungen, USt-Berichte und mehr
- **Nachrichten** — Echtzeit-artiger Chat zwischen registrierten Nutzern
- **Referenzdaten** — die meisten Dropdown-Werte im ganzen System frei konfigurierbar
- **Single-Container** — läuft komplett in einem Docker-Container, alle Daten liegen in
  einem `/data`-Volume

## Schnellstart (Docker Compose)

```bash
git clone https://github.com/xXJimnyCricketXx/wonderland-erp.git
cd wonderland-erp
cp .env.example .env
# .env bearbeiten und mindestens SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS setzen
docker compose up -d --build
```

Die App ist danach unter `http://localhost:18001` erreichbar.

### Ersten Admin-Account anlegen

Entweder automatisch beim ersten Start, indem `ADMIN_USERNAME`/`ADMIN_PASSWORD` in `.env`
gesetzt werden, oder nachträglich manuell:

```bash
docker compose exec wonderland-erp python manage.py createsuperuser
```

## Unraid

Ein fertiges Unraid-Template liegt unter [`unraid-template.xml`](unraid-template.xml). In
Unraid unter *Docker → Add Container → Template* die rohe GitHub-URL dieser Datei eintragen
(oder die Datei direkt nach `/boot/config/plugins/dockerMan/templates-user/` kopieren, falls
kein Community-Applications-Plugin installiert ist) - Port, Datenpfad und alle Variablen sind
dann vorausgefüllt.

## Konfiguration

| Variable | Pflicht | Beschreibung |
|---|---|---|
| `SECRET_KEY` | ja | Zufälliger Schlüssel für Sessions/CSRF, z.B. `openssl rand -hex 32` |
| `ALLOWED_HOSTS` | ja | Kommagetrennte Liste erlaubter Hostnamen/IPs |
| `CSRF_TRUSTED_ORIGINS` | ja | Kommagetrennte Liste vertrauenswürdiger Origins inkl. Schema+Port |
| `ADMIN_USERNAME` | nein | Benutzername für den beim ersten Start automatisch angelegten Admin-Account |
| `ADMIN_PASSWORD` | nein | Passwort dafür — beide Werte müssen gesetzt sein, sonst wird nichts automatisch angelegt |
| `DB_PATH` | nein | Pfad zur Haupt-Datenbank (Standard: `/data/db.sqlite3`) |
| `LEXIKON_DB_PATH` | nein | Pfad zur Heilstein-Lexikon-Datenbank (Standard: `/data/lexikon.sqlite3`) |
| `MEDIA_ROOT` | nein | Pfad für hochgeladene Dateien (Standard: `/data/media`) |

Datenbanken und Medien-Dateien liegen standardmäßig alle unter `/data` - im Docker-Setup ein
einziges gemountetes Volume, ein einfaches Backup des Ordners reicht also.

## Tech-Stack

| Komponente | Technologie |
|---|---|
| Backend | Django 5.2 |
| Datenbank | SQLite (WAL-Modus) |
| Frontend | Server-seitige Templates, Bootstrap 5, HTMX |
| Diagramme | Chart.js, jsvectormap |
| Auth | Django-eigene Session-Authentifizierung |

## Entwicklung

```bash
python -m venv venv
venv/Scripts/activate  # oder: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py migrate --database=lexikon
python manage.py createsuperuser
python manage.py runserver
```

## Lizenz

Es wurde noch keine Lizenz gewählt - bis dahin liegen alle Rechte standardmäßig beim Autor.
