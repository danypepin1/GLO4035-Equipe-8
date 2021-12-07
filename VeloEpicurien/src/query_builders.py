DEFAULT_NB_STOPS = 10


def build_starting_point_query(length, types):
    query = 'MATCH p=((r1:Restaurant)'
    for i in range(2, DEFAULT_NB_STOPS + 1):
        query += f'-->(r{i}:Restaurant)'
    query += ')\n'

    query += 'WHERE size(REDUCE(s=[], n in nodes(p) '
    query += f'| CASE WHEN NOT n IN s THEN s + n ELSE s END)) = {DEFAULT_NB_STOPS}\n'

    if len(types) > 0:
        query += f'AND ANY(r in nodes(p) WHERE ANY(type in {str(types)} WHERE type in r.types))\n'

    query += f'AND REDUCE(acc=0, r in relationships(p) | acc + r.total_length) < {length * 1.1}\n'

    query += 'MATCH (starting_point:Junction)-->(r1)\n'

    query += 'RETURN starting_point, r1'
    for i in range(2, DEFAULT_NB_STOPS + 1):
        query += f', r{i}'
    query += ' LIMIT 1'

    print(f'[QUERY]\n{query}\n')
    return query


def build_itinerary_query(nb_stops, restaurant_ids):
    query = 'MATCH\n(r1:Restaurant)-[sp1:shortest_path_to]->(r2:Restaurant)'
    for i in range(2, nb_stops):
        query += f',\n(r{i})-[sp{i}:shortest_path_to]->(r{i+1}:Restaurant)'

    query += f'\nWHERE ID(r1) = {restaurant_ids[0]}'
    for i in range(2, nb_stops + 1):
        query += f'\nAND ID(r{i}) = {restaurant_ids[i - 1]}'

    query += '\nMATCH p1=shortestPath((r1)-[:connects_to*..20]->(r2))'
    for i in range(2, nb_stops):
        query += f',\np{i}=shortestPath((r{i})-[:connects_to*..20]->(r{i+1}))'

    query += '\nRETURN p1'
    for i in range(2, nb_stops):
        query += f', p{i}'
    for i in range(1, nb_stops):
        query += f',\nsp{i}.total_length AS l{i}'
    query += ',\nr1'
    for i in range(2, nb_stops + 1):
        query += f', r{i}'

    query += '\nLIMIT 1'

    print(f'[QUERY]\n{query}\n')
    return query
