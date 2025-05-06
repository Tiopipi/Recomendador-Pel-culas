import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from recomendador.Neo4jConector import Neo4jConector
from recomendador.ChatbotRecommender import ChatbotRecommender
from recomendador.utils import show_recommendations

from recomendador.CompleteRecommendationSystem import Neo4jRecommendationSystem

def main():
    print("Movie Recommendation System")
    print("==========================")

    NEO4J_URI = "neo4j://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "Virt1234*"

    connector = Neo4jConector(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    system = Neo4jRecommendationSystem(connector)

    chatbot = ChatbotRecommender(system)

    print("\nProcesando consulta: 'Recomiéndame películas de cuento de hadas'")
    results = chatbot.process_natural_query("Recomiéndame películas de cuento de hadas", limit=5)
    show_recommendations(results)

    print("\nProcesando consulta: 'Quiero ver películas de Steven Spielberg'")
    results = chatbot.process_natural_query("Quiero ver películas de Steven Spielberg", limit=5)
    show_recommendations(results)

    print("\nProcesando consulta: 'Recomiéndame películas de Action dirigidas por Christopher Nolan'")
    results = chatbot.process_natural_query("Recomiéndame películas de Action dirigidas por Christopher Nolan", limit=5)
    show_recommendations(results)

    print("\nProcesando consulta: 'Recomiéndame películas parecida a Superman'")
    results = chatbot.process_natural_query("Recomiéndame películas parecida a Superman", limit=5)
    show_recommendations(results)

    user_id = 79
    print(f"\nRecomendaciones personalizadas para el usuario {user_id}:")
    results = system.generate_personalized_recommendations(user_id, limit=5)
    show_recommendations(results)

    connector.close()
    return results


if __name__ == "__main__":
    main()