import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from typing import Dict, List, Any, Callable
from app.prompt_builder import MoviePromptBuilder
from app.llm_client import OllamaClient


class MovieRecommendationChatbot:
    """
    Chatbot recomendador de películas que utiliza un generador de prompts y un cliente LLM.
    """

    def __init__(self, model_name="gemma3:4b", api_url="http://localhost:11434/api/generate"):
        """
        Inicializa el chatbot recomendador de películas.

        Args:
            model_name: El nombre del modelo a usar (por defecto es "gemma3:4b")
            api_url: URL de la API de Ollama
        """
        self.prompt_builder = MoviePromptBuilder()
        self.llm_client = OllamaClient(model_name, api_url)
        self.history = []

    def chat(self, query: str, movies_list: List[Dict[str, Any]]) -> str:
        """
        Función principal del chatbot que procesa la consulta y la lista de películas
        para generar recomendaciones.

        Args:
            query: La consulta del usuario
            movies_list: Lista de diccionarios con los resultados de las películas

        Returns:
            La respuesta generada por el modelo
        """
        prompt = self.prompt_builder.build_recommendation_prompt(movies_list, query)

        response = self.llm_client.generate_response(prompt)

        self.history.append({"query": query, "response": response})

        return response

    def chat_stream(self, query: str, movies_list: List[Dict[str, Any]],
                    callback: Callable[[str], None] = None) -> str:
        """
        Función principal del chatbot que procesa la consulta y la lista de películas
        para generar recomendaciones en modo streaming.

        Args:
            query: La consulta del usuario
            movies_list: Lista de diccionarios con los resultados de las películas
            callback: Función opcional que se llama con cada fragmento de texto generado

        Returns:
            La respuesta completa generada por el modelo
        """
        prompt = self.prompt_builder.build_recommendation_prompt(movies_list, query)

        full_response = ""

        for text_chunk in self.llm_client.generate_response_stream(prompt):
            full_response += text_chunk
            if callback:
                callback(text_chunk)

        self.history.append({"query": query, "response": full_response})

        return full_response