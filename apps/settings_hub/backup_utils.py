"""File-based backups - the filesystem is the source of truth (not a DB
table), so backups survive even a full database reset."""

import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings

BACKUP_DIR = Path(settings.BASE_DIR) / "data" / "backups"


def list_backups():
    if not BACKUP_DIR.exists():
        return []
    files = sorted(BACKUP_DIR.glob("*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "name": f.name,
            "size": f.stat().st_size,
            "created_at": datetime.fromtimestamp(f.stat().st_mtime),
        }
        for f in files
    ]


def create_backup():
    """Uses sqlite3's own backup API rather than a raw file copy - safe even
    while the app is running in WAL mode with a live connection."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest_path = BACKUP_DIR / f"backup_{timestamp}.sqlite3"

    source = sqlite3.connect(settings.DATABASES["default"]["NAME"])
    dest = sqlite3.connect(str(dest_path))
    with dest:
        source.backup(dest)
    source.close()
    dest.close()
    return dest_path


def enforce_retention(keep_count):
    for old in list_backups()[keep_count:]:
        (BACKUP_DIR / old["name"]).unlink(missing_ok=True)


def get_backup_path(filename):
    """Resolves filename against BACKUP_DIR and rejects anything that would
    escape it (path traversal via '..' or absolute paths)."""
    path = (BACKUP_DIR / filename).resolve()
    if path.parent != BACKUP_DIR.resolve():
        return None
    return path if path.exists() else None
