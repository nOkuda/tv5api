"""The family of /texts/ endpoints"""
import json
import os
import urllib.parse

import flask

import tv5api.errors
import tesserae.db.entities


bp = flask.Blueprint('texts', __name__, url_prefix='/texts')


@bp.route('/')
def query_texts():
    """Consult database for text metadata"""
    alloweds = {'author', 'is_prose', 'language', 'title'}
    filters = {}
    for allowed in alloweds:
        grabbed = flask.request.args.get(allowed, None)
        if grabbed:
            filters[allowed] = grabbed
    before_val = flask.request.args.get('before', None)
    after_val = flask.request.args.get('after', None)
    try:
        if before_val is not None:
            before_val = int(before_val)
        if after_val is not None:
            after_val = int(after_val)
    except ValueError:
        return tv5api.errors.error(
            400,
            message='If used, "before" and "after" must have integer values.')

    if before_val is not None and after_val is not None:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            year_not=(before_val, after_val),
            **filters)
    elif before_val is not None and after_val is None:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            # Assuming that lower limit pre-dates all texts in database
            year=(-999999999999, before_val),
            **filters)
    elif not before_val is None and after_val is not None:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            # Assuming that upper limit post-dates all texts in database
            year=(after_val, 999999999999),
            **filters)
    else:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            **filters)
    return flask.jsonify(texts=[r.json_encode(exclude=['_id']) for r in results])


@bp.route('/<cts_urn>/')
def get_text(cts_urn):
    """Retrieve specific text's metadata"""
    if cts_urn.count(':') > 3:
        return tv5api.errors.too_specific(301, flask.request.path)
    found = flask.g.db.find(
        tesserae.db.entities.Text.collection,
        cts_urn=cts_urn)
    if not found:
        return tv5api.errors.error(
            404,
            cts_urn=cts_urn,
            message='No text with the provided CTS URN ({}) was found in the database.'.format(cts_urn))
    return flask.jsonify(found[0].json_encode(exclude=['_id']))


@bp.route('/<cts_urn>/units/')
def get_text_units(cts_urn):
    """Retrieve text chunks already in the database for the specified text"""
    # TODO finish
    unit_types = [u for u in flask.request.args]
    result = {}
    found = flask.g.db.find(
        tesserae.db.entities.Text.collection,
        cts_urn=cts_urn)
    if not found:
        return tv5api.errors.error(
            404,
            cts_urn=cts_urn,
            units=unit_types,
            message='No text with the provided CTS URN ({}) was found in the database.'.format(cts_urn))
    text_path = found[0].path
    bad_types = []
    for unit_type in unit_types:
        found = flask.g.db.find(
            tesserae.db.entities.Unit.collection,
            text=text_path,
            unit_type=unit_type)
        if not found:
            bad_types.append(unit_type)
        else:
            result[unit_type] = [f.cts_urn for f in found]
    if bad_types:
        return tv5api.errors.error(
            400,
            cts_urn=cts_urn,
            units=unit_types,
            message='The following unit type(s) could not be found for the specified CTS URN ({}): {}'.format(cts_urn, ', '.join(bad_types)))

    return flask.jsonify(result)


if os.environ.get('ADMIN_INSTANCE') == 'true':
    @bp.route('/', methods=['POST'])
    def add_text():
        received = flask.request.get_json()
        # error checking on request data
        requireds = {'author', 'cts_urn', 'is_prose', 'language', 'path',
                'title', 'year'}
        missing = []
        for req in requireds:
            if req not in received:
                missing.append(req)
        if missing:
            return tv5api.errors.error(
                400,
                data=received,
                message='The request data payload is missing the following required key(s): {}'.format(', '.join(missing)))

        cts_urn = received['cts_urn']
        percent_encoded_cts_urn = urllib.parse.quote(cts_urn)
        if flask.g.db.find(tesserae.db.entities.Text.collection, cts_urn=cts_urn):
            return tv5api.errors.error(
                400,
                data=received,
                message='The CTS URN provided ({}) already exists in the database. If you meant to update the text information, try a PATCH at https://tesserae.caset.buffalo.edu/texts/{}/.'.format(cts_urn, percent_encoded_cts_urn))

        # add text to database
        # TODO type checking here or in library?
        insert_result = flask.g.db.insert(tesserae.db.entities.Text(**received))

        if not insert_result.inserted_ids:
            return tv5api.errors.error(
                500,
                data=received,
                message='Could not add to database')

        response = flask.Response()
        response.status_code = 201
        response.status = '201 Created'
        response.headers['Content-Location'] = os.path.join(
            bp.url_prefix, percent_encoded_cts_urn, '')
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.set_data(flask.json.dumps(received).encode('utf-8'))
        return response


    @bp.route('/<cts_urn>/', methods=['PATCH'])
    def update_text(cts_urn):
        received = flask.request.get_json()
        if cts_urn.count(':') > 3:
            return tv5api.errors.too_specific(308, flask.request.path)
        found = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            cts_urn=cts_urn)
        if not found:
            return tv5api.errors.error(
                404,
                cts_urn=cts_urn,
                data=received,
                message='No text with the provided CTS URN ({}) was found in the database.'.format(cts_urn))

        prohibited = {'_id', 'id', 'cts_urn'}
        problems = []
        for key in prohibited:
            if key in received:
                problems.append(key)
        if problems:
            return tv5api.errors.error(
                400,
                cts_urn=cts_urn,
                data=received,
                message='Prohibited key(s) found in data payload: {}'.format(', '.join(problems)))

        found = found[0]
        found.__dict__.update(received)
        updated = flask.g.db.update(found)
        if updated.matched_count != 1:
            return tv5api.errors.error(
                500,
                cts_urn=cts_urn,
                data=received,
                message='Unexpected number of updates: {}'.format(updated.matched_count))
        return get_text(cts_urn)


    @bp.route('/<cts_urn>/', methods=['DELETE'])
    def delete_text(cts_urn):
        if cts_urn.count(':') > 3:
            return tv5api.errors.too_specific(308, flask.request.path)
        found = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            cts_urn=cts_urn)
        if not found:
            return tv5api.errors.error(
                404,
                cts_urn=cts_urn,
                message='No text with the provided CTS URN ({}) was found in the database.'.format(cts_urn))
        # TODO check for proper deletion?
        flask.g.db.delete(found).deleted_count
        response = flask.Response()
        response.status_code = 204
        response.status = '204 No Content'
        return response
