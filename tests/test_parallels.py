import gzip
import json

import flask
import pytest
import werkzeug.datastructures


def test_search(client):
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
    headers['Content-Type'] = 'application/json; charset=utf-8'
    headers['Content-Encoding'] = 'gzip'
    response = client.post(
        '/parallels/',
        data=gzip.compress(json.dumps(search_submission).encode(encoding='utf-8')),
        headers=headers,
    )

    results = client.get(
        response.headers['Location']
    )
    assert results.status_code == 200
