import os
from geopy.distance import distance
from py2neo import Graph, Node, Relationship, Subgraph

BIDIRECTIONAL = 2
CONNECTS_TO = 'connects_to'
POINT = 'Point'
RESTAURANT = 'Restaurant'


def generate_cycling_graph(mongodb):
    if can_generate_cycling_graph(mongodb):
        print('Generating cycling graph...')
        graph = _connect_to_graph()
        graph.delete_all()
        transaction = graph.begin()
        _generate_cycling_graph(mongodb, transaction)
        graph.commit(transaction)
        print('Finished generating cycling graph.')


def can_generate_cycling_graph(mongodb):
    return {'restaurants_view', 'segments_view', 'intersections_view'}.issubset(mongodb.list_collection_names())


def _connect_to_graph():
    return Graph(
        os.environ.get('NEO4J_URI'),
        auth=(os.environ.get('NEO4J_USERNAME'), os.environ.get('NEO4J_PASSWORD')),
        secure=False
    )


def _generate_cycling_graph(mongodb, transaction):
    print('- Building restaurant nodes...')
    restaurants = _build_restaurant_nodes(mongodb)
    print('- Building intersection nodes...')
    intersections = _build_intersection_nodes(mongodb)
    print('- Building restaurant path edges...')
    restaurant_paths = _build_restaurant_path_edges(mongodb, restaurants, intersections)
    print('- Building path edges...')
    paths = _build_path_edges(mongodb, intersections)
    print('- Building subgraph...')
    transaction.create(Subgraph(
        nodes=list(intersections.values()) + restaurants,
        relationships=paths + restaurant_paths
    ))


def _build_restaurant_nodes(mongodb):
    return [
        Node(
            RESTAURANT,
            long=restaurant['geometry']['coordinates'][0],
            lat=restaurant['geometry']['coordinates'][1],
            name=restaurant['name'],
            types=[category['title'] for category in restaurant['categories']]
        )
        for restaurant in mongodb.restaurants_view.find()
    ]


def _build_intersection_nodes(mongodb):
    return {
        str(point): Node(POINT, long=point[0], lat=point[1])
        for segment in mongodb.segments_view.find()
        for point in segment['geometry']['coordinates'][0]
    }


def _build_restaurant_path_edges(mongodb, restaurants, intersections):
    restaurant_paths = []
    for restaurant_node in restaurants:
        intersection_node, length = _find_closest_intersection(mongodb, restaurant_node, intersections)
        restaurant_paths += _build_restaurant_paths(restaurant_node, intersection_node, length)
    return restaurant_paths


def _find_closest_intersection(mongodb, restaurant, intersections):
    closest_intersection = mongodb.intersections_view.aggregate([{
        '$geoNear': {
            'near': {'type': 'Point', 'coordinates': [restaurant['long'], restaurant['lat']]},
            'distanceField': 'distance'
        }},
        {'$limit': 1}
    ]).next()
    coordinates = closest_intersection['geometry']['coordinates']
    return intersections[str([coordinates[0], coordinates[1]])], closest_intersection['distance']


def _build_restaurant_paths(restaurant, intersection, length):
    return [
        Relationship(restaurant, CONNECTS_TO, intersection, length=length),
        Relationship(intersection, CONNECTS_TO, restaurant, length=length)
    ]


def _build_path_edges(mongodb, intersections):
    paths = []
    for segment in mongodb.segments_view.find():
        points = segment['geometry']['coordinates'][0]
        for i in range(len(points) - 1):
            paths.append(_build_path(intersections, points[i], points[i + 1]))
            if segment['properties']['NBR_VOIE'] == BIDIRECTIONAL:
                paths.append(_build_path(intersections, points[i + 1], points[i]))
    return paths


def _build_path(intersections, origin, destination):
    length = distance(
        (origin[1], origin[0]),
        (destination[1], destination[0])
    ).meters
    return Relationship(intersections[str(origin)], CONNECTS_TO, intersections[str(destination)], length=length)
