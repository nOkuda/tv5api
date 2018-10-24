"""The family of /texts/ endpoints"""
import json
import os

import flask

import errors
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
    try:
        specials = {
            'before': int(flask.request.args.get('before', None)),
            'after': int(flask.request.args.get('after', None))
        }
    except ValueError:
        return errors.user_error(
            400,
            message='If used, "before" and "after" must have integer values.')

    if specials['before'] and specials['after']:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            year_not=(specials['before'], specials['after']),
            **filters)
    elif specials['before'] and not specials['after']:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            # Assuming that lower limit pre-dates all texts in database
            year=(-999999999999, specials['before']),
            **filters)
    elif not specials['before'] and specials['after']:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            # Assuming that upper limit post-dates all texts in database
            year=(specials['after'], 999999999999),
            **filters)
    else:
        results = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            **filters)
    return flask.jsonify(texts=results)


@bp.route('/<cts_urn>/')
def get_text(cts_urn):
    """Retrieve specific text's metadata"""
    found = flask.g.db.find(
        tesserae.db.entities.Text.collection,
        cts_urn=cts_urn)[0]
    if not found:
        # TODO differentiate from case where CTS URN is overly specific (301)
        return errors.error(
            404,
            cts_urn=cts_urn,
            message='No text with the provided CTS URN ({}) was found in the database.'.format(cts_urn))
    return flask.jsonify(found)


@bp.route('/<cts_urn>/units/')
def get_text_units(cts_urn):
    """Retrieve text chunks already in the database for the specified text"""
    # TODO
    return flask.jsonify({})


if os.environ.get('ADMIN_INSTANCE'):
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
            return errors.user_error(
                400,
                data=received,
                message='The request data payload is missing the following required key(s): {}'.format(', '.join(missing)))

        cts_urn = received['cts_urn']
        percent_encoded_cts_urn = urllib.parse.quote(cts_urn)
        if flask.g.db.find(tesserae.db.entities.Text.collection, cts_urn=cts_urn):
            return errors.user_error(
                400,
                data=received,
                message='The CTS URN provided ({}) already exists in the database. If you meant to update the text information, try a PATCH at https://tesserae.caset.buffalo.edu/texts/{}/.'.format(cts_urn, percent_encoded_cts_urn))

        # add text to database
        # TODO type checking here or in library?
        data = flask.g.db.insert(tesserae.db.entities.Text(**received))

        response = flask.Response()
        response.status_code = 201
        response.status = '201 Created'
        response.headers['Content-Location'] = os.path.join(
            bp.url_prefix, percent_encoded_cts_urn, '')
        response.set_data(data)
        return response


    @bp.route('/<cts_urn>/', methods=['PATCH'])
    def update_text(cts_urn):
        found = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            cts_urn=cts_urn)[0]
        if not found:
            # TODO differentiate from case where CTS URN is overly specific
            # (308)
            return errors.error(
                404,
                cts_urn=cts_urn,
                message='No text with the provided CTS URN ({}) was found in the database.'.format(cts_urn))

        received = flask.request.get_json()
        prohibited = {'_id', 'id', 'cts_urn'}
        problems = []
        for key in prohibited:
            if key in received:
                problems.append(key)
        if problems:
            return errors.user_error(
                400,
                cts_urn=cts_urn,
                data=received,
                message='Prohibited key(s) found in data payload: {}'.format(', '.join(problems)))

        found.update(received)
        updated = flask.g.db.update(found)
        return flask.jsonify(updated)


    @bp.route('/<cts_urn>/', methods=['DELETE'])
    def delete_text(cts_urn):
        found = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            cts_urn=cts_urn)[0]
        if not found:
            # TODO differentiate from case where CTS URN is overly specific
            # (308)
            return errors.error(
                404,
                cts_urn=cts_urn,
                message='No text with the provided CTS URN ({}) was found in the database.'.format(cts_urn))
        # TODO check for proper deletion?
        flask.g.db.delete(found).deleted_count
        response = flask.Response()
        response.status_code = 204
        response.status = '204 No Content'
        return response
