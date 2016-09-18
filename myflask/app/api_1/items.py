from flask import jsonify, request, g, abort, url_for, current_app
from .. import db
from ..models import Item, Permission
from . import api
from .decorators import permission_required
from .errors import forbidden


@api.route('/items/')
def get_items():
    page = request.args.get('page', 1, type=int)
    pagination = Item.query.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    items = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_items', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_items', page=page+1, _external=True)
    return jsonify({
        'posts': [item.to_json() for item in items],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/items/<int:id>')
def get_item(id):
    item = Item.query.get_or_404(id)
    return jsonify(item.to_json())


@api.route('/items/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_item():
    item = Item.from_json(request.json)
    item.author = g.current_user
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_json()), 201, \
        {'Location': url_for('api.get_item', id=item.id, _external=True)}


@api.route('/items/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_item(id):
    item = Item.query.get_or_404(id)
    if g.current_user != item.author and \
            not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Insufficient permissions')
    item.body = request.json.get('body', item.body)
    db.session.add(item)
    return jsonify(item.to_json())
