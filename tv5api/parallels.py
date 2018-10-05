"""The family of /parallels/ endpoints"""
import gzip
import os
import uuid

import flask


bp = flask.Blueprint('parallels', __name__, url_prefix='/parallels')


@bp.route('/', methods=('POST',))
def submit_search():
    """Run a Tesserae search"""
    # TODO run search if necessary
    response = flask.Response()
    response.status_code = 201
    response.status = '201 Created'
    results_id = uuid.uuid4().hex
    print(bp.url_prefix)
    print(results_id)
    response.headers['Location'] = os.path.join(bp.url_prefix, results_id)
    return response


@bp.route('/<results_id>/')
def retrieve_results(results_id):
    # TODO get search results
    response = flask.Response(
        response=gzip.compress(flask.json.dumps({
            # This suggests we'll need to store the parameters somewhere;
            # should we expose an endpoint to retrieve this information?
            'data': {},
            'parallels': [],
        }).encode()),
        mimetype='application/json',
    )
    response.status_code = 200
    response.status = '200 OK'
    response.headers['Content-Encoding'] = 'gzip'
    return response
