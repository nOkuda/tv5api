import gzip
import json

import flask
import pytest
import werkzeug.datastructures


def test_search(client, app):
    search_submission = {
        'source': ['urn:cts:latinLit:phi0472.phi001:28.14'],
        'target': ['urn:cts:latinLit:phi0690.phi002:1.21'],
        'method': {
            'name': 'original',
            'feature': 'lemma',
            'stopwords': [
                'qui', 'quis', 'sum', 'et', 'in',
                'is', 'non', 'hic', 'ego', 'ut'
            ],
            'freq_basis': 'corpus',
            'max_distance': 10,
            'distance_basis': 'frequency',
        },
    }

    headers = werkzeug.datastructures.Headers()
    headers['Content-Encoding'] = 'gzip'
    response = client.post(
        '/parallels/',
        data=gzip.compress(json.dumps(search_submission).encode()),
        headers=headers,
    )

    print(response.headers['Location'])
    results = client.get(
        response.headers['Location']
    )
    # TODO figure out why this isn't working
    assert results.status_code == 200
