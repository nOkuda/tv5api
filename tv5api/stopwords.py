"""The family of /stopwords/ endpoints"""
import json
import os

import flask

import tv5api.errors
import tesserae.db.entities

bp = flask.Blueprint('stopwords', __name__, url_prefix='/stopwords')


@bp.route('/')
def query_stopwords():
    """Build a stopwords list"""
    # TODO
    return flask.jsonify({})


@bp.route('/lists/')
def query_stopwords_lists():
    """Report curated stopwords lists in database"""
    found = flask.g.db.find(
        tesserae.db.entities.StopwordsList.collection
    )
    return flask.jsonify({'list_names': [a.name for a in found]})


@bp.route('/lists/<name>/')
def get_stopwords_list(name):
    """Retrieve specified stopwords list"""
    found = flask.g.db.find(
        tesserae.db.entities.StopwordsList.collection,
        name=name
    )
    if not found:
        return tv5api.errors.error(
            404,
            name=name,
            message='No list with the provided name ({}) was found in the database.'.format(name))
    return flask.jsonify({'name': name, 'stopwords': found[0].stopwords})


if os.environ.get('ADMIN_INSTANCE') == 'true':
    @bp.route('/lists/', methods=['POST'])
    def add_stopwords_list():
        data = flask.request.get_json()
        if 'name' not in data:
            return tv5api.errors.error(
                400,
                data=data,
                message='"name" field missing from request data.')
        if not isinstance(data['name'], str):
            return tv5api.errors.error(
                400,
                data=data,
                message='"name" must be a string.')
        if 'stopwords' not in data:
            return tv5api.errors.error(
                400,
                data=data,
                message='"stopwords" field missing from request data.')
        if not isinstance(data['stopwords'], list):
            return tv5api.errors.error(
                400,
                data=data,
                message='"stopwords" must be a list of strings.')
        for stopword in data['stopwords']:
            if not isinstance(stopword, str):
                return tv5api.errors.error(
                    400,
                    data=data,
                    message='"stopwords" must be a list of strings.')

        name = data['name']

        try:
            found = flask.g.db.insert(
                tesserae.db.entities.StopwordsList(
                    name=data['name'],
                    stopwords=data['stopwords']
                )
            )
        except ValueError as e:
            if 'exists' in e.args[0]:
                return tv5api.errors.error(
                    400,
                    data=data,
                    message='The stopwords list name provided ({0}) already exists in the database. If you meant to update the stopwords list, try a DELETE at https://tesserae.caset.buffalo.edu/texts/{0}/ first, then re-try this POST.'.format(name))
            return tv5api.errors.error(
                500,
                data=data,
                message='Unknown server error'
            )
        response = flask.jsonify({'stopwords': data['stopwords']})
        response.status_code = 201
        response.headers['Content-Location'] = os.path.join(
            flask.request.url_rule.rule, name, '')
        return response


    @bp.route('/lists/<name>/', methods=['DELETE'])
    def delete_stopwords_list(name):
        found = flask.g.db.find(
            tesserae.db.entities.StopwordsList.collection,
            name=name
        )
        if not found:
            return tv5api.errors.error(
                404,
                name=name,
                message='No stopwords list matches the specified name ({}).'.format(name))
        result = flask.g.db.delete(found[0])
        if result.deleted_count != 1:
            return tv5api.errors.error(
                500,
                name=name,
                message='Server error in deleting: deleted {} documents'.format(result.deleted_count)
            )
        response = flask.Response()
        response.status_code = 204
        return response
