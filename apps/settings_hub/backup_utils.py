"""File-based backups - the filesystem is the source of truth (not a DB
table), so backups survive even a full database reset."""

import re
import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings

# Matches both the current per-database filenames (db_<ts>.sqlite3,
# lexikon_<ts>.sqlite3) and the older single-file scheme (backup_<ts>.sqlite3)
# from before the Heilstein-Lexikon-DB got its own backup - used to group a
# db+lexikon pair created in the same run together for retention purposes.
BACKUP_FILENAME_RE = re.compile(r"^(?:db|lexikon|backup)_(?P<timestamp>.+)\.sqlite3$")

# Neben der Haupt-DB statt fest unter BASE_DIR - folgt damit automatisch
# DB_PATH (im Docker-Deployment /data/db.sqlite3, siehe Dockerfile), sonst
# wuerden Backups im Container ausserhalb des persistenten /data-Volumes
# landen und bei jedem Neustart/Update stillschweigend verloren gehen.
BACKUP_DIR = Path(settings.DATABASES["default"]["NAME"]).resolve().parent / "backups"


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


def _backup_database(db_alias, filename_prefix, timestamp):
    """Uses sqlite3's own backup API rather than a raw file copy - safe even
    while the app is running in WAL mode with a live connection."""
    dest_path = BACKUP_DIR / f"{filename_prefix}_{timestamp}.sqlite3"
    source = sqlite3.connect(settings.DATABASES[db_alias]["NAME"])
    dest = sqlite3.connect(str(dest_path))
    with dest:
        source.backup(dest)
    source.close()
    dest.close()
    return dest_path


def create_backup():
    """Backs up both SQLite databases (Haupt-DB und Heilstein-Lexikon-DB) as
    a matching pair with the same timestamp - the Lexikon-DB used to be left
    out entirely, which meant it had no backup coverage at all."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return {
        "default": _backup_database("default", "db", timestamp),
        "lexikon": _backup_database("lexikon", "lexikon", timestamp),
    }


def enforce_retention(keep_count):
    """Groups backup files by timestamp (a db+lexikon pair created in the
    same run share one) so `keep_count` means "N backup runs", not "N loose
    files" - otherwise a pair would silently count as two against the limit.
    Older single-file backups (before the Lexikon-DB got its own backup)
    have no matching pair and simply form a group of one."""
    groups = {}
    for backup in list_backups():
        match = BACKUP_FILENAME_RE.match(backup["name"])
        key = match.group("timestamp") if match else backup["name"]
        groups.setdefault(key, []).append(backup)

    ordered_keys = sorted(groups, key=lambda k: max(b["created_at"] for b in groups[k]), reverse=True)
    for key in ordered_keys[keep_count:]:
        for backup in groups[key]:
            (BACKUP_DIR / backup["name"]).unlink(missing_ok=True)


def get_backup_path(filename):
    """Resolves filename against BACKUP_DIR and rejects anything that would
    escape it (path traversal via '..' or absolute paths)."""
    path = (BACKUP_DIR / filename).resolve()
    if path.parent != BACKUP_DIR.resolve():
        return None
    return path if path.exists() else None
