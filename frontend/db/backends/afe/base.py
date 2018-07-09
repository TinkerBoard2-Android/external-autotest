import time

from django.db.backends.mysql.base import DatabaseCreation as MySQLCreation
from django.db.backends.mysql.base import DatabaseOperations as MySQLOperations
from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
from django.db.backends.mysql.base import DatabaseIntrospection as MySQLIntrospection

try:
    import MySQLdb as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading MySQLdb module: %s" % e)


class DatabaseOperations(MySQLOperations):
    """Custom database backend wrapper."""
    compiler_module = "autotest_lib.frontend.db.backends.afe.compiler"


class DatabaseWrapper(MySQLDatabaseWrapper):
    """Custom database backend wrapper."""

    def __init__(self, *args, **kwargs):
        self.connection = None
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = MySQLCreation(self)
        try:
            self.ops = DatabaseOperations()
        except TypeError:
            self.ops = DatabaseOperations(connection=kwargs.get('connection'))
        self.introspection = MySQLIntrospection(self)

    def _valid_connection(self):
        if self.connection is not None:
            if self.connection.open:
                try:
                    self.connection.ping()
                    return True
                except Database.DatabaseError:
                    self.connection.close()
                    self.connection = None
        return False

    def _cursor(self):
        # crbug.com/805724 Add a retry for connection errors.
        try:
            return super(DatabaseWrapper, self)._cursor()
        except Database.OperationalError:
            time.sleep(0.3)
            return super(DatabaseWrapper, self)._cursor()
