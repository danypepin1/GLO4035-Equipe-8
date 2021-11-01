from flask import Blueprint, jsonify
from pymongo import MongoClient

client = MongoClient('mongodb://mongodb:27017')
db = client.test

views = Blueprint('views', __name__)

chosenCity = {'villeChoisie': "Montreal"}


@views.route("/heartbeat")
def city():
    return jsonify(chosenCity)


@views.route('/extracted_data')
def extracted_data():
    return jsonify({
        'nbRestaurants': db.restaurants.find().count(),
        'nbSegments': db.segments.find().count()
    })


@views.route('/restaurants')
def restaurants():
    return jsonify(
        list(db.restaurants.find(projection={"_id": False}))
    ), 200


@views.route('/segments')
def segments():
    return jsonify(
        list(db.segments.find(projection={"_id": False}))
    ), 200


@views.route('/transformed_data')
def transformed_data():
    return jsonify({
            'restaurants': _fetch_restaurant_types(),
            'longueurCyclable': _fetch_segments_length()
        }
    ), 200


def _fetch_restaurant_types():
    restaurant_types = list(db.restaurant_types_view.find())
    formatted_restaurant_types = {}
    for restaurant_type in restaurant_types:
        formatted_restaurant_types[restaurant_type['title']] = restaurant_type['count']
    return formatted_restaurant_types


def _fetch_segments_length():
    cursor = list(db.segments.aggregate([
            {'$group': {'_id': 'null', 'total': {'$sum': '$properties.LONGUEUR'}}}
    ]))
    if len(cursor) > 0:
        return 0. + cursor[0]['total']
    else:
        return 0.
