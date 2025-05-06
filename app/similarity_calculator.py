import numpy as np


def calculate_pearson_similarity(user1_ratings, user2_ratings, min_peliculas=3):
    """
    Calcula la correlación de Pearson entre dos usuarios basándose en sus valoraciones
    """
    common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())
    n_common = len(common_movies)

    if n_common < min_peliculas:
        return None

    movie_ids = list(common_movies)
    ratings1 = np.array([user1_ratings[movie_id] for movie_id in movie_ids], dtype=np.float64)
    ratings2 = np.array([user2_ratings[movie_id] for movie_id in movie_ids], dtype=np.float64)

    mean1 = np.mean(ratings1)
    mean2 = np.mean(ratings2)

    numerator = np.sum((ratings1 - mean1) * (ratings2 - mean2))
    denom1 = np.sqrt(np.sum((ratings1 - mean1) ** 2))
    denom2 = np.sqrt(np.sum((ratings2 - mean2) ** 2))

    if denom1 > 0 and denom2 > 0:
        pearson = numerator / (denom1 * denom2)
        return pearson
    return None


def calculate_similarities_for_new_user(connector, user_id, movie_ratings, min_peliculas=3):
    """
    Calcula similaridades solo con usuarios que hayan valorado las mismas películas
    que el nuevo usuario

    Args:
        connector: Conector Neo4j
        user_id: ID del usuario nuevo
        movie_ratings: Lista de diccionarios con las valoraciones {pelicula: título, valoracion: puntuación}
        min_peliculas: Número mínimo de películas en común para calcular similitud

    Returns:
        int: Número de relaciones de similitud creadas
    """
    movie_ids_query = """
    MATCH (p:Pelicula)
    WHERE p.titulo IN $titulos
    RETURN p.id as id, p.titulo as titulo
    """
    movie_titles = [rating['pelicula'] for rating in movie_ratings]
    movies_result = connector.execute_query(movie_ids_query, {"titulos": movie_titles})

    title_to_id = {record['titulo']: record['id'] for record in movies_result}

    new_user_ratings = {}
    for rating in movie_ratings:
        movie_title = rating['pelicula']
        if movie_title in title_to_id:
            new_user_ratings[title_to_id[movie_title]] = rating['valoracion']

    related_users_query = """
    MATCH (u:Usuario)-[r:VALORA]->(p:Pelicula)
    WHERE p.id IN $movie_ids AND u.id <> $user_id
    RETURN DISTINCT u.id as user_id
    """
    related_users = connector.execute_query(
        related_users_query,
        {"movie_ids": list(new_user_ratings.keys()), "user_id": user_id}
    )

    similarity_pairs = []

    for user_record in related_users:
        other_user_id = user_record['user_id']

        other_ratings_query = """
        MATCH (u:Usuario {id: $user_id})-[r:VALORA]->(p:Pelicula)
        RETURN p.id as movie_id, r.puntuacion as rating
        """
        other_ratings_result = connector.execute_query(
            other_ratings_query,
            {"user_id": other_user_id}
        )

        other_user_ratings = {record['movie_id']: record['rating'] for record in other_ratings_result}

        similarity = calculate_pearson_similarity(new_user_ratings, other_user_ratings, min_peliculas)

        if similarity is not None:
            similarity_pairs.append([user_id, other_user_id, float(similarity)])

    if similarity_pairs:
        create_similarities_query = """
        UNWIND $batch AS pair
        MATCH (u1:Usuario {id: pair[0]}), (u2:Usuario {id: pair[1]})
        MERGE (u1)-[s:SIMILAR]-(u2)
        SET s.score = pair[2]
        """
        connector.execute_query(create_similarities_query, {"batch": similarity_pairs})

    return len(similarity_pairs)