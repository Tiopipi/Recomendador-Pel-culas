import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import streamlit as st
from app.similarity_calculator import calculate_similarities_for_new_user


def show_auth_form(db_manager):
    """Muestra el formulario de autenticación con pestañas para inicio de sesión y registro."""
    st.markdown("<h1 class='auth-header'>🎬 CineBot - Tu asistente de cine</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])

    with tab1:
        st.markdown("<div class='auth-form'>", unsafe_allow_html=True)
        st.markdown("<h3 class='auth-tab'>Iniciar Sesión</h3>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Usuario", key="login_username")
            password = st.text_input("Contraseña", type="password", key="login_password")
            submit_login = st.form_submit_button("Iniciar Sesión")

        if submit_login:
            if not username or not password:
                st.error("Por favor, completa todos los campos.")
            else:
                success, user_id, username, ratings, has_preferences, message = db_manager.login_user(username,
                                                                                                      password)
                if success:
                    st.success(message)
                    st.session_state.auth_status = "logged_in"
                    st.session_state.current_username = username
                    st.session_state.user_id = user_id
                    st.session_state.movie_ratings = ratings if ratings else []
                    st.session_state.preferences_completed = has_preferences
                    st.session_state.is_new_user = not has_preferences
                    st.rerun()
                else:
                    st.error(message)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='auth-form'>", unsafe_allow_html=True)
        st.markdown("<h3 class='auth-tab'>Crear una cuenta</h3>", unsafe_allow_html=True)

        with st.form("register_form"):
            new_username = st.text_input("Nombre de usuario", key="reg_username")
            new_email = st.text_input("Correo electrónico", key="reg_email")
            new_password = st.text_input("Contraseña", type="password", key="reg_password")
            confirm_password = st.text_input("Confirmar contraseña", type="password", key="confirm_password")
            submit_register = st.form_submit_button("Registrarse")

        if submit_register:
            if not new_username or not new_email or not new_password or not confirm_password:
                st.error("Por favor, completa todos los campos.")
            elif new_password != confirm_password:
                st.error("Las contraseñas no coinciden.")
            elif len(new_password) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            else:
                success, user_id, message = db_manager.register_user(new_username, new_password, new_email)
                if success:
                    st.success(message)
                    st.session_state.auth_status = "logged_in"
                    st.session_state.current_username = new_username
                    st.session_state.user_id = user_id
                    st.session_state.movie_ratings = []
                    st.session_state.is_new_user = True
                    st.session_state.preferences_completed = False
                    st.rerun()
                else:
                    st.error(message)
        st.markdown("</div>", unsafe_allow_html=True)


def logout_user():
    """Cierra la sesión del usuario actual y limpia los estados de sesión."""
    st.session_state.auth_status = None
    st.session_state.current_username = None
    st.session_state.user_id = None
    st.session_state.preferences_completed = False
    st.session_state.messages = []
    st.session_state.movie_ratings = []
    st.session_state.is_new_user = False
    return True, "Sesión cerrada correctamente."


def process_user_ratings(db_manager, user_id, movie_ratings):
    """Procesa y guarda las valoraciones del usuario y calcula similitudes."""
    try:
        success, message = db_manager.save_movie_ratings(user_id, movie_ratings)
        if not success:
            return False, message

        if len(movie_ratings) >= 3:
            with st.spinner("Calculando recomendaciones personalizadas..."):
                similitudes_count = calculate_similarities_for_new_user(
                    db_manager.connector,
                    user_id,
                    movie_ratings
                )
                if similitudes_count > 0:
                    st.success(f"¡Se encontraron {similitudes_count} usuarios con gustos similares!")

        return True, "¡Valoraciones guardadas exitosamente! Ahora puedes usar el chatbot."
    except Exception as e:
        return False, f"Error al procesar las valoraciones: {str(e)}"