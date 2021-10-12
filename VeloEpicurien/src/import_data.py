import json


def import_restaurants_if_needed(db):
    if 'restaurants' in db.list_collection_names():
        print('Restaurants already imported.')
        return

    _import_restaurants(db)


def _import_restaurants(db):
    print('Importing restaurants...')
    with open('./datasets/yelp_mtl_restaurants.json') as f:
        restaurants = json.load(f)
        for restaurant in restaurants:
            db.restaurants.insert_one(restaurant)
        print(f'Imported {len(restaurants)} restaurants.')
