import os
import markdown
from flask import Blueprint, jsonify, request
from py2neo import Graph
from pymongo import MongoClient
from src.query_builders import build_starting_point_query, build_itinerary_query

JUNCTION = 'Junction'
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
    }), 200


@views.route('/type')
def get_restaurant_types():
    restaurant_types = list(db.restaurant_types_view.distinct('title'))
    return jsonify(restaurant_types), 200


@views.route('/readme')
def get_readme():
    with open('README.md', encoding="utf-8") as f:
        readme = f.read()
        return markdown.markdown(readme, extensions=['fenced_code']), 200


@views.route('/starting_point')
def get_starting_point():
    error = _validate_starting_point_params(request.json)
    if error:
        return error, 400
    length = request.json['length']
    types = request.json['type']
    query = build_starting_point_query(length, types)
    cursor = graph.run(query)
    cursor.forward()
    starting_point = cursor.current['starting_point']
    return jsonify({
        'startingPoint': {
            'type': 'Point',
            'coordinates': [starting_point['long'], starting_point['lat']]
        }
    }), 200


@views.route('/parcours')
def get_itinerary():
    error = _validate_itinerary_params(request.json)
    if error:
        return error, 400
    length = request.json['length']
    if length > _fetch_segments_length():
        return 'Cannot create an itinerary of the provided length', 404
    types = request.json['type']
    if any(t not in _fetch_restaurant_types().keys() for t in types):
        return 'The provided restaurant types were not found', 404
    number_of_stops = request.json['numberOfStops']
    query = build_starting_point_query(length, types)
    cursor = graph.run(query)
    cursor.forward()
    if not cursor.current:
        return 'Could not find a valid itinerary', 404
    query = build_itinerary_query(
        number_of_stops,
        [cursor.current[f'r{i}'].identity for i in range(1, number_of_stops + 1)],
        length
    )
    cursor = graph.run(query)
    cursor.forward()
    return jsonify(_build_itinerary_geojson(cursor.current, number_of_stops, types)), 200


def _build_itinerary_geojson(result, number_of_stops, types):
    features = []
    for i in range(1, number_of_stops):
        features.append(_build_restaurant_geojson(result[f'r{i}'], types))
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'MultiLineString',
                'coordinates': [[[node['long'], node['lat']] for node in result[f'p{i}'].nodes]]
            },
            'properties': {
                'length': result[f'l{i}']
            }
        })
    features.append(_build_restaurant_geojson(result[f'r{number_of_stops}'], types))
    return {'type': 'FeatureCollection', 'features': features}


def _build_restaurant_geojson(restaurant, types):
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [
                restaurant['long'],
                restaurant['lat']
            ]
        },
        'properties': {
            'name': restaurant['name'],
            'type': _get_correct_type(restaurant['types'], types)
        }
    }


def _validate_starting_point_params(json):
    error = ''
    if 'length' not in json:
        error += 'Must include parameter "length"\n'
    elif not (isinstance(json['length'], int) or isinstance(json['length'], float)):
        error += 'Parameter "length" must be a number\n'
    if 'type' not in json:
        error += 'Must include parameter "type"\n'
    else:
        if not (isinstance(json['type'], list)):
            error += 'Parameter "type" must be a list\n'
        if not all(isinstance(t, str) for t in json['type']):
            error += 'Parameter "type" must be a list of strings\n'
    return error


def _validate_itinerary_params(json):
    error = ''
    if not (isinstance(json['startingPoint'], dict)):
        error += 'Parameter "startingPoint" must be a dictionary\n'
    if 'length' not in json:
        error += 'Must include parameter "length"\n'
    elif not (isinstance(json['length'], int) or isinstance(json['length'], float)):
        error += 'Parameter "length" must be a number\n'
    if not (isinstance(json['numberOfStops'], int)):
        error += 'Parameter "numberOfStops" must be an integer\n'
    if 'type' not in json:
        error += 'Must include parameter "type"\n'
    else:
        if not (isinstance(json['type'], list)):
            error += 'Parameter "type" must be a list\n'
        if not all(isinstance(t, str) for t in json['type']):
            error += 'Parameter "type" must be a list of strings\n'
    return error


def _get_correct_type(restaurant_types, wanted_types):
    for restaurant_type in restaurant_types:
        if restaurant_type in wanted_types:
            return restaurant_type
    return restaurant_types[0]


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
