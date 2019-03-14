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


if os.environ.get('ADMIN_INSTANCE') == 'true':
    def test_add_and_remove_text(app, client):

        before = {
            text['object_id']: text
            for text in client.get('/texts/').get_json()['texts']
        }

        to_be_added = {
            'author': 'Bob',
            'is_prose': False,
            'language': 'latin',
            'path': os.path.join(os.path.dirname(__file__), 'bob.txt'),
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
            if k == 'object_id':
                new_obj_id = v
            else:
                assert k in to_be_added and v == to_be_added[k]

        # make sure the new text isn't in the database
        with app.test_request_context():
            endpoint = flask.url_for('texts.get_text', object_id=new_obj_id)
        # make sure the new text is now in the database
        assert client.get(endpoint).get_json()

        # make sure adding doesn't mess up the database
        after_add = {
            text['object_id']: text
            for text in client.get('/texts/').get_json()['texts']
        }
        for k, v in after_add.items():
            if k != new_obj_id:
                assert k in before and v == before[k]

        response = client.delete(endpoint)
        # make sure the new text has been deleted
        assert response.status_code == 204
        response = client.get(endpoint)
        assert response.status_code == 404

        # make sure adding then deleting doesn't mess up the database
        after_delete = {
            text['object_id']: text
            for text in client.get('/texts/').get_json()['texts']
        }
        for k, v in after_delete.items():
            assert k in before and v == before[k]


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
        to_be_added = {
            'author': 'Bob',
            'is_prose': False,
            'language': 'latin',
            'path': os.path.join(os.path.dirname(__file__), 'bob.txt'),
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
        new_obj_id = response.get_json()['object_id']

        with app.test_request_context():
            endpoint = flask.url_for(
                'texts.get_text',
                object_id=new_obj_id)
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
        assert response.status_code == 400

        del before['object_id']
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
            if k != 'object_id':
                assert k in before and before[k] == v

        with app.test_request_context():
            endpoint = flask.url_for(
                'texts.get_text',
                object_id=data['object_id'])
        response = client.delete(endpoint)
        assert response.status_code == 204
        response = client.get(endpoint)
        assert response.status_code == 404


    def test_nonexistent_text(app, client):
        nonexistent = 'DEADBEEFDEADBEEFDEADBEEF'
        with app.test_request_context():
            endpoint = flask.url_for(
                'texts.get_text',
                object_id=nonexistent,
            )

        # make sure the text doesn't exist
        response = client.get(endpoint)
        assert response.status_code == 404

        response = client.delete(endpoint)
        assert response.status_code == 404
        data = response.get_json()
        assert 'object_id' in data and data['object_id'] == nonexistent
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
        assert 'object_id' in data and data['object_id'] == nonexistent
        assert 'message' in data

    # TODO check for 400 errors when object_ids are bad
