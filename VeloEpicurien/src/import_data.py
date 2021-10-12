import json

RESTAURANTS_DATASET_PATH = './datasets/yelp_mtl_restaurants.json'


def import_restaurants_if_needed(db):
    if 'restaurants' in db.list_collection_names():
        print('Restaurants already imported.')
    else:
        _import_restaurants(db)


def _import_restaurants(db):
    print('Importing restaurants...')
    with open(RESTAURANTS_DATASET_PATH) as f:
        restaurants = json.load(f)
        db.restaurants.insert_many(restaurants)
        print(f'Imported {len(restaurants)} restaurants.')
