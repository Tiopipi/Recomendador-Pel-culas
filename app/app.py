import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import streamlit as st
from app.database import DatabaseManager
from app.auth import show_auth_form
from app.movie_ratings import show_movie_rating_form
from app.ui_components import configure_page, show_sidebar
from app.chat_handler import ChatHandler


def initialize_session_state():
    """Inicializa las variables de estado de sesión si no existen."""
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()

    if 'chat_handler' not in st.session_state:
        st.session_state.chat_handler = ChatHandler(st.session_state.db_manager)

    st.session_state.setdefault('messages', [])
    st.session_state.setdefault('streaming', False)
    st.session_state.setdefault('input_key', 0)
    st.session_state.setdefault('is_new_user', False)
    st.session_state.setdefault('auth_status', None)
    st.session_state.setdefault('current_username', None)
    st.session_state.setdefault('user_id', None)
    st.session_state.setdefault('preferences_completed', False)
    st.session_state.setdefault('movie_ratings', [])
    st.session_state.setdefault('selected_movies', [])


def main():
    """Función principal que maneja el flujo de la aplicación."""
    configure_page()

    initialize_session_state()

    if hasattr(st.session_state.db_manager, 'connection_error') and st.session_state.db_manager.connection_error:
        st.error(f"Error de conexión a Neo4j: {st.session_state.db_manager.connection_error}")
        st.stop()

    if st.session_state.auth_status != "logged_in":
        show_auth_form(st.session_state.db_manager)
        st.stop()

    if st.session_state.is_new_user and not st.session_state.preferences_completed:
        show_movie_rating_form(st.session_state.db_manager)
        st.stop()

    show_sidebar(st.session_state.chat_handler.process_input)

    st.session_state.chat_handler.display_chat_history()

    st.session_state.chat_handler.get_user_input()


if __name__ == "__main__":
    main()