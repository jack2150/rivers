# noinspection PyMethodMayBeStatic,PyProtectedMember
class DataRouter(object):
    """
    A router to control all database operations on models in the
    auth application.
    """
    using = 'quote'
    model = ('data', )

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to data_db.
        """
        if model._meta.app_label in self.model:
            return self.using
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to data_db.
        """
        if model._meta.app_label in self.model:
            return self.using
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth app is involved.
        """
        if obj1._meta.app_label in self.model or obj2._meta.app_label in self.model:
            return True
        return None

    def allow_syncdb(self, db, model):
        """
        Make sure the auth app only appears in the self.quote
        database.
        """
        if db == self.using:
            return model._meta.app_label in self.model
        elif model._meta.app_label in self.model:
            return False
        return None