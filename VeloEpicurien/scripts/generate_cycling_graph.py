import os
from string import ascii_uppercase

from geopy.distance import distance
from py2neo import Graph, Node, Relationship, Subgraph

CONNECTS_TO = 'connects_to'
JUNCTION = 'Junction'
RESTAURANT = 'Restaurant'
WALKING_DISTANCE = 400


def generate_cycling_graph(mongodb):
    if can_generate_cycling_graph(mongodb):
        print('Generating cycling graph...')
        graph = _connect_to_graph()
        graph.delete_all()
        transaction = graph.begin()
        _generate_cycling_graph(mongodb, transaction)
        graph.commit(transaction)
        print('- Creating shortest path edges...')
        _build_shortest_path_edges(graph)
        print('Finished generating cycling graph.')


def can_generate_cycling_graph(mongodb):
    return {'restaurants_view', 'segments_view', 'junctions_view'}.issubset(mongodb.list_collection_names())


def _connect_to_graph():
    return Graph(
        os.environ.get('NEO4J_URI'),
        auth=(os.environ.get('NEO4J_USERNAME'), os.environ.get('NEO4J_PASSWORD')),
        secure=False
    )


def _generate_cycling_graph(mongodb, transaction):
    print('- Building restaurant nodes...')
    restaurants = _build_restaurant_nodes(mongodb)
    print('- Building junction nodes...')
    junctions = _build_junction_nodes(mongodb)
    print('- Building restaurant path edges...')
    restaurant_paths = _build_restaurant_path_edges(mongodb, restaurants, junctions)
    print('- Building path edges...')
    paths = _build_path_edges(mongodb, junctions)
    print('- Creating subgraph...')
    transaction.create(Subgraph(
        nodes=list(junctions.values()) + restaurants,
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


def _build_junction_nodes(mongodb):
    return {
        str(point): Node(JUNCTION, long=point[0], lat=point[1])
        for segment in mongodb.segments_view.find()
        for point in segment['geometry']['coordinates'][0]
    }


def _build_restaurant_path_edges(mongodb, restaurants, junctions):
    restaurant_paths = []
    for restaurant_node in restaurants:
        junction_node, length = _find_closest_junction(mongodb, restaurant_node, junctions)
        if length < WALKING_DISTANCE:
            restaurant_paths += _build_restaurant_paths(restaurant_node, junction_node)
    return restaurant_paths


def _find_closest_junction(mongodb, restaurant, junctions):
    closest_junction = mongodb.junctions_view.aggregate([{
        '$geoNear': {
            'near': {'type': 'Point', 'coordinates': [restaurant['long'], restaurant['lat']]},
            'distanceField': 'distance'
        }},
        {'$limit': 1}
    ]).next()
    coordinates = closest_junction['geometry']['coordinates']
    return junctions[str([coordinates[0], coordinates[1]])], closest_junction['distance']


def _build_restaurant_paths(restaurant, junction):
    return [
        Relationship(restaurant, CONNECTS_TO, junction, length=0),
        Relationship(junction, CONNECTS_TO, restaurant, length=0)
    ]


def _build_path_edges(mongodb, junctions):
    paths = []
    for segment in mongodb.segments_view.find():
        points = segment['geometry']['coordinates'][0]
        for i in range(len(points) - 1):
            paths.append(_build_path(junctions, points[i], points[i + 1]))
            paths.append(_build_path(junctions, points[i + 1], points[i]))
    return paths


def _build_path(junctions, origin, destination):
    length = distance(
        (origin[1], origin[0]),
        (destination[1], destination[0])
    ).meters
    return Relationship(junctions[str(origin)], CONNECTS_TO, junctions[str(destination)], length=length)


def _build_shortest_path_edges(graph):
    for char in ascii_uppercase:
        graph.evaluate(
            f"""
            MATCH p=shortestPath((r1:Restaurant)-[:connects_to*..20]->(r2:Restaurant))
            WHERE r1.name > r2.name
            AND r1.name STARTS WITH '{char}'
            WITH r1, r2, reduce(acc=0, r IN relationships(p) | acc + coalesce(r.length, 0)) AS len
            MERGE (r1)-[:shortest_path_to {{total_length: len}}]->(r2)
            MERGE (r2)-[:shortest_path_to {{total_length: len}}]->(r1)
            RETURN count(*)
            """
        )
