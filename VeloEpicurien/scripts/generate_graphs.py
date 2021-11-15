import os
from py2neo import Graph, Node, Relationship
from pymongo import MongoClient

URL = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "supersecret"


def generate_segment_nodes():
    mongo_client = MongoClient(os.environ.get('MONGO_URI'))
    db = mongo_client.test
    graph = Graph(URL, auth=(USERNAME, PASSWORD), secure=False)
    transaction = graph.begin()

    segments = db.segments_view.find(projection={'_id': False})

    nodes_per_point = {}
    for segment in segments:
        node = Node('Segment', length=segment['properties']['LONGUEUR'])
        for point in segment['geometry']['coordinates'][0]:
            if str(point) in nodes_per_point:
                nodes_per_point[str(point)].append(node)
            else:
                nodes_per_point[str(point)] = [node]
        transaction.create(node)
    print('A')
    for node_list in nodes_per_point.values():
        for i in range(len(node_list)):
            for j in range(len(node_list)):
                if i != j:
                    transaction.create(Relationship(
                        node_list[i],
                        'connects_to',
                        node_list[j]
                    ))
    print('B')
    graph.commit(transaction)


if __name__ == '__main__':
    generate_segment_nodes()
