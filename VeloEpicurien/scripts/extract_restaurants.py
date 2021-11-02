import os
import sys
import json

from pymongo import MongoClient


def extract_restaurants(db, path):
    print('Extracting restaurants...')
    with open(path) as f:
        old_docs = db.restaurants.find()
        new_docs = [
            new_doc for new_doc in json.load(f)
            if not any(old_doc for old_doc in old_docs if old_doc['id'] == new_doc['id'])
        ]
        if len(new_docs) > 0:
            db.restaurants.insert_many(new_docs)
        print(f'Extracted {len(new_docs)} restaurants.')


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
    print('Finished generating restaurants view.')


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
    print('Finished generating types view.')


def main(path):
    client = MongoClient(os.environ.get('MONGO_URI'))
    db = client.test
    extract_restaurants(db, path)
    generate_restaurants_view(db)
    generate_types_view(db)


if __name__ == '__main__':
    main(sys.argv[1])
