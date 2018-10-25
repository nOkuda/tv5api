"""Global fixtures for tests"""
import pytest

import flask

import tv5api


@pytest.fixture(scope='session')
def app():
    cur_app = tv5api.create_app({
        'MONGO_HOSTNAME': 'localhost',
        'MONGO_PORT': 27017,
        'MONGO_USER': None,
        'MONGO_PASSWORD': None,
        'DB_NAME': 'test_tv5api',
    })

    with cur_app.test_request_context():
        # initialize database for testing
        cur_app.preprocess_request()
        for coll_name in flask.g.db.connection.list_collection_names():
            flask.g.db.connection.drop_collection(coll_name)

    yield cur_app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()
