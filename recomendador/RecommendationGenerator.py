import concurrent.futures
import time

class RecommendationGeneratorMixin:

    def generate_personalized_recommendations(self, user_id, limit=20):
        """Genera recomendaciones personalizadas usando paralelización."""
        cache_key = f"{user_id}_{limit}"
        with self._cache_lock:
            cache_entry = self._recommendations_cache.get(cache_key)
            if cache_entry and (time.time() - cache_entry['timestamp'] < self.cache_expiration_time):
                return cache_entry['data']

        preferences = self._get_user_preferences(user_id)

        tasks = [
            ('genero', preferences['favorite_genres'], user_id, 5),
            ('director', preferences['favorite_directors'], user_id, 5),
            ('pelicula_similar', preferences['favorite_movies'], user_id, 5),
            ('usuario_similar', [user_id], user_id, 5)
        ]

        combined_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._get_recommendations_by_criteria, c, v, user_id, l): c
                for c, v, user_id, l in tasks
            }
            for future in concurrent.futures.as_completed(futures):
                criteria = futures[future]
                try:
                    results = future.result()
                    for r in results:
                        result_dict = dict(r)
                        result_dict['criteria_origin'] = criteria
                        combined_results.append(result_dict)
                except Exception as e:
                    print(f"Error obteniendo recomendaciones por {criteria}: {e}")

        if combined_results:
            unique_movies = {}
            for r in combined_results:
                title = r['titulo']
                if title not in unique_movies:
                    unique_movies[title] = {
                        'titulo': title,
                        'año': r.get('año'),
                        'puntaje_total': 0,
                        'criterios': []
                    }
                criteria_val = r.get('criteria_origin')
                base_score = r.get('score_coincidencia', 0)
                rating = r.get('promedio_valoracion', 0)

                weights = {
                    'genero': 0.3,
                    'director': 0.25,
                    'pelicula_similar': 0.25,
                    'usuario_similar': 0.2
                }
                score = (base_score * 0.7 + rating * 0.3) * weights.get(criteria_val, 0.1)
                unique_movies[title]['puntaje_total'] += score
                unique_movies[title]['criterios'].append(criteria_val)

            sorted_recommendations = sorted(
                unique_movies.values(),
                key=lambda x: x['puntaje_total'],
                reverse=True
            )[:limit]

            recommended_titles = [r['titulo'] for r in sorted_recommendations]
            details = self._get_movie_details(recommended_titles)

            final_result = []
            for detail in details:
                detail_dict = dict(detail)
                for rec in sorted_recommendations:
                    if rec['titulo'] == detail_dict['titulo']:
                        detail_dict['recommendation_score'] = rec['puntaje_total']
                        detail_dict['recommendation_criteria'] = rec['criterios']
                        final_result.append(detail_dict)
                        break

            final_result.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)

            with self._cache_lock:
                self._recommendations_cache[cache_key] = {
                    'data': final_result,
                    'timestamp': time.time()
                }

            return final_result

        return []

    def get_recommendations_by_criteria_combination(self, criteria_dict, user_id=None, limit=10):
        """
        Obtiene recomendaciones basadas en una combinación de criterios.
        criteria_dict: Diccionario con criterios como claves y valores para cada uno.
                       Ej: {'genero': ['Acción', 'Aventura'], 'director': ['Steven Spielberg']}
        user_id: Opcional para incluir recomendaciones basadas en usuarios similares
        limit: Número máximo de recomendaciones a retornar
        """
        filter_keys = [k for k in criteria_dict.keys() if k in ('genero', 'director', 'pelicula_similar')]

        if filter_keys and set(criteria_dict.keys()) <= set(filter_keys):
            return self._get_combined_recommendations(
                {k: criteria_dict[k] for k in filter_keys},
                None,
                limit
            )

        combined_criteria_count = sum(1 for k, v in criteria_dict.items() if v and k in ['genero', 'director', 'pelicula_similar'])
        should_use_combined_query = combined_criteria_count > 1

        combined_results = []

        if should_use_combined_query:
            filtered_criteria = {k: v for k, v in criteria_dict.items() if k != 'usuario_similar'}
            combined_query_results = self._get_combined_recommendations(filtered_criteria, user_id, limit)
            combined_results.extend(combined_query_results)
            if user_id and 'usuario_similar' in criteria_dict:
                similar_user_results = self._get_recommendations_by_criteria('usuario_similar', [user_id], user_id, limit)
                for r in similar_user_results:
                    result_dict = dict(r)
                    result_dict['criteria_origin'] = 'usuario_similar'
                    combined_results.append(result_dict)
        else:
            if user_id and 'usuario_similar' not in criteria_dict:
                criteria_dict['usuario_similar'] = [user_id]
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(criteria_dict)) as executor:
                futures = {}
                for criteria, values in criteria_dict.items():
                    if values:
                        futures[executor.submit(self._get_recommendations_by_criteria, criteria, values, user_id, limit)] = criteria
                for future in concurrent.futures.as_completed(futures):
                    criteria = futures[future]
                    try:
                        results = future.result()
                        for r in results:
                            result_dict = dict(r)
                            result_dict['criteria_origin'] = criteria
                            combined_results.append(result_dict)
                    except Exception as e:
                        print(f"Error obteniendo recomendaciones por {criteria}: {e}")

        if combined_results:
            unique_movies = {}
            for r in combined_results:
                title = r['titulo']
                if title not in unique_movies:
                    unique_movies[title] = {
                        'titulo': title,
                        'año': r.get('año'),
                        'puntaje_total': 0,
                        'criterios': []
                    }
                criteria_val = r.get('criteria_origin')
                if isinstance(criteria_val, str):
                    criteria_list = [criteria_val]
                else:
                    criteria_list = criteria_val
                base_score = r.get('score_coincidencia', 0)
                rating = r.get('promedio_valoracion', 0)

                weights = {
                    'genero': 0.3,
                    'director': 0.25,
                    'pelicula_similar': 0.25,
                    'usuario_similar': 0.2,
                    'multi': 0.5
                }
                if should_use_combined_query and not isinstance(criteria_val, str):
                    base_score = 3.0 * len(criteria_list)
                    weight = weights.get('multi', 0.5)
                else:
                    weight = weights.get(criteria_list[0], 0.1)
                score = (base_score * 0.7 + rating * 0.3) * weight
                unique_movies[title]['puntaje_total'] += score
                for c in criteria_list:
                    if c not in unique_movies[title]['criterios']:
                        unique_movies[title]['criterios'].append(c)

            sorted_recommendations = sorted(
                unique_movies.values(),
                key=lambda x: x['puntaje_total'],
                reverse=True
            )[:limit]

            recommended_titles = [r['titulo'] for r in sorted_recommendations]
            details = self._get_movie_details(recommended_titles)

            final_result = []
            for detail in details:
                detail_dict = dict(detail)
                for rec in sorted_recommendations:
                    if rec['titulo'] == detail_dict['titulo']:
                        detail_dict['recommendation_score'] = rec['puntaje_total']
                        detail_dict['recommendation_criteria'] = rec['criterios']
                        final_result.append(detail_dict)
                        break

            final_result.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
            return final_result

        return []

    def get_complete_recommendations(self, user_id, limit=10):
        return self.generate_personalized_recommendations(user_id, limit)