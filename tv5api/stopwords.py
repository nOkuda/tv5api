"""The family of /stopwords/ endpoints"""
import json
import os

import flask


bp = flask.Blueprint('stopwords', __name__, url_prefix='/stopwords')


@bp.route('/')
def query_stopwords():
    """Build a stopwords list"""
    return flask.jsonify({})


@bp.route('/lists/')
def query_stopwords_lists():
    """Report curated stopwords lists in database"""
    # TODO
    return flask.jsonify({})


@bp.route('/lists/<name>/')
def get_stopwords_list(name):
    """Retrieve specified stopwords list"""
    # TODO
    return flask.jsonify({})


if os.environ.get('ADMIN_INSTANCE') == 'true':
    @bp.route('/lists/', methods=['POST'])
    def add_stopwords_list():
        # TODO actually implement
        name = 'FIXME'
        data = json.dumps({})
        response = flask.Response()
        response.status_code = 201
        response.status = '201 Created'
        response.headers['Content-Location'] = os.path.join(
            bp.url_prefix, name, '')
        response.set_data(data)
        return response


    @bp.route('/lists/<name>/', methods=['DELETE'])
    def delete_stopwords_list(name):
        # TODO
        return flask.jsonify({})
