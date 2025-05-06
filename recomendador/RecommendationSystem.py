import threading


class RecommendationSystem:
    _cache_lock = threading.Lock()
    _preferences_cache = {}
    _recommendations_cache = {}

    def __init__(self, db_connection, cache_expiration_time=3600):
        self.db_connection = db_connection
        self.cache_expiration_time = cache_expiration_time

    def execute_query(self, query, params=None):
        """Ejecuta una consulta en la base de datos Neo4j."""
        return self.db_connection.execute_query(query, params)


    def get_all_genres(self):
        """Obtiene la lista de todos los géneros desde la base de datos."""
        query = "MATCH (n:Genero) RETURN n.nombre AS genero"
        result = self.execute_query(query)
        return [record["genero"] for record in result if record.get("genero")]

    def get_all_directors(self):
        """Obtiene la lista de todos los directores desde la base de datos."""
        query = "MATCH (n:Director) RETURN n.nombre AS director"
        result = self.execute_query(query)
        return [record["director"] for record in result if record.get("director")]

    def get_all_movies_titles(self):
        """Obtiene la lista de todos los títulos de películas desde la base de datos."""
        query = "MATCH (n:Pelicula) RETURN n.titulo AS titulo"
        result = self.execute_query(query)
        return [record["titulo"] for record in result if record.get("titulo")]

    def clear_cache(self):
        with self._cache_lock:
            self._preferences_cache.clear()
            self._recommendations_cache.clear()
        self._get_user_preferences.cache_clear()