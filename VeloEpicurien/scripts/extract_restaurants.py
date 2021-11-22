import os
import sys
import json
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from scripts.generate_cycling_graph import generate_cycling_graph


def extract_restaurants(db, path):
    print('Extracting restaurants...')
    with open(path) as f:
        restaurants = json.load(f)
        db.restaurants.create_index('id', unique=True)
        try:
            db.restaurants.insert_many(restaurants, ordered=False)
            print(f'- Extracted {len(restaurants)} restaurants.')
        except BulkWriteError as e:
            print(f'- Ignored {len(e.details["writeErrors"])} duplicates.')
            print(f'- Extracted {len(restaurants) - len(e.details["writeErrors"])} restaurants.')


def generate_restaurants_view(db):
    print('Generating restaurants view...')
    restaurants = db.restaurants.aggregate([{
        '$project': {
            '_id': False,
            'id': True,
            'name': True,
            'categories': True,
            'geometry': {
                'type': 'Point',
                'coordinates': ['$coordinates.longitude', '$coordinates.latitude']
            }
        }
    }])
    db.restaurants_view.drop()
    db.restaurants_view.insert_many(restaurants)


def generate_types_view(db):
    print('Generating types view...')
    restaurant_types = db.restaurants.aggregate(
        [
            {'$unwind': '$categories'},
            {'$group': {'_id': '$categories.title', 'count': {'$sum': 1}}},
            {'$project': {'title': '$_id', 'count': True, '_id': False}}
        ]
    )
    db.restaurant_types_view.drop()
    db.restaurant_types_view.insert_many(restaurant_types)


def main(path):
    client = MongoClient(os.environ.get('MONGO_URI'))
    db = client.test
    extract_restaurants(db, path)
    generate_restaurants_view(db)
    generate_types_view(db)
    generate_cycling_graph(db)


if __name__ == '__main__':
    main(sys.argv[1])
