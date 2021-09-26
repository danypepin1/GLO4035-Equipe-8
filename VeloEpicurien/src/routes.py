from flask import Blueprint, jsonify, request
from pymongo import MongoClient

client = MongoClient('mongodb://mongodb:27017')
db = client.test

views = Blueprint('views', __name__)

villeChoisie = {'villeChoisie': "Montreal"}


@views.route("/heartbeat")
def get_json():
    return jsonify(villeChoisie)


@views.route('/cities', methods=['GET', 'POST'])
def cities():
    if request.method == 'POST':
        db.cities.insert_one(request.json)
        return '', 201
    elif request.method == 'GET':
        return jsonify(list(db.cities.find(projection={"_id": 0}))), 200
