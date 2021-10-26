from flask import Blueprint, jsonify, request
from pymongo import MongoClient

from .import_data import import_restaurants_if_needed

client = MongoClient('mongodb://mongodb:27017')
db = client.test
import_restaurants_if_needed(db)

views = Blueprint('views', __name__)

villeChoisie = {'villeChoisie': "Montreal"}


@views.route("/heartbeat")
def get_json():
    return jsonify(villeChoisie)


@views.route('/restaurants', methods=['GET', 'DELETE'])
def restaurants():
    if request.method == 'GET':
        return jsonify(
            list(db.restaurants.find(projection={"_id": False}))
        ), 200
    elif request.method == 'DELETE':
        db.restaurants.drop()
        return '', 200
