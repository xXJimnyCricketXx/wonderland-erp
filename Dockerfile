FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# weasyprint (PDF reports) needs these system libs at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    shared-mime-info fonts-dejavu-core libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# /data ist das einzige persistente Volume (Unraid-Appdata-Pfad): beide
# SQLite-Datenbanken und alle hochgeladenen Dateien (Rechnungen, USt-Berichte,
# Profilbilder) liegen darunter, damit ein einziger Volume-Mount reicht.
ENV DB_PATH=/data/db.sqlite3 \
    LEXIKON_DB_PATH=/data/lexikon.sqlite3 \
    MEDIA_ROOT=/data/media \
    DEBUG=False

VOLUME ["/data"]
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
