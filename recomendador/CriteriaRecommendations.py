class CriteriaRecommendationsMixin:

    def _get_recommendations_by_criteria(self, criteria, values, user_id=None, limit=5):
        """Obtiene recomendaciones basadas en un criterio específico."""
        if not values:
            return []

        if criteria == 'genero':
            allowed = self.get_all_genres()
            values = [v for v in values if v in allowed]
        elif criteria == 'director':
            allowed = self.get_all_directors()
            values = [v for v in values if v in allowed]
        elif criteria == 'pelicula_similar':
            query = "MATCH (p:Pelicula) WHERE p.id IN $valores RETURN p.id AS id"
            result = self.execute_query(query, {"valores": values})
            valid_ids = [record["id"] for record in result]
            values = valid_ids

        if not values:
            return []

        if criteria == 'genero':
            query = """
            MATCH (p:Pelicula)-[:PERTENECE_A]->(g:Genero)
            WHERE g.nombre IN $valores
            """
            if user_id:
                query += """
                AND NOT EXISTS {
                    MATCH (u:Usuario {id: $usuario_id})-[:VALORA]->(p)
                }
                """
            query += """
            WITH p, COUNT(DISTINCT g) AS coincidencias
            MATCH (p)<-[v:VALORA]-(u:Usuario)
            WITH p, coincidencias, AVG(v.puntuacion) AS promedio_valoracion, COUNT(v) AS num_valoraciones
            WHERE num_valoraciones > 5
            RETURN p.id AS id, p.titulo AS titulo, p.año AS año, 
                   coincidencias AS score_coincidencia,
                   promedio_valoracion
            ORDER BY score_coincidencia DESC, promedio_valoracion DESC
            LIMIT $limite
            """

        elif criteria == 'director':
            query = """
            MATCH (p:Pelicula)<-[:DIRIGE]-(d:Director)
            WHERE d.nombre IN $valores
            """
            if user_id:
                query += """
                AND NOT EXISTS {
                    MATCH (u:Usuario {id: $usuario_id})-[:VALORA]->(p)
                }
                """
            query += """
            WITH p, COUNT(DISTINCT d) AS coincidencias
            MATCH (p)<-[v:VALORA]-(u:Usuario)
            WITH p, coincidencias, AVG(v.puntuacion) AS promedio_valoracion, COUNT(v) AS num_valoraciones
            WHERE num_valoraciones > 5
            RETURN p.id AS id, p.titulo AS titulo, p.año AS año, 
                   coincidencias AS score_coincidencia,
                   promedio_valoracion
            ORDER BY score_coincidencia DESC, promedio_valoracion DESC
            LIMIT $limite
            """

        elif criteria == 'pelicula_similar':
            query = """
            MATCH (pelicula_origen:Pelicula)
            WHERE pelicula_origen.id IN $valores
            MATCH (pelicula_origen)-[:PERTENECE_A]->(g:Genero)<-[:PERTENECE_A]-(p:Pelicula)
            WHERE p <> pelicula_origen
            """
            if user_id:
                query += """
                AND NOT EXISTS {
                    MATCH (u:Usuario {id: $usuario_id})-[:VALORA]->(p)
                }
                """
            query += """
            WITH p, COUNT(DISTINCT g) AS coincidencias
            MATCH (p)<-[v:VALORA]-(u:Usuario)
            WITH p, coincidencias, AVG(v.puntuacion) AS promedio_valoracion, COUNT(v) AS num_valoraciones
            WHERE num_valoraciones > 5
            RETURN p.id AS id, p.titulo AS titulo, p.año AS año, 
                   coincidencias AS score_coincidencia,
                   promedio_valoracion
            ORDER BY score_coincidencia DESC, promedio_valoracion DESC
            LIMIT $limite
            """

        elif criteria == 'usuario_similar':
            if not user_id:
                return []
            query = """
            MATCH (u:Usuario {id: $usuario_id})-[sim:SIMILAR]->(u2:Usuario)
            WHERE sim.score > 0.3
            MATCH (u2)-[v:VALORA]->(p:Pelicula)
            WHERE v.puntuacion > 3.5
              AND NOT (u)-[:VALORA]->(p)
            WITH p, COUNT(DISTINCT u2) AS usuarios_comunes, AVG(v.puntuacion) AS promedio_valoracion
            MATCH (p)<-[v2:VALORA]-(u_all:Usuario)
            WITH p, usuarios_comunes, promedio_valoracion, COUNT(v2) AS num_valoraciones
            WHERE num_valoraciones > 5
            RETURN p.id AS id, p.titulo AS titulo, p.año AS año,
                   usuarios_comunes AS score_coincidencia,
                   promedio_valoracion
            ORDER BY score_coincidencia DESC, promedio_valoracion DESC
            LIMIT $limite
            """
        else:
            return []

        params = {
            "valores": values,
            "limite": limit
        }
        if user_id:
            params["usuario_id"] = user_id

        return self.execute_query(query, params)

    def _get_combined_recommendations(self, criteria_values, user_id=None, limit=10):
        """
        Obtiene recomendaciones que satisfacen múltiples criterios simultáneamente.

        Args:
            criteria_values: Dict con criterios como claves y sus valores (ej. {'genero': ['Acción'], 'director': ['Christopher Nolan']})
            user_id: Opcional para filtrar películas ya valoradas
            limit: Número máximo de recomendaciones a retornar
        """
        if not criteria_values:
            return []

        query = "MATCH "
        where_clauses = []
        params = {"limite": limit}

        if 'genero' in criteria_values and criteria_values['genero']:
            query += "(p:Pelicula)-[:PERTENECE_A]->(g:Genero) "
            where_clauses.append("g.nombre IN $generos")
            params["generos"] = criteria_values['genero']

        if 'director' in criteria_values and criteria_values['director']:
            if 'genero' in criteria_values and criteria_values['genero']:
                query += ", "
            query += "(p)<-[:DIRIGE]-(d:Director) "
            where_clauses.append("d.nombre IN $directores")
            params["directores"] = criteria_values['director']

        if 'pelicula_similar' in criteria_values and criteria_values['pelicula_similar']:
            if ('genero' in criteria_values and criteria_values['genero']) or ('director' in criteria_values and criteria_values['director']):
                query += ", "
            query += "(origen:Pelicula)-[:PERTENECE_A]->(gen:Genero)<-[:PERTENECE_A]-(p) "
            where_clauses.append("origen.id IN $peliculas_similares")
            where_clauses.append("p <> origen")
            params["peliculas_similares"] = criteria_values['pelicula_similar']

        if where_clauses:
            query += "WHERE " + " AND ".join(where_clauses)

        if user_id:
            if where_clauses:
                query += " AND "
            else:
                query += " WHERE "
            query += "NOT EXISTS { MATCH (u:Usuario {id: $usuario_id})-[:VALORA]->(p) }"
            params["usuario_id"] = user_id

        query += """
        WITH DISTINCT p
        MATCH (p)<-[v:VALORA]-(u:Usuario)
        WITH p, AVG(v.puntuacion) AS promedio_valoracion, COUNT(v) AS num_valoraciones
        WHERE num_valoraciones > 5
        RETURN p.id AS id, p.titulo AS titulo, p.año AS año, 
               promedio_valoracion,
               num_valoraciones,
               'multi' AS criteria_origin
        ORDER BY promedio_valoracion DESC, num_valoraciones DESC
        LIMIT $limite
        """

        results = self.execute_query(query, params)

        formatted_results = []
        for r in results:
            result_dict = dict(r)
            result_dict['score_coincidencia'] = 1.0
            criteria_names = [k for k in criteria_values.keys() if criteria_values[k]]
            result_dict['criteria_origin'] = criteria_names
            formatted_results.append(result_dict)

        return formatted_results

    def _get_movie_details(self, titles):
        """Obtiene los detalles completos de un conjunto de películas a partir de sus títulos."""
        if not titles:
            return []

        details_query = """
        MATCH (p:Pelicula)
        WHERE p.titulo IN $titulos
        OPTIONAL MATCH (p)-[:PERTENECE_A]->(genero:Genero)
        OPTIONAL MATCH (director:Director)-[:DIRIGE]->(p)
        OPTIONAL MATCH (p)<-[v:VALORA]-(u:Usuario)
        WITH p, 
             COLLECT(DISTINCT genero.nombre) AS generos, 
             COLLECT(DISTINCT director.nombre) AS directores,
             AVG(v.puntuacion) AS promedio_valoracion,
             COUNT(v) AS num_valoraciones
        RETURN p.id AS id,
               p.titulo AS titulo, 
               p.año AS año, 
               p.duracion AS duracion, 
               generos, 
               directores, 
               promedio_valoracion,
               num_valoraciones
        """
        return self.execute_query(details_query, {"titulos": titles})