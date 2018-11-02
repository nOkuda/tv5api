import json
import os
import urllib.parse

import flask
import werkzeug.datastructures

import tesserae.db.entities


def test_query_texts(client):
    response = client.get('/texts/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'texts' in data and isinstance(data['texts'], list)


def test_query_texts_with_fields(app, client):
    year = 1
    lang = 'latin'
    with app.test_request_context():
        endpoint = flask.url_for('texts.query_texts', after=year, language=lang)
    response = client.get(endpoint)
    assert response.status_code == 200
    data = response.get_json()
    assert 'texts' in data and isinstance(data['texts'], list)
    for text in data['texts']:
        assert text['year'] >= year
        assert text['language'] == lang


def test_get_text_units(app, client):
    cts_urn = 'cts:urn:test'
    text_path = '/path/'
    text = tesserae.db.entities.Text(cts_urn=cts_urn, path=text_path)
    # TODO update with new way of identifying cts_urn
    units = [
        tesserae.db.entities.Unit(
            cts_urn=cts_urn+':1.1', text=text_path, unit_type='lines'),
        tesserae.db.entities.Unit(
            cts_urn=cts_urn+':1.2', text=text_path, unit_type='lines'),
        tesserae.db.entities.Unit(
            cts_urn=cts_urn+':1.3', text=text_path, unit_type='lines'),
        tesserae.db.entities.Unit(
            cts_urn=cts_urn+':1.1-1.2@[10]', text=text_path, unit_type='phrases'),
        tesserae.db.entities.Unit(
            cts_urn=cts_urn+':1.2@[11]-1.3', text=text_path, unit_type='phrases'),
    ]

    with app.test_request_context():
        app.preprocess_request()
        endpoint = flask.url_for('texts.get_text_units', cts_urn=cts_urn)
        flask.g.db.insert(text)
        flask.g.db.insert(units)
    response = client.get(endpoint)
    assert not response.get_json()

    with app.test_request_context():
        endpoint = flask.url_for('texts.get_text_units', cts_urn=cts_urn,
                lines='true')
    response = client.get(endpoint)
    data = response.get_json()
    assert 'lines' in data
    assert 'phrases' not in data

    with app.test_request_context():
        endpoint = flask.url_for('texts.get_text_units', cts_urn=cts_urn,
                phrases='true')
    response = client.get(endpoint)
    data = response.get_json()
    assert 'lines' not in data
    assert 'phrases' in data

    with app.test_request_context():
        endpoint = flask.url_for('texts.get_text_units', cts_urn=cts_urn,
                lines='true', phrases='true')
    response = client.get(endpoint)
    data = response.get_json()
    assert 'lines' in data
    assert 'phrases' in data

    with app.test_request_context():
        app.preprocess_request()
        for coll_name in flask.g.db.connection.list_collection_names():
            flask.g.db.connection.drop_collection(coll_name)


if os.environ.get('ADMIN_INSTANCE') == 'true':
    def test_add_and_remove_text(app, client):
        new_cts_urn = 'urn:cts:test'

        before = {
            text['cts_urn']: text
            for text in client.get('/texts/').get_json()['texts']
        }

        # make sure the new text isn't in the database
        with app.test_request_context():
            endpoint = flask.url_for('texts.get_text', cts_urn=new_cts_urn)
        response = client.get(endpoint)
        assert response.status_code == 404

        to_be_added = {
            'author': 'Bob',
            'cts_urn': new_cts_urn,
            'is_prose': False,
            'language': 'english',
            'path': '/bob.txt',
            'title': 'Bob Bob',
            'year': 2018
        }
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            '/texts/',
            data=json.dumps(to_be_added).encode(encoding='utf-8'),
            headers=headers,
        )
        # make sure the response data is correct
        assert response.status_code == 201
        for k, v in response.get_json().items():
            assert k in to_be_added and v == to_be_added[k]

        # make sure the new text is now in the database
        assert client.get(endpoint).get_json()

        # make sure adding doesn't mess up the database
        after_add = {
            text['cts_urn']: text
            for text in client.get('/texts/').get_json()['texts']
        }
        for k, v in after_add.items():
            if k != new_cts_urn:
                assert k in before and v == before[k]

        response = client.delete(endpoint)
        # make sure the new text has been deleted
        assert response.status_code == 204
        response = client.get(endpoint)
        assert response.status_code == 404

        # make sure adding then deleting doesn't mess up the database
        after_delete = {
            text['cts_urn']: text
            for text in client.get('/texts/').get_json()['texts']
        }
        for k, v in after_delete.items():
            assert k in before and v == before[k]


    def test_add_text_already_in_database(client):
        to_be_added = {
            'cts_urn': 'urn:cts:latinLit:phi0472.phi001',
        }

        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            '/texts/',
            data=json.dumps(to_be_added).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'data' in data
        for k, v in data['data'].items():
            assert k in to_be_added and v == to_be_added[k]
        assert 'message' in data


    def test_add_text_insufficient_data(client):
        to_be_added = {
        }

        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            '/texts/',
            data=json.dumps(to_be_added).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'data' in data
        for k, v in data['data'].items():
            assert k in to_be_added and v == to_be_added[k]
        assert 'message' in data


    def test_patch_then_replace_text(app, client):
        new_cts_urn = 'urn:cts:test'
        to_be_added = {
            'author': 'Bob',
            'cts_urn': new_cts_urn,
            'is_prose': False,
            'language': 'english',
            'path': '/bob.txt',
            'title': 'Bob Bob',
            'year': 2018
        }
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            '/texts/',
            data=json.dumps(to_be_added).encode(encoding='utf-8'),
            headers=headers,
        )

        with app.test_request_context():
            endpoint = flask.url_for(
                'texts.get_text',
                cts_urn=new_cts_urn)
        before = client.get(endpoint).get_json()

        patch = {
            'title': 'Pharsalia',
            'extras': {
                'new_key': 'new_value',
            }
        }
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.patch(
            endpoint,
            data=json.dumps(patch).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'title' in data and data['title'] == 'Pharsalia'
        for k, v in data.items():
            if k not in patch:
                assert k in before and before[k] == v

        response = client.delete(endpoint)
        assert response.status_code == 204
        response = client.get(endpoint)
        assert response.status_code == 404

        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            '/texts/',
            data=json.dumps(before).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        for k, v in data.items():
            assert k in before and before[k] == v

        response = client.delete(endpoint)
        assert response.status_code == 204
        response = client.get(endpoint)
        assert response.status_code == 404


    def test_redirects(app, client):
        base_urn = 'urn:cts:latinLit:phi0472.phi001'
        expected_end = urllib.parse.quote_plus(base_urn) + '/'
        specific_urn = base_urn + ':1.1'
        with app.test_request_context():
            endpoint = flask.url_for(
                'texts.get_text',
                cts_urn=specific_urn,
            )
        response = client.get(endpoint)
        assert response.status_code == 301
        assert response.headers['Location'].endswith(expected_end)

        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        patch = {'fail': 'this example will'}
        response = client.patch(
            endpoint,
            data=json.dumps(patch).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 308
        assert response.headers['Location'].endswith(expected_end)

        response = client.delete(
            endpoint,
        )
        assert response.status_code == 308
        assert response.headers['Location'].endswith(expected_end)


    def test_nonexistent_text(app, client):
        nonexistent = 'DEADBEEF'
        with app.test_request_context():
            endpoint = flask.url_for(
                'texts.get_text',
                cts_urn=nonexistent,
            )

        # make sure the text doesn't exist
        response = client.get(endpoint)
        assert response.status_code == 404

        response = client.delete(endpoint)
        assert response.status_code == 404
        data = response.get_json()
        assert 'cts_urn' in data and data['cts_urn'] == nonexistent
        assert 'message' in data

        patch = {'fail': 'this example will'}
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.patch(
            endpoint,
            data=json.dumps(patch).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 404
        data = response.get_json()
        assert 'cts_urn' in data and data['cts_urn'] == nonexistent
        assert 'message' in data
