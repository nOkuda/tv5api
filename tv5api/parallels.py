"""The family of /parallels/ endpoints"""
import gzip
import os
import uuid

from bson.objectid import ObjectId
import flask

import tesserae.db.entities
from tesserae.matchers import AggregationMatcher
import tv5api.errors

bp = flask.Blueprint('parallels', __name__, url_prefix='/parallels')


def _validate_units(specs, name):
    """Provide error messages if units are not specified correctly

    Parameters
    ----------
    specs : dict
        specification of which units from what text
    name : str
        either 'source' or 'target'

    Returns
    -------
    list of str
        error messages corresponding to errors encountered
    """
    result = []
    if 'object_id' not in specs:
        result.append('{} is missing object_id.'.format(name))
    if 'units' not in specs:
        result.append('{} is missing units.'.format(name))
    else:
        units = specs['units']
        if units != 'line' and units != 'phrase':
            result.append('{} has unrecognized units: {}'.format(name, units))
    return result


def _queue_search(results_id, connection, received):
    """Queue up search for processing"""
    matcher = AggregationMatcher(connection)
    received_method = received['method']
    matches, match_set = matcher.match(
        texts=[received['source']['object_id'], received['target']['object_id']],
        unit_type=[received['source']['units'], received['target']['units']],
        feature=received_method['feature'],
        stopwords_list=received_method['stopwords'],
        frequency_basis=received_method['freq_basis'],
        max_distance=received_method['max_distance'],
        distance_metric=received_method['distance_basis']
    )
    results_pair = tesserae.db.entities.ResultsPair(match_set_id=match_set.id,
            results_id=results_id)
    connection.insert(results_pair)


@bp.route('/', methods=('POST',))
def submit_search():
    """Run a Tesserae search"""
    received = flask.request.get_json()
    requireds = {'source', 'target', 'method'}
    missing = []
    for req in requireds:
        if req not in received:
            missing.append(req)
    if missing:
        return tv5api.errors.error(
            400,
            data=received,
            message='The request data payload is missing the following required key(s): {}'.format(', '.join(missing)))

    source = received['source']
    target = received['target']

    errors = _validate_units(source, 'source')
    errors.extend(_validate_units(target, 'target'))
    if errors:
        return tv5api.errors.error(
            400,
            data=received,
            message='The following errors were found in source and target unit specifications:\n{}'.format('\n\t'.join(errors)))

    method_requireds = {
        'original': {
            'name', 'feature', 'stopwords', 'freq_basis', 'max_distance',
            'distance_basis'
        }
    }
    method = received['method']
    if 'name' not in method:
        return tv5api.errors.error(
            400,
            data=received,
            message='No specified method name.')
    missing = []
    for req in method_requireds[method['name']]:
        if req not in method:
            missing.append(req)
    if missing:
        return tv5api.errors.error(
            400,
            data=received,
            message='The specified method is missing the following required key(s): {}'.format(', '.join(missing)))

    response = flask.Response()
    response.status_code = 201
    response.status = '201 Created'
    results_id = uuid.uuid4().hex
    # we want the final '/' on the URL
    response.headers['Location'] = os.path.join(bp.url_prefix, results_id, '')

    _queue_search(results_id, flask.g.db, received)
    return response


@bp.route('/<results_id>/')
def retrieve_results(results_id):
    # get search results
    found = flask.g.db.find(
        tesserae.db.entities.ResultsPair.collection,
        results_id=results_id
    )
    if not found:
        response = flask.Response()
        response.status_code = 404
        return response
    params = found[0].parameters

    found = flask.g.db.find(
        tesserae.db.entities.MatchSet.collection,
        _id=ObjectId(found[0]['match_set_id'])
    )
    if not found:
        response = flask.Response()
        response.status_code = 404
        return response

    matches = flask.g.db.get_search_matches(found[0].id)
    response = flask.Response(
        response=gzip.compress(flask.json.dumps({
            'data': params,
            'parallels': matches
        }).encode()),
        mimetype='application/json',
    )
    response.status_code = 200
    response.status = '200 OK'
    response.headers['Content-Encoding'] = 'gzip'
    return response
