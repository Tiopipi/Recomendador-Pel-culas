import time
from functools import lru_cache

class UserPreferencesMixin:

    @lru_cache(maxsize=100)
    def _get_user_preferences(self, user_id):
        """Obtiene las preferencias del usuario con cache."""
        with self._cache_lock:
            cache_entry = self._preferences_cache.get(user_id)
            if cache_entry and (time.time() - cache_entry['timestamp'] < self.cache_expiration_time):
                return cache_entry['data']

        preferences_query = """
        // Preferencias del usuario (géneros, directores y películas favoritas)
        MATCH (u:Usuario {id: $usuario_id})

        // Buscar géneros favoritos
        OPTIONAL MATCH (u)-[v1:VALORA]->(p1:Pelicula)-[:PERTENECE_A]->(g:Genero)
        WHERE v1.puntuacion > 4
        WITH u, g.nombre AS genero, COUNT(p1) AS contador_genero, AVG(v1.puntuacion) AS promedio_genero
        ORDER BY contador_genero DESC, promedio_genero DESC
        LIMIT 3

        // Buscar directores favoritos
        MATCH (u)-[v2:VALORA]->(p2:Pelicula)<-[:DIRIGE]-(d:Director)
        WHERE v2.puntuacion > 4
        WITH u, genero, contador_genero, promedio_genero, 
             d.nombre AS director_name,
             COUNT(p2) AS contador_director, 
             AVG(v2.puntuacion) AS promedio_director
        ORDER BY contador_director DESC, promedio_director DESC
        LIMIT 3

        // Buscar películas favoritas
        MATCH (u)-[v3:VALORA]->(p3:Pelicula)
        WHERE v3.puntuacion > 4.5
        WITH genero, contador_genero, promedio_genero, 
             director_name, contador_director, promedio_director, 
             p3.id AS pelicula_id
        LIMIT 3

        RETURN genero, director_name, pelicula_id
        """

        preferences = self.execute_query(preferences_query, {"usuario_id": user_id})

        favorite_genres = [record["genero"] for record in preferences if record["genero"]]
        favorite_directors = [record["director_name"] for record in preferences if record["director_name"]]
        favorite_movies = [record["pelicula_id"] for record in preferences if record["pelicula_id"]]

        result = {
            'favorite_genres': favorite_genres,
            'favorite_directors': favorite_directors,
            'favorite_movies': favorite_movies
        }

        with self._cache_lock:
            self._preferences_cache[user_id] = {
                'data': result,
                'timestamp': time.time()
            }

        return result