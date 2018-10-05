"""The family of /stopwords/ endpoints"""

import flask


bp = flask.Blueprint('stopwords', __name__, url_prefix='/stopwords')


@bp.route('/')
def query_stopwords():
    """Build a stopwords list"""
    return flask.jsonify({})

