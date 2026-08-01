class AstroRouter:
    """Routes the astro app to its own database file (astro.db), same
    pattern as LexikonRouter - keeps the astrology reference/interpretation
    data separate from the main ERP DB. No real FK constraints across DBs;
    the link to the Heilstein-Lexikon dataset happens via a plain reference
    field resolved in application code (see services/gemstone_lookup.py)."""

    app_label = "astro"

    def db_for_read(self, model, **hints):
        return "astro" if model._meta.app_label == self.app_label else None

    def db_for_write(self, model, **hints):
        return "astro" if model._meta.app_label == self.app_label else None

    def allow_relation(self, obj1, obj2, **hints):
        labels = {self.app_label}
        if obj1._meta.app_label in labels or obj2._meta.app_label in labels:
            return obj1._meta.app_label == obj2._meta.app_label
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return db == "astro"
        return db == "default" if db == "astro" else None
