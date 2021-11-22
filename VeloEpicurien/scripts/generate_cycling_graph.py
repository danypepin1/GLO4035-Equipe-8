import os
from geopy.distance import distance
from py2neo import Graph, Node, Relationship, Subgraph

BIDIRECTIONAL = 2
CONNECTS_TO = 'connects_to'
POINT = 'Point'


def generate_cycling_graph(mongodb):
    print('Generating cycling graph...')
    graph = _connect_to_graph()
    graph.delete_all()
    transaction = graph.begin()
    _generate_cycling_graph(mongodb, transaction)
    graph.commit(transaction)
    print('Finished generating cycling graph.')


def _connect_to_graph():
    return Graph(
        os.environ.get('NEO4J_URI'),
        auth=(os.environ.get('NEO4J_USERNAME'), os.environ.get('NEO4J_PASSWORD')),
        secure=False
    )


def _generate_cycling_graph(mongodb, transaction):
    nodes = _build_nodes(mongodb)
    edges = _build_edges(mongodb, nodes)
    transaction.create(Subgraph(nodes=nodes.values(), relationships=edges))


def _build_nodes(mongodb):
    nodes = {}
    for segment in mongodb.segments_view.find(projection={'_id': False}):
        points = segment['geometry']['coordinates'][0]
        for point in points:
            if str(point) not in nodes:
                nodes[str(point)] = Node(POINT, x=point[0], y=point[1])
    return nodes


def _build_edges(mongodb, nodes):
    edges = []
    for segment in mongodb.segments_view.find(projection={'_id': False}):
        points = segment['geometry']['coordinates'][0]
        for i in range(len(points) - 1):
            edges.append(_build_edge(nodes, points[i], points[i + 1]))
            if segment['properties']['NBR_VOIE'] == BIDIRECTIONAL:
                edges.append(_build_edge(nodes, points[i + 1], points[i]))
    return edges


def _build_edge(nodes, origin, destination):
    origin_point = (origin[1], origin[0])
    destination_point = (destination[1], destination[0])
    length = distance(origin_point, destination_point).meters
    return Relationship(nodes[str(origin)], CONNECTS_TO, nodes[str(destination)], length=length)
