from pymongo import MongoClient
from datetime import datetime
import uuid
import hashlib
from recomendador.Neo4jConector import Neo4jConector
from recomendador.CompleteRecommendationSystem import Neo4jRecommendationSystem
from recomendador.ChatbotRecommender import ChatbotRecommender


class DatabaseManager:
    def __init__(self):
        """Inicializa las conexiones a las bases de datos Neo4j y MongoDB."""

        NEO4J_URI = "neo4j://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "Virt1234*"

        try:
            self.connector = Neo4jConector(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            self.system = Neo4jRecommendationSystem(self.connector)
            self.recommender = ChatbotRecommender(self.system)
            self.connection_error = None
        except Exception as e:
            self.connection_error = str(e)

        mongo_uri = "mongodb://localhost:27017/"
        client = MongoClient(mongo_uri)
        db = client['MRP']
        self.mongo_coll = db['peliculas']

    def user_exists(self, username: str) -> bool:
        """Devuelve True si existe un usuario con ese username en Neo4j."""
        check_query = "MATCH (u:Usuario {username: $username}) RETURN u LIMIT 1"
        result = self.connector.execute_query(check_query, {"username": username})
        return bool(result)

    def get_peliculas_options(self):
        """Obtiene la lista de todas las películas disponibles en Neo4j."""
        query = "MATCH (p:Pelicula) RETURN DISTINCT p.titulo AS titulo ORDER BY titulo"
        results = self.connector.execute_query(query)
        peliculas = [record['titulo'] for record in results]
        return peliculas

    def enrich_movie_results(self, results):
        """Enriquece los resultados de Neo4j con datos de MongoDB."""
        enriched = []
        import ast
        for item in results:
            enriched_item = item.copy()
            imdb_id = item.get('id')
            if imdb_id:
                mongo_doc = self.mongo_coll.find_one({"id": imdb_id})
                if mongo_doc:
                    for key in ['Duration', 'MPA', 'Votes', 'budget', 'grossWorldWide', 'stars', 'genres']:
                        val = mongo_doc.get(key)
                        if isinstance(val, str) and key in ['stars', 'genres']:
                            try:
                                enriched_item[key] = ast.literal_eval(val)
                            except Exception:
                                enriched_item[key] = [s.strip() for s in val.split(',')]
                        elif val is not None:
                            enriched_item[key] = val
            enriched.append(enriched_item)
        return enriched

    def hash_password(self, password):
        """Encripta la contraseña mediante SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, email):
        """Registra un nuevo usuario en Neo4j."""
        if self.user_exists(username):
            return False, "El nombre de usuario ya está en uso.", None
        try:
            hashed_password = self.hash_password(password)
            user_uuid = str(uuid.uuid4())
            create_query = """
            CREATE (u:Usuario {
                id: $id,
                username: $username,
                password: $password,
                email: $email,
                fecha_registro: $fecha_registro
            }) RETURN u
            """
            params = {
                "id": user_uuid,
                "username": username,
                "password": hashed_password,
                "email": email,
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.connector.execute_query(create_query, params)
            return True, user_uuid, "Usuario registrado exitosamente."
        except Exception as e:
            return False, None, f"Error al registrar: {str(e)}"

    def login_user(self, username, password):
        """Autentica un usuario existente."""
        try:
            hashed = self.hash_password(password)
            auth_query = """
            MATCH (u:Usuario {username: $username, password: $password})
            RETURN u.id AS id, u.username AS username
            """
            res = self.connector.execute_query(
                auth_query, {"username": username, "password": hashed}
            )
            if not res:
                return False, None, None, [], False, "Nombre de usuario o contraseña incorrectos."
            user = res[0]

            ratings_query = """
            MATCH (u:Usuario {id: $id})-[r:VALORA]->(p:Pelicula)
            RETURN p.titulo AS pelicula, r.puntuacion AS valoracion
            """
            ratings = self.connector.execute_query(
                ratings_query, {"id": user['id']}
            )

            has_preferences = len(ratings) > 0
            return True, user['id'], user['username'], ratings, has_preferences, "Inicio de sesión exitoso."
        except Exception as e:
            return False, None, None, [], False, f"Error al iniciar sesión: {str(e)}"

    def save_movie_ratings(self, user_id, movie_ratings):
        """Guarda las valoraciones de películas del usuario en Neo4j."""
        try:
            for rating in movie_ratings:
                pelicula_query = """
                    MATCH (p:Pelicula {titulo: $titulo})
                    RETURN p.id as id
                    """
                pelicula_params = {"titulo": rating['pelicula']}
                pelicula_result = self.connector.execute_query(pelicula_query, pelicula_params)

                if pelicula_result:
                    pelicula_id = pelicula_result[0]['id']

                    rating_query = """
                        MATCH (u:Usuario {id: $user_id})
                        MATCH (p:Pelicula {id: $pelicula_id})
                        MERGE (u)-[r:VALORA]->(p)
                        ON CREATE SET r.puntuacion = $puntuacion
                        RETURN r
                        """
                    rating_params = {
                        "user_id": user_id,
                        "pelicula_id": pelicula_id,
                        "puntuacion": rating['valoracion']
                    }
                    self.connector.execute_query(rating_query, rating_params)

            return True, "Valoraciones guardadas exitosamente."
        except Exception as e:
            return False, f"Error al guardar las valoraciones: {str(e)}"

    def get_movie_recommendations(self, user_query, user_id):
        """Obtiene recomendaciones de películas basadas en la consulta del usuario."""
        results = self.recommender.process_natural_query(user_query, user_id)
        return self.enrich_movie_results(results)