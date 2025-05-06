import requests
import json
from typing import Generator


class OllamaClient:
    """
    Cliente para la comunicación con la API de Ollama.
    """

    def __init__(self, model_name="gemma3:4b", api_url="http://localhost:11434/api/generate"):
        """
        Inicializa el cliente de Ollama.

        Args:
            model_name: El nombre del modelo a usar (por defecto es "gemma3:4b")
            api_url: URL de la API de Ollama
        """
        self.model_name = model_name
        self.api_url = api_url

    def generate_response_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Envía el prompt a Ollama y obtiene la respuesta en modo stream.

        Args:
            prompt: El prompt completo a enviar

        Yields:
            Fragmentos de texto de la respuesta generada por el modelo
        """
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True
            }

            response = requests.post(self.api_url, json=data, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        yield token
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.RequestException as e:
            yield f"Error al comunicarse con Ollama: {str(e)}"

    def generate_response(self, prompt: str) -> str:
        """
        Envía el prompt a Ollama y obtiene la respuesta completa.

        Args:
            prompt: El prompt completo a enviar

        Returns:
            La respuesta generada por el modelo
        """
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }

            response = requests.post(self.api_url, json=data)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "No se pudo generar una respuesta.")

        except requests.exceptions.RequestException as e:
            return f"Error al comunicarse con Ollama: {str(e)}"