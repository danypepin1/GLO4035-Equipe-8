import os
from geopy.distance import distance
from py2neo import Graph, Node, Relationship, Subgraph

BIDIRECTIONAL = 2
CONNECTS_TO = 'connects_to'
POINT = 'Point'
RESTAURANT = 'Restaurant'


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
    restaurants = _build_restaurants(mongodb)
    intersections = _build_intersections(mongodb)
    paths = _build_paths(mongodb, intersections)
    transaction.create(Subgraph(nodes=list(intersections.values()) + restaurants, relationships=paths))


def _build_restaurants(mongodb):
    restaurants = []
    for restaurant in mongodb.restaurants_view.find():
        restaurants.append(Node(
            RESTAURANT,
            x=restaurant['geometry']['coordinates'][0],
            y=restaurant['geometry']['coordinates'][1],
            name=restaurant['name'],
            types=[category['title'] for category in restaurant['categories']]
        ))
    return restaurants


def _build_intersections(mongodb):
    intersections = {}
    for segment in mongodb.segments_view.find():
        points = segment['geometry']['coordinates'][0]
        for point in points:
            if str(point) not in intersections:
                intersections[str(point)] = Node(POINT, x=point[0], y=point[1])
    return intersections


def _build_paths(mongodb, intersections):
    paths = []
    for segment in mongodb.segments_view.find():
        points = segment['geometry']['coordinates'][0]
        for i in range(len(points) - 1):
            paths.append(_build_path(intersections, points[i], points[i + 1]))
            if segment['properties']['NBR_VOIE'] == BIDIRECTIONAL:
                paths.append(_build_path(intersections, points[i + 1], points[i]))
    return paths


def _build_path(intersections, origin, destination):
    origin_point = (origin[1], origin[0])
    destination_point = (destination[1], destination[0])
    length = distance(origin_point, destination_point).meters
    return Relationship(intersections[str(origin)], CONNECTS_TO, intersections[str(destination)], length=length)
