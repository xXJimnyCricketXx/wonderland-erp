class LexikonRouter:
    """Routes the lexikon app to its own database file, so it stays a
    self-contained, portable dataset. No relations are allowed between it
    and the default DB - cross-referencing happens via name/text queries in
    application code instead."""

    def db_for_read(self, model, **hints):
        if model._meta.app_label == "lexikon":
            return "lexikon"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "lexikon":
            return "lexikon"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        lexikon_labels = {"lexikon"}
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if labels & lexikon_labels:
            return labels == lexikon_labels
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "lexikon":
            return db == "lexikon"
        return db == "default"
