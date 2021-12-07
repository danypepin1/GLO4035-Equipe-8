DEFAULT_NB_STOPS = 10


def build_starting_point_query(length, types):
    query = 'MATCH p=('
    query += '-->'.join([f'(r{i}:Restaurant)' for i in range(1, DEFAULT_NB_STOPS + 1)])
    query += ')\n'
    query += 'WHERE size(REDUCE(s=[], n in nodes(p) '
    query += f'| CASE WHEN NOT n IN s THEN s + n ELSE s END)) = {DEFAULT_NB_STOPS}\n'
    if len(types) > 0:
        query += f'AND ANY(r in nodes(p) WHERE ANY(type in {str(types)} WHERE type in r.types))\n'
    query += f'AND REDUCE(acc=0, r in relationships(p) | acc + r.total_length) < {length * 1.1}\n'
    query += 'MATCH (starting_point:Junction)-->(r1)\n'
    query += f'RETURN starting_point, {", ".join([f"r{i}" for i in range(1, 11)])}\n'
    query += 'LIMIT 1'

    print(f'[QUERY]\n{query}\n')
    return query


def build_itinerary_query(nb_stops, restaurant_ids):
    query = 'MATCH (r1:Restaurant)-[sp1:shortest_path_to]->(r2:Restaurant),\n'
    query += ',\n'.join([f'(r{i})-[sp{i}:shortest_path_to]->(r{i+1}:Restaurant)' for i in range(2, nb_stops)])
    query += f'\nWHERE '
    query += '\nAND '.join([f'ID(r{i}) = {restaurant_ids[i - 1]}' for i in range(1, nb_stops + 1)])
    query += '\nMATCH '
    query += ',\n'.join([f'p{i}=shortestPath((r{i})-[:connects_to*..20]->(r{i+1}))' for i in range(1, nb_stops)])
    query += f'\nRETURN {", ".join([f"p{i}" for i in range(1, 10)])},\n'
    query += f'{", ".join([f"sp{i}.total_length AS l{i}" for i in range(1, 10)])},\n'
    query += f'{", ".join([f"r{i}" for i in range(1, 11)])}\n'
    query += 'LIMIT 1'

    print(f'[QUERY]\n{query}\n')
    return query
