import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
import streamlit as st
from app.auth import process_user_ratings


def add_movie_rating():
    """Añade una película y su valoración a la lista temporal."""
    if st.session_state.movie_select and st.session_state.movie_select not in [m['pelicula'] for m in
                                                                               st.session_state.movie_ratings]:
        st.session_state.movie_ratings.append({
            'pelicula': st.session_state.movie_select,
            'valoracion': st.session_state.rating_value
        })


def remove_movie_rating(index):
    """Elimina una película de la lista de valoraciones."""
    if 0 <= index < len(st.session_state.movie_ratings):
        del st.session_state.movie_ratings[index]


def show_movie_rating_form(db_manager):
    """Muestra el formulario para que los usuarios valoren películas."""
    st.header(f"Bienvenido, {st.session_state.current_username}! 👋")
    st.write(
        "Para obtener mejores recomendaciones, indica las películas que has visto y tu valoración para cada una (de 1 a 5 estrellas). Al menos debes de elegir 5 películas.")

    peliculas_existentes = db_manager.get_peliculas_options()

    if st.session_state.movie_ratings:
        st.subheader("Tus valoraciones:")
        for i, rating in enumerate(st.session_state.movie_ratings):
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"""
                <div class="rating-container">
                    <span class="rating-movie">{rating['pelicula']}</span>
                    <span class="rating-stars">{'⭐' * rating['valoracion']}</span>
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                if st.button("Eliminar", key=f"remove_{i}"):
                    remove_movie_rating(i)
                    st.rerun()

    st.subheader("Añadir película:")
    col1, col2 = st.columns([3, 1])

    with col1:
        if 'movie_select' not in st.session_state:
            st.session_state.movie_select = None

        st.selectbox("Selecciona una película:",
                     options=[None] + peliculas_existentes,
                     key="movie_select",
                     index=0)

    with col2:
        if 'rating_value' not in st.session_state:
            st.session_state.rating_value = 3

        st.select_slider("Valoración:",
                         options=[1, 2, 3, 4, 5],
                         value=st.session_state.rating_value,
                         key="rating_value",
                         format_func=lambda x: "⭐" * x)

    if st.button("Añadir película", key="add_movie"):
        add_movie_rating()
        st.rerun()

    if st.button("Guardar valoraciones y continuar", type="primary"):
        success, message = process_user_ratings(
            db_manager,
            st.session_state.user_id,
            st.session_state.movie_ratings
        )

        if success:
            st.session_state.preferences_completed = True
            st.session_state.is_new_user = False
            st.success(message)
            st.rerun()
        else:
            st.error(message)