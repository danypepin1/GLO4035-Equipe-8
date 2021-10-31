from flask import Blueprint, jsonify, request
from pymongo import MongoClient

from .import_data import import_datasets_if_needed

client = MongoClient('mongodb://mongodb:27017')
db = client.test
import_datasets_if_needed(db)

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


@views.route('/restaurants', methods=['GET', 'DELETE'])
def restaurants():
    if request.method == 'GET':
        return jsonify(
            list(db.restaurants.find(projection={"_id": False}))
        ), 200
    elif request.method == 'DELETE':
        db.restaurants.drop()
        return '', 200


@views.route('/segments', methods=['GET', 'DELETE'])
def segments():
    if request.method == 'GET':
        return jsonify(
            list(db.segments.find(projection={"_id": False}))
        ), 200
    elif request.method == 'DELETE':
        db.segments.drop()
        return '', 200


def transformed_restaurant_data():
    data = list(db.restaurants.aggregate([{'$unwind': '$categories'},
                                          {'$group': {'_id': '$categories.title',
                                                      'count': {'$sum': 1}}},
                                          {'$project': {'type': '$_id', 'count': 1, '_id': 0}}]))
    output = {}
    p = {}
    for d in data:
        p.update({d['type']: d['count']})
    output.update({'restaurants': p})
    return output


@views.route('/transformed_data', methods=['GET', 'DELETE'])
def transformed_data():
    if request.method == 'GET':
        return jsonify(

            transformed_restaurant_data(), {
                'longueurCyclable': list(db.segments.aggregate([{'$group': {'_id': 'null',
                                                                            'total': {'$sum': '$properties.LONGUEUR'}}}]
                                                               ))[0]['total']
            }
        ), 200
    elif request.method == 'DELETE':
        db.transformed_data.drop()
        return '', 200
