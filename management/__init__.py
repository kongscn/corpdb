from south.signals import post_migrate

from corpdb.utils.initdb import init_db


def migration_callback(**kwargs):
    if kwargs['app'] == 'ypl':
        init_db()


post_migrate.connect(migration_callback)
