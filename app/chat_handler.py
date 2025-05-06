import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import streamlit as st
from app.ui_components import display_movie_results
from app.movie_chatbot import MovieRecommendationChatbot


class ChatHandler:
    def __init__(self, db_manager):
        """Inicializa el manejador de chat con el gestor de base de datos."""
        self.db_manager = db_manager
        self.chatbot = MovieRecommendationChatbot()

    def process_input(self, user_input):
        """Procesa la entrada del usuario y genera una respuesta."""
        if not user_input or st.session_state.streaming:
            return

        st.session_state.streaming = True
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        full_response = ""
        try:
            results = self.db_manager.get_movie_recommendations(
                user_input, st.session_state.user_id
            )

            with st.chat_message("assistant"):
                placeholder = st.empty()

                def update_stream(chunk):
                    nonlocal full_response
                    full_response += chunk
                    placeholder.write(full_response)

                complete = self.chatbot.chat_stream(
                    user_input, results, update_stream
                )
                placeholder.write(complete)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": complete,
                    "movies": results
                })

                if results:
                    display_movie_results(results)

        except Exception as e:
            err = f"Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": err, "movies": []})
            with st.chat_message("assistant"):
                st.write(err)

        st.session_state.streaming = False
        st.session_state.input_key += 1

    def display_chat_history(self):
        """Muestra el historial de conversación."""
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant" and "movies" in msg and msg["movies"]:
                    display_movie_results(msg["movies"])

    def get_user_input(self):
        """Obtiene y procesa la entrada del usuario desde la interfaz de chat."""
        user_input = st.chat_input("Escribe tu mensaje...")
        if user_input:
            self.process_input(user_input)
            st.rerun()