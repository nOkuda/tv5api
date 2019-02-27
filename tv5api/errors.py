"""A place for error message code"""
import urllib.parse

import flask


def error(status_code, **kwargs):
    response = flask.jsonify(**kwargs)
    response.status_code = status_code
    return response
