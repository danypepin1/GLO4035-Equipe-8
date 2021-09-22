from flask import Blueprint, jsonify

views = Blueprint('views', __name__)

villeChoisie = {'villeChoisie': "Montreal"}


@views.route("/heartbeat")
def get_json():
    return jsonify(villeChoisie)