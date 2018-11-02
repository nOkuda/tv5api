import json
import os

import flask
import werkzeug.datastructures

import tesserae.db.entities


def test_stopwords(client):
    # TODO fill this in
    assert False


def test_stopwords_lists(app, client):
    stopwords_list = tesserae.db.entities.StopwordsList(
        name='test_list',
        stopwords=['a','b'])
    with app.test_request_context():
        app.preprocess_request()
        endpoint = flask.url_for('stopwords.query_stopwords_lists')
        flask.g.db.insert(stopwords_list)

    response = client.get(endpoint)
    assert response.status_code == 200
    data = response.get_json()
    assert 'list_names' in data and isinstance(data['list_names'], list) and data['list_names']

    with app.test_request_context():
        endpoint = flask.url_for('stopwords.get_stopwords_list', name=data['list_names'][0])
    response = client.get(endpoint)
    assert response.status_code == 200
    data = response.get_json()
    assert 'stopwords' in data and isinstance(data['stopwords'], list)

    with app.test_request_context():
        app.preprocess_request()
        for coll_name in flask.g.db.connection.list_collection_names():
            flask.g.db.connection.drop_collection(coll_name)


if os.environ.get('ADMIN_INSTANCE') == 'true':
    def test_add_and_replace_stopwords_list(app, client):
        new_list = 'im-new'
        with app.test_request_context():
            endpoint = flask.url_for('stopwords.get_stopwords_list', name=new_list)
        response = client.get(endpoint)
        assert response.status_code == 404

        for_post1 = {
            'name': new_list,
            'stopwords': ['a', 'b'],
        }
        with app.test_request_context():
            post_endpoint = flask.url_for('stopwords.add_stopwords_list')
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            post_endpoint,
            data=json.dumps(for_post1).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.headers['Content-Location'] == endpoint
        data = response.get_json()
        assert 'stopwords' in data and isinstance(data['stopwords'], list)

        response = client.get(endpoint)
        assert response.status_code == 200

        response = client.delete(endpoint)
        assert response.status_code == 204

        response = client.get(endpoint)
        assert response.status_code == 404

        for_post2 = {
            'name': new_list,
            'stopwords': ['a'],
        }
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            post_endpoint,
            data=json.dumps(for_post2).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.headers['Content-Location'] == endpoint
        data = response.get_json()
        assert 'stopwords' in data and isinstance(data['stopwords'], list)

        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.get_json()
        assert 'stopwords' in data and 'b' not in data['stopwords']

        response = client.delete(endpoint)
        assert response.status_code == 204

        response = client.get(endpoint)
        assert response.status_code == 404


    def test_bad_posts(app, client):
        for_post = {
            'stopwords': ['a', 'b'],
        }
        with app.test_request_context():
            post_endpoint = flask.url_for('stopwords.add_stopwords_list')
        headers = werkzeug.datastructures.Headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        response = client.post(
            post_endpoint,
            data=json.dumps(for_post).encode(encoding='utf-8'),
            headers=headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'data' in data
        for k, v in data['data'].items():
            assert k in for_post and for_post[k] == v


    def test_nonexistent_lists(app, client):
        nonexistent = 'i-dont-exist'
        with app.test_request_context():
            endpoint = flask.url_for('stopwords.get_stopwords_list', name=nonexistent)
        response = client.get(endpoint)
        assert response.status_code == 404
        data = response.get_json()
        assert 'name' in data and data['name'] == nonexistent
        assert 'message' in data

        response = client.delete(endpoint)
        assert response.status_code == 404
        data = response.get_json()
        assert 'name' in data and data['name'] == nonexistent
        assert 'message' in data
