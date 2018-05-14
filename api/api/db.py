from pymongo import MongoClient
from urllib.parse import urlparse


def includeme(config):
    settings = config.registry.settings

    db_url = urlparse(settings['mongo_uri'])
    config.registry.db = MongoClient(
        host=db_url.hostname,
        port=db_url.port
    )

    def add_db(request):
        db = config.registry.db[db_url.path[1:]]
        if db_url.username and db_url.password:
            db.authenticate(db_url.username, db_url.password)
        return db

    config.add_request_method(add_db, 'db', reify=True)
