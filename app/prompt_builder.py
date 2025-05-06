from typing import Dict, List, Any


class MoviePromptBuilder:
    """
    Clase encargada de construir prompts para el recomendador de películas.
    """

    def build_recommendation_prompt(self, movies: List[Dict[str, Any]], user_query: str = "") -> str:
        """
        Construye un prompt para el modelo de lenguaje basado en la información
        de películas recomendadas.

        Args:
            movies: Lista de diccionarios con información de películas
            user_query: Consulta del usuario

        Returns:
            Prompt formateado para el modelo de lenguaje
        """
        if not movies:
            return f"""
            Eres un asistente experto en cine que proporciona recomendaciones personalizadas.

            CONSULTA DEL USUARIO: "{user_query}"

            RESULTADOS DE BÚSQUEDA:
            No se encontraron películas que coincidan con los criterios de búsqueda.

            Tu tarea es responder al usuario explicando que no se encontraron películas 
            que coincidan con sus criterios. Proporciona algunas sugerencias generales 
            sobre cómo podría modificar su búsqueda para obtener mejores resultados.
            """

        cleaned_movies = self._clean_movie_data(movies)

        sorted_movies = sorted(cleaned_movies, key=lambda x: float(x.get('recommendation_score', 0)), reverse=True)

        criteria = sorted_movies[0].get('recommendation_criteria', ['desconocido'])
        if isinstance(criteria, list):
            criteria = ', '.join(criteria)

        unique_genres = self._extract_unique_genres(sorted_movies)

        movies_section = self._format_movies_section(sorted_movies[:10])

        avg_rating = self._calculate_average_rating(sorted_movies)
        top_directors = self._get_top_directors(sorted_movies)
        decade_counts = self._count_decades(sorted_movies)

        prompt = f"""
        Eres un asistente experto en cine que proporciona recomendaciones personalizadas.

        CONSULTA DEL USUARIO: "{user_query}"

        RESULTADOS DE BÚSQUEDA:
        Se encontraron {len(sorted_movies)} películas que podrían interesarle al usuario.
        Criterio principal de recomendación: {criteria}

        PELÍCULAS RECOMENDADAS (ordenadas por relevancia):
        {movies_section}

        ANÁLISIS DE RECOMENDACIONES:
        - Géneros predominantes: {', '.join(unique_genres[:5])}
        - Valoración media: {avg_rating:.2f}/5
        - Directores destacados: {', '.join([director for director, _ in top_directors])}
        - Décadas representadas: {', '.join([f"{decade} ({count} películas)" for decade, count in decade_counts.items()])}

        Tu tarea es responder al usuario con recomendaciones personalizadas basadas en estos resultados.
        Debes:
        1. Presentar las 3-5 películas más relevantes de manera conversacional y atractiva
        2. Explicar por qué estas películas podrían gustarle basándote en los géneros y otros factores. Debes incluir la valoración media de las películas para que el usuario sepa como de buena es.
        3. Destacar conexiones interesantes entre las películas (si las hay)
        4. Terminar con una pregunta sobre sus preferencias para refinar futuras recomendaciones

        Mantén un tono amigable y entusiasta, como un verdadero amante del cine compartiendo sus pasiones. Responde siempre en el idioma en el que te escribe el usuario.
        Si te pregunta cualquier cosa que no sea recomendaciones sobre películas, debes decir que no puedes responder ya que eres un recomendador de películas y que te pida recomendaciones.
        """

        return prompt

    def _clean_movie_data(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia y prepara los datos de películas para evitar errores con valores None.

        Args:
            movies: Lista de diccionarios con información de películas

        Returns:
            Lista de diccionarios con datos limpios
        """
        cleaned_movies = []
        for movie in movies:
            cleaned_movie = {}
            for key, value in movie.items():
                if key == 'promedio_valoracion' and value is None:
                    cleaned_movie[key] = 0.0
                elif key == 'num_valoraciones' and value is None:
                    cleaned_movie[key] = 0
                elif key == 'recommendation_score' and value is None:
                    cleaned_movie[key] = 0.0
                else:
                    cleaned_movie[key] = value
            cleaned_movies.append(cleaned_movie)
        return cleaned_movies

    def _extract_unique_genres(self, movies: List[Dict[str, Any]]) -> List[str]:
        """
        Extrae todos los géneros únicos de una lista de películas.

        Args:
            movies: Lista de diccionarios con información de películas

        Returns:
            Lista de géneros únicos ordenados
        """
        all_genres = []
        for movie in movies:
            if 'generos' in movie and movie['generos']:
                all_genres.extend(movie['generos'])
        return sorted(list(set(all_genres)))

    def _format_movies_section(self, movies: List[Dict[str, Any]]) -> str:
        """
        Formatea la sección de películas para el prompt.

        Args:
            movies: Lista de diccionarios con información de películas

        Returns:
            Texto formateado con la información de las películas
        """
        movies_section = ""
        for i, movie in enumerate(movies, 1):
            genres_str = ", ".join(movie.get("generos", [])[:3])
            promedio_valoracion = float(movie.get('promedio_valoracion', 0))
            recommendation_score = float(movie.get('recommendation_score', 0))

            movies_section += f"""
            {i}. {movie.get('titulo', 'Sin título')} ({movie.get('año', 'Año desconocido')})
               - Director: {', '.join(movie.get('directores', ['Desconocido']))}
               - Géneros: {genres_str}
               - Duración: {movie.get('duracion', 'Desconocida')}
               - Valoración: {promedio_valoracion:.2f}/5 ({movie.get('num_valoraciones', 0)} valoraciones)
               - Score de recomendación: {recommendation_score:.2f}
            """
        return movies_section

    def _calculate_average_rating(self, movies: List[Dict[str, Any]]) -> float:
        """
        Calcula la valoración media de una lista de películas.

        Args:
            movies: Lista de diccionarios con información de películas

        Returns:
            Valoración media
        """
        total_rating = 0
        valid_ratings = 0
        for movie in movies:
            val = movie.get('promedio_valoracion', 0)
            if val is not None:
                try:
                    total_rating += float(val)
                    valid_ratings += 1
                except (ValueError, TypeError):
                    pass

        return total_rating / valid_ratings if valid_ratings > 0 else 0

    def _get_top_directors(self, movies: List[Dict[str, Any]], limit: int = 3) -> List[tuple]:
        """
        Obtiene los directores más frecuentes en una lista de películas.

        Args:
            movies: Lista de diccionarios con información de películas
            limit: Número máximo de directores a devolver

        Returns:
            Lista de tuplas (director, frecuencia) ordenadas por frecuencia
        """
        director_counts = {}
        for movie in movies:
            for director in movie.get('directores', []):
                director_counts[director] = director_counts.get(director, 0) + 1
        return sorted(director_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def _count_decades(self, movies: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Cuenta las películas por década en una lista de películas.

        Args:
            movies: Lista de diccionarios con información de películas

        Returns:
            Diccionario con décadas y número de películas
        """
        decade_counts = {}
        for movie in movies:
            year = movie.get('año', 0)
            if isinstance(year, str):
                # Intentar extraer un número del string
                import re
                year_match = re.search(r'\d{4}', str(year))
                if year_match:
                    year = int(year_match.group(0))
                else:
                    year = 0
            decade = f"{(int(year) // 10) * 10}s" if year else "Desconocida"
            decade_counts[decade] = decade_counts.get(decade, 0) + 1
        return decade_counts