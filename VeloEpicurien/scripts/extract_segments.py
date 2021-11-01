import os
import sys
import json

from pymongo import MongoClient


def extract_segments(db, path):
    print('Extracting segments...')
    with open(path) as f:
        segments = json.load(f)['features']
        db.segments.insert_many(segments)
        print(f'Extracted {len(segments)} segments.')


def generate_segments_view(db):
    print('Generating segments view...')
    segments = db.segments.find(project={
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
