"""Global fixtures for tests"""
import pytest

import tv5api


@pytest.fixture
def app():
    cur_app = tv5api.create_app({
        'MONGO_USER': None,
        'MONGO_PASSWORD': None,
        'DB_NAME': 'tesserae_test',
    })

    with cur_app.app_context():
        # initialize database for testing
        pass

    yield cur_app


@pytest.fixture
def client(app):
    return app.test_client()
