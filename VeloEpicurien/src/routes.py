import os
from flask import Blueprint, jsonify, request
from py2neo import Graph
from pymongo import MongoClient

DEFAULT_NB_STOPS = 10
CHOSEN_CITY = {'villeChoisie': "Montreal"}

client = MongoClient(os.environ.get('MONGO_URI'))
db = client.test
graph = Graph(
    os.environ.get('NEO4J_URI'),
    auth=(os.environ.get('NEO4J_USERNAME'), os.environ.get('NEO4J_PASSWORD')),
    secure=False
)

views = Blueprint('views', __name__)


@views.route("/heartbeat")
def city():
    return jsonify(CHOSEN_CITY)


@views.route('/extracted_data')
def extracted_data():
    return jsonify({
        'nbRestaurants': db.restaurants_view.find().count(),
        'nbSegments': db.segments_view.find().count()
    })


@views.route('/transformed_data')
def transformed_data():
    return jsonify({
        'restaurants': _fetch_restaurant_types(),
        'longueurCyclable': _fetch_segments_length()
    }
    ), 200


@views.route('/type')
def get_restaurant_types():
    restaurant_types = list(db.restaurant_types_view.distinct('title'))
    return jsonify(restaurant_types), 200


@views.route('/starting_point')
def get_starting_point():
    query = _build_starting_point_query(
        request.json['length'],
        request.json['type']
    )
    starting_point = graph.evaluate(query)
    return jsonify({
        'startingPoint': {
            'type': 'Point',
            'coordinates': [starting_point['long'], starting_point['lat']]
        }
    }), 200


def _fetch_restaurant_types():
    restaurant_types = list(db.restaurant_types_view.find())
    formatted_restaurant_types = {}
    for restaurant_type in restaurant_types:
        formatted_restaurant_types[restaurant_type['title']] = restaurant_type['count']
    return formatted_restaurant_types


def _fetch_segments_length():
    cursor = list(db.segments_view.aggregate([
        {'$group': {'_id': 'null', 'total': {'$sum': '$properties.LONGUEUR'}}}
    ]))
    if len(cursor) > 0:
        return 0. + cursor[0]['total']
    else:
        return 0.


def _build_starting_point_query(length, types):
    query = 'MATCH p=((starting_point:Junction)-[c1:connects_to]->(r1:Restaurant)'
    for i in range(2, DEFAULT_NB_STOPS + 1):
        query += f'-[c{i}:shortest_path_to]->(r{i}:Restaurant)'
    query += ')\n'

    query += 'WHERE c1.length'
    for i in range(2, DEFAULT_NB_STOPS + 1):
        query += f' + c{i}.total_length'
    query += f' < {length * 1.1}\n'

    for i in range(1, DEFAULT_NB_STOPS):
        for j in range(i + 1, DEFAULT_NB_STOPS + 1):
            query += f'AND r{i}.name <> r{j}.name '
        query += '\n'

    if len(types) > 0:
        query += f'AND ANY(r IN [r1'
        for i in range(2, DEFAULT_NB_STOPS + 1):
            query += f', r{i}'
        query += f'] WHERE ANY(type in {str(types)} WHERE type in r.types))\n'

    query += 'RETURN starting_point LIMIT 1'

    print(f'[QUERY]\n{query}')
    return query
