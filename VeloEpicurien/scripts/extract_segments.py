import os
import sys
import json
import hashlib
from pymongo import MongoClient, GEOSPHERE
from pymongo.errors import BulkWriteError
from scripts.generate_cycling_graph import generate_cycling_graph


def extract_segments(db, path):
    print('Extracting segments...')
    with open(path) as f:
        segments = json.load(f)['features']
        for segment in segments:
            segment['hashcode'] = _encode_string(str(segment['geometry']['coordinates']))
        db.segments.create_index('hashcode', unique=True)
        try:
            db.segments.insert_many(segments, ordered=False)
            print(f'Extracted {len(segments)} segments.')
        except BulkWriteError as e:
            print(f'- Ignored {len(e.details["writeErrors"])} duplicates.')
            print(f'- Extracted {len(segments) - len(e.details["writeErrors"])} segments.')


def _encode_string(input_string):
    return hashlib.sha256(input_string.encode('utf-8')).hexdigest()


def generate_segments_view(db):
    print('Generating segments view...')
    segments = db.segments.find(projection={
        '_id': False,
        'properties.LONGUEUR': True,
        'properties.NBR_VOIE': True,
        'geometry': True
    })
    db.segments_view.drop()
    db.segments_view.create_index([('geometry', GEOSPHERE)])
    db.segments_view.insert_many(segments)


def generate_intersections_view(db):
    print('Generating intersections view...')
    intersections = [
        {'geometry': {'type': 'Point', 'coordinates': point}}
        for segment in db.segments.find(projection={'_id': False, 'geometry': True})
        for point in segment['geometry']['coordinates'][0]
    ]
    db.intersections_view.drop()
    db.intersections_view.create_index([('geometry', GEOSPHERE)])
    db.intersections_view.create_index('geometry.coordinates', unique=True)
    try:
        db.intersections_view.insert_many(intersections, ordered=False)
    except BulkWriteError:
        pass


def main(path):
    client = MongoClient(os.environ.get('MONGO_URI'))
    db = client.test
    extract_segments(db, path)
    generate_segments_view(db)
    generate_intersections_view(db)
    generate_cycling_graph(db)


if __name__ == '__main__':
    main(sys.argv[1])
