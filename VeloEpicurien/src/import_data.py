import json

RESTAURANTS_DATASET_PATH = './datasets/yelp_mtl_restaurants.json'
SEGMENTS_DATASET_PATH = './datasets/reseau_cyclable.geojson'


def import_datasets_if_needed(db):
    import_restaurants_if_needed(db)
    import_segments_if_needed(db)


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


def import_segments_if_needed(db):
    if 'segments' in db.list_collection_names():
        print('Segments already imported.')
    else:
        _import_segments(db)


def _import_segments(db):
    print('Importing segments...')
    with open(SEGMENTS_DATASET_PATH) as f:
        segments = json.load(f)
        db.segments.insert_many(segments["features"])
        print(f'Imported {len(segments["features"])} segments.')
