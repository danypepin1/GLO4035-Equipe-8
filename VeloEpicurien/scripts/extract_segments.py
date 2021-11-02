import os
import sys
import json
import hashlib

from pymongo import MongoClient
from pymongo.errors import BulkWriteError


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
        'geometry': True
    })
    db.segments_view.drop()
    db.segments_view.insert_many(segments)
    print('Finished generating segments view.')


def main(path):
    client = MongoClient(os.environ.get('MONGO_URI'))
    db = client.test
    extract_segments(db, path)
    generate_segments_view(db)


if __name__ == '__main__':
    main(sys.argv[1])