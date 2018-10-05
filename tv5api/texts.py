"""The family of /texts/ endpoints"""

import flask


bp = flask.Blueprint('texts', __name__, url_prefix='/texts')


@bp.route('/')
def query_texts():
    """Consult database for text metadata"""
    return flask.jsonify({})
