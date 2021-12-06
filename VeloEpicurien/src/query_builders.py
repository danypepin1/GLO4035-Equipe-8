DEFAULT_NB_STOPS = 10


def build_starting_point_query(length, types):
    query = 'MATCH (r1:Restaurant)\n'
    if len(types) > 0:
        query += f'WHERE ANY(type in {str(types)} WHERE type in r1.types)\n'

    query += 'MATCH p=((starting_point:Junction)-->(r1)'
    for i in range(2, DEFAULT_NB_STOPS + 1):
        query += f'-[p{i-1}:shortest_path_to]->(r{i}:Restaurant)'
    query += ')\n'

    query += f'WHERE {length * 0.9} < p1.total_length'
    for i in range(2, DEFAULT_NB_STOPS):
        query += f' + p{i}.total_length'
    query += f' < {length * 1.1}\n'

    query += 'AND size(REDUCE(s=[], n in nodes(p) | '
    query += f'CASE WHEN NOT n IN s THEN s + n ELSE s END)) = {DEFAULT_NB_STOPS+1}\n'

    query += 'RETURN starting_point, r1'
    for i in range(2, DEFAULT_NB_STOPS + 1):
        query += f', r{i}'
    query += ' LIMIT 1'

    print(f'[QUERY]\n{query}\n')
    return query


def build_itinerary_query(nb_stops, restaurant_ids, length):
    query = 'MATCH\n(r1:Restaurant)-[sp1:shortest_path_to]->(r2:Restaurant)'
    for i in range(2, nb_stops):
        query += f',\n(r{i})-[sp{i}:shortest_path_to]->(r{i+1}:Restaurant)'

    query += f'\nWHERE ID(r1) = {restaurant_ids[0]}'
    for i in range(2, nb_stops + 1):
        query += f'\nAND ID(r{i}) = {restaurant_ids[i - 1]}'

    query += '\nMATCH\n'
    query += '(j1:Junction)-->(r1),\n'
    query += 'p1=shortestPath((j1)-[:connects_to*..30]->(j2))'
    for i in range(2, nb_stops):
        query += f',\n(j{i}:Junction)-->(r{i})'
        query += f',\np{i}=shortestPath((j{i})-[:connects_to*..30]->(j{i+1}))'
    query += f',\n(j{nb_stops}:Junction)-->(r{nb_stops})'

    query += '\nWITH'
    for i in range(1, nb_stops):
        query += f'\nsp{i}.total_length AS l{i},'
    query += '\np1'
    for i in range(2, nb_stops):
        query += f', p{i}'
    query += ', r1'
    for i in range(2, nb_stops+1):
        query += f', r{i}'

    query += f'\nWHERE {length * 0.9} < l1'
    for i in range(2, nb_stops):
        query += f' + l{i}'
    query += f' < {length * 1.1}\n'

    query += 'RETURN p1'
    for i in range(2, nb_stops):
        query += f', p{i}'
    query += ', l1'
    for i in range(2, nb_stops):
        query += f', l{i}'
    query += ', r1'
    for i in range(2, nb_stops + 1):
        query += f', r{i}'

    query += '\nLIMIT 1'

    print(f'[QUERY]\n{query}\n')
    return query
