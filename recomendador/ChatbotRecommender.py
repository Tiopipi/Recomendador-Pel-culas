import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
import re
from recomendador.GenreMapper import GenreMapper

class ChatbotRecommender:
    """
    Clase para procesar consultas en lenguaje natural y devolver recomendaciones.
    Ahora con soporte para traducción de géneros del español al inglés.
    """

    def __init__(self, recommendation_system):
        self.system = recommendation_system
        self.genre_map = GenreMapper.get_genre_map()

    def extract_criteria(self, query):
        """Extrae de la consulta los criterios para la recomendación."""
        query = query.lower()
        criteria_dict = {}

        found_spanish_genres = []
        for spanish_genre in self.genre_map.keys():
            if spanish_genre in query:
                found_spanish_genres.append(self.genre_map[spanish_genre])

        if found_spanish_genres:
            criteria_dict['genero'] = found_spanish_genres
        else:
            allowed_genres = self.system.get_all_genres()
            found_genres = [genre for genre in allowed_genres if genre.lower() in query]
            if found_genres:
                criteria_dict['genero'] = found_genres

        allowed_directors = self.system.get_all_directors()
        found_directors = [director for director in allowed_directors if director.lower() in query]
        if found_directors:
            criteria_dict['director'] = found_directors

        movie_patterns = [
            r'como (["\'])(.+?)\1',
            r'similar a (["\'])(.+?)\1',
            r'parecida a (["\'])(.+?)\1',
            r'como (\b\w+\b)',
            r'similar a (\b\w+\b)',
            r'parecida a (\b\w+\b)'
        ]
        movies = []
        for pattern in movie_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                if isinstance(match, tuple) and len(match) > 1:
                    movies.append(match[1])
                elif isinstance(match, str):
                    movies.append(match)
        if movies:
            movie_ids = self._get_movie_ids(movies)
            if movie_ids:
                criteria_dict['pelicula_similar'] = movie_ids

        return criteria_dict

    def _get_movie_ids(self, movie_titles):
        """
        Obtiene los IDs de películas a partir de sus títulos consultando la base de datos.
        """
        if not movie_titles:
            return []

        query = """
        MATCH (p:Pelicula)
        WHERE p.titulo IN $titulos
        RETURN p.id AS id, p.titulo AS titulo
        """

        result = self.system.execute_query(query, {"titulos": movie_titles})

        movie_ids = []
        for record in result:
            if record.get("id"):
                movie_ids.append(record["id"])

        if not movie_ids:
            partial_query = """
            MATCH (p:Pelicula)
            WHERE any(titulo IN $titulos WHERE p.titulo CONTAINS titulo OR toLower(p.titulo) CONTAINS toLower(titulo))
            RETURN p.id AS id, p.titulo AS titulo
            LIMIT 3
            """
            partial_result = self.system.execute_query(partial_query, {"titulos": movie_titles})
            movie_ids = [record["id"] for record in partial_result if record.get("id")]

        return movie_ids

    def process_natural_query(self, query, user_id=None, limit=10):
        """Procesa la consulta en lenguaje natural y retorna las recomendaciones."""
        criteria = self.extract_criteria(query)
        if not criteria:
            if user_id:
                return self.system.generate_personalized_recommendations(user_id, limit)
            else:
                return {
                    "error": "No se encontraron criterios en la consulta. Especifique géneros, directores o películas similares."}
        return self.system.get_recommendations_by_criteria_combination(criteria, user_id, limit)