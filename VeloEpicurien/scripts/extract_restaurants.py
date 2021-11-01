from pymongo import MongoClient
import sys
import json


def extract_restaurants(db, path):
    print('Extracting restaurants...')
    with open(path) as f:
        restaurants = json.load(f)
        db.restaurants.insert_many(restaurants)
        print(f'Extracted {len(restaurants)} restaurants.')


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
    client = MongoClient('mongodb://mongodb:27017')
    db = client.test
    extract_restaurants(db, path)
    generate_types_view(db)


if __name__ == '__main__':
    main(sys.argv[1])
