import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from recomendador.RecommendationSystem import RecommendationSystem
from recomendador.UserPreferences import UserPreferencesMixin
from recomendador.CriteriaRecommendations import CriteriaRecommendationsMixin
from recomendador.RecommendationGenerator import RecommendationGeneratorMixin

class CompleteRecommendationSystem(
    RecommendationGeneratorMixin,
    CriteriaRecommendationsMixin,
    UserPreferencesMixin,
    RecommendationSystem
):
    """Implementación completa del sistema de recomendaciones que combina todas las funcionalidades."""
    pass

class Neo4jRecommendationSystem(CompleteRecommendationSystem):
    def __init__(self, connector, cache_expiration_time=3600):
        super().__init__(connector, cache_expiration_time)
        self.connector = connector

    def execute_query(self, query, params=None):
        return self.connector.ejecutar_consulta(query, params)