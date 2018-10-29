"""A place for error message code"""
import urllib.parse

import flask


def error(status_code, **kwargs):
    response = flask.jsonify(**kwargs)
    response.status_code = status_code
    return response


def too_specific(status_code, path):
    response = flask.Response()
    response.status_code = status_code
    pos = path.find(':', 0)
    for _ in range(3):
        pos = path.find(':', pos+1)
    if pos == -1:
        raise ValueError('Could not find 4th ":" in "{}"'.format(path))
    response.headers['Location'] = '/'.join(
        [urllib.parse.quote_plus(a) for a in path[:pos].split('/')])
    if response.headers['Location'][-1] != '/':
        response.headers['Location'] += '/'
    print(response.headers['Location'])
    return response
