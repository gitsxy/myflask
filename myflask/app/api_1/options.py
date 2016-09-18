from flask import jsonify, request, current_app, url_for
from . import api
from ..models import Item,Option


@api.route('/items/<int:id>/timeline/')
def get_item_options(id):
    item = Item.query.get_or_404(id)
    options = item.options.order_by(Option.id.asc())
    return jsonify({
        'options': [option.to_json() for option in options],
    })
