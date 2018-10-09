"""The family of /texts/ endpoints"""
import json
import os

import flask


bp = flask.Blueprint('texts', __name__, url_prefix='/texts')


@bp.route('/')
def query_texts():
    """Consult database for text metadata"""
    # TODO
    return flask.jsonify({})


@bp.route('/<cts_urn>/')
def get_text(cts_urn):
    """Retrieve specific text's metadata"""
    # TODO
    return flask.jsonify({})


@bp.route('/<cts_urn>/units/')
def get_text_units(cts_urn):
    """Retrieve text chunks already in the database for the specified text"""
    # TODO
    return flask.jsonify({})


if os.environ.get('ADMIN_INSTANCE'):
    @bp.route('/', methods=['POST'])
    def add_text():
        # TODO error checking on request data
        cts_urn = 'TODO CHANGE ME'
        # TODO add text to database
        data = json.dumps({})

        response = flask.Response()
        response.status_code = 201
        response.status = '201 Created'
        response.headers['Content-Location'] = os.path.join(
            bp.url_prefix, cts_urn, '')
        response.set_data(data)
        return response


    @bp.route('/<cts_urn>/', methods=['PATCH'])
    def update_text(cts_urn):
        # TODO
        return flask.jsonify({})


    @bp.route('/<cts_urn>/', methods=['DELETE'])
    def delete_text(cts_urn):
        # TODO
        return flask.jsonify({})
