"""The family of /texts/ endpoints"""
import json
import os
import urllib.parse

from bson.objectid import ObjectId
from bson.errors import InvalidId
import flask

import tv5api.errors
import tesserae.db.entities
import tesserae.utils


bp = flask.Blueprint('texts', __name__, url_prefix='/texts')


def fix_id(entity_json):
    """Replaces entity_json['id'] with entity_json['object_id']

    Note that this updates entity_json in place
    """
    entity_json['object_id'] = entity_json['id']
    del entity_json['id']
    return entity_json


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
    return flask.jsonify(texts=[fix_id(r.json_encode()) for r in results])


@bp.route('/<object_id>/')
def get_text(object_id):
    """Retrieve specific text's metadata"""
    try:
        object_id_obj = ObjectId(object_id)
    except:
        return tv5api.errors.error(
            400,
            object_id=object_id,
            message='Provided identifier ({}) is malformed.'.format(object_id))
    found = flask.g.db.find(
        tesserae.db.entities.Text.collection,
        _id=object_id_obj)
    if not found:
        return tv5api.errors.error(
            404,
            object_id=object_id,
            message='No text with the provided identifier ({}) was found in the database.'.format(object_id))
    result = fix_id(found[0].json_encode())
    return flask.jsonify(result)


if os.environ.get('ADMIN_INSTANCE') == 'true':
    @bp.route('/', methods=['POST'])
    def add_text():
        received = flask.request.get_json()
        # error checking on request data
        requireds = {'author', 'is_prose', 'language', 'path',
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
        prohibiteds = {'_id', 'id', 'object_id'}
        found = []
        for prohib in prohibiteds:
            if prohib in received:
                found.append(prohib)
        if found:
            return tv5api.errors.error(
                400,
                data=received,
                message='The request data payload contains the following prohibited key(s): {}'.format(', '.join(found)))

        try:
            # add text to database
            insert_id = tesserae.utils.ingest_text(
                flask.g.db, tesserae.db.entities.Text(**received))
        except Exception as e:
            return tv5api.errors.error(
                500,
                data=received,
                message='Could not add to database: {}'.format(e))

        object_id = str(insert_id)
        received['object_id'] = object_id
        percent_encoded_object_id = urllib.parse.quote(object_id)

        response = flask.Response()
        response.status_code = 201
        response.status = '201 Created'
        response.headers['Content-Location'] = os.path.join(
            bp.url_prefix, percent_encoded_object_id, '')
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.set_data(flask.json.dumps(received).encode('utf-8'))
        return response


    @bp.route('/<object_id>/', methods=['PATCH'])
    def update_text(object_id):
        try:
            object_id_obj = ObjectId(object_id)
        except:
            return tv5api.errors.error(
                400,
                object_id=object_id,
                message='Provided identifier ({}) is malformed.'.format(object_id))
        received = flask.request.get_json()
        found = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            _id=object_id_obj)
        if not found:
            return tv5api.errors.error(
                404,
                object_id=object_id,
                data=received,
                message='No text with the provided identifier ({}) was found in the database.'.format(object_id))

        prohibited = {'_id', 'id', 'object_id'}
        problems = []
        for key in prohibited:
            if key in received:
                problems.append(key)
        if problems:
            return tv5api.errors.error(
                400,
                object_id=object_id,
                data=received,
                message='Prohibited key(s) found in data payload: {}'.format(', '.join(problems)))

        found = found[0]
        found.__dict__.update(received)
        updated = flask.g.db.update(found)
        if updated.matched_count != 1:
            return tv5api.errors.error(
                500,
                object_id=object_id,
                data=received,
                message='Unexpected number of updates: {}'.format(updated.matched_count))
        return get_text(object_id)


    @bp.route('/<object_id>/', methods=['DELETE'])
    def delete_text(object_id):
        try:
            object_id_obj = ObjectId(object_id)
        except:
            return tv5api.errors.error(
                400,
                object_id=object_id,
                message='Provided identifier ({}) is malformed.'.format(object_id))
        found = flask.g.db.find(
            tesserae.db.entities.Text.collection,
            _id=object_id_obj)
        if not found:
            return tv5api.errors.error(
                404,
                object_id=object_id,
                message='No text with the provided identifier ({}) was found in the database.'.format(object_id))
        # TODO check for proper deletion?
        flask.g.db.delete(found).deleted_count
        response = flask.Response()
        response.status_code = 204
        response.status = '204 No Content'
        return response
