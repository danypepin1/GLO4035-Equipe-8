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
            print(f'Ignored {len(e.details["writeErrors"])} duplicates.')
            print(f'Extracted {len(segments) - len(e.details["writeErrors"])} segments.')


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
    print('Finished generating segments view.')


def main(path):
    client = MongoClient(os.environ.get('MONGO_URI'))
    db = client.test
    extract_segments(db, path)
    generate_segments_view(db)
    generate_cycling_graph(db)


if __name__ == '__main__':
    main(sys.argv[1])
