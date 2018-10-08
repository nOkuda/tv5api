import json
import os

import werkzeug.datastructures


def test_query_texts(client):
    response = client.get('/texts/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'texts' in data and isinstance(data['texts'], list)


def test_query_texts_with_fields(app, client):
    year = 1
    lang = 'latin'
    with app.test_request_context():
        endpoint = flask.url_for('texts', after=year, language=lang)
    response = client.get(endpoint)
    assert response.status_code == 200
    data = response.get_json()
    assert 'texts' in data and isinstance(data['texts'], list)
    for text in data['texts']:
        assert text['year'] >= year
        assert text['language'] == lang


if os.environ.get('ADMIN_INSTANCE'):
    def test_add_and_remove_text(client):
        new_cts_urn = 'urn:cts:test'

        before = {
            text['cts_urn']: text
            for text in client.get('/texts/').get_json()['texts']
        }

        # make sure the new text isn't in the database
        with app.test_request_context():
            endpoint = flask.url_for('texts', cts_urn=new_cts_urn)
        assert not client.get(endpoint).get_json()

        to_be_added = {
            'cts_urn': new_cts_urn,
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
        response = client.get(endpoint).get_json()
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
        with app.test_request_context():
            endpoint = flask.url_for(
                'texts',
                cts_urn='urn:cts:latinLit:phi0472.phi001')
        before = client.get(endpoint).get_json()

        patch = {
            'new_key': 'new_value',
            'title': 'Pharsalia',
        }
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.patch(
            endpoint,
            data=json.dumps(patch).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code = 200
        data = response.get_json()
        assert 'new_key' in data and data['new_key'] == 'new_value'
        assert 'title' in data and data['title'] == 'Pharsalia'
        for k, v in data.items():
            if k not in patch:
                assert k in before and before[k] == v

        response = client.delete(endpoint)
        assert response.status_code == 204
        response = client.get(endpoint).get_json()
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


    def test_redirects(app, client):
        base_urn = 'urn:cts:latinLit:phi0472.phi001'
        specific_urn = base_urn + ':1.1'
        with app.test_request_context():
            base_endpoint = flask.url_for(
                'texts',
                cts_urn=base_urn,
            )
            endpoint = flask.url_for(
                'texts',
                cts_urn=specific_urn,
            )
        response = client.get(endpoint)
        assert response.status_code == 301
        assert response.headers['Location'].endswith(base_endpoint)

        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.patch(
            endpoint,
            data=json.dumps(patch).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 308
        assert response.headers['Location'].endswith(base_endpoint)

        response = client.delete(
            endpoint,
        )
        assert response.status_code == 308
        assert response.headers['Location'].endswith(base_endpoint)


    def test_nonexistent_text(app, client):
        nonexistent = 'DEADBEEF'
        with app.test_request_context():
            endpoint = flask.url_for(
                'texts',
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
