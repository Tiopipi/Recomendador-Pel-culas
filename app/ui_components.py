import streamlit as st
from app.auth import logout_user


def load_css():
    """Carga los estilos CSS para la aplicación."""
    st.markdown("""
    <style>
        .movie-results {
            background-color: #f7f7f9;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .movie-card {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s ease-in-out;
        }
        .movie-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .movie-title {
            font-weight: bold;
            font-size: 18px;
            color: #1e3a8a;
            margin-bottom: 5px;
        }
        .movie-info {
            margin-top: 8px;
            font-size: 14px;
            color: #4b5563;
        }
        .movie-score {
            color: #047857;
            font-weight: 500;
        }
        .auth-form {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 450px;
            margin: 0 auto;
        }
        .auth-tab {
            margin-bottom: 20px;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 20px;
            color: #1e3a8a;
        }
        .stButton > button {
            width: 100%;
        }
        .rating-container {
            display: flex;
            align-items: center;
            margin-top: 5px;
            margin-bottom: 15px;
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .rating-movie {
            flex-grow: 1;
            font-weight: 500;
        }
        .rating-stars {
            display: flex;
            justify-content: flex-end;
        }
        .add-more-btn {
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)


def display_movie_results(movies):
    """Muestra los resultados de películas en tarjetas organizadas."""
    if not movies:
        return

    st.markdown("<div class='movie-results'>", unsafe_allow_html=True)
    st.markdown("### 🎬 Películas recomendadas")
    cols = st.columns(3)

    for i, movie in enumerate(movies[:9]):
        col = cols[i % 3]
        titulo = movie.get('titulo', 'Desconocido')
        anio = movie.get('año', '?')
        dur = movie.get('Duration', movie.get('duracion', '?'))
        mpa = movie.get('MPA', '')
        votes = movie.get('Votes', '')
        budget = movie.get('budget', 'N/A')
        gross = movie.get('grossWorldWide', 'N/A')
        stars = movie.get('stars', []) if isinstance(movie.get('stars', []), list) else []
        genres = movie.get('genres', []) if isinstance(movie.get('genres', []), list) else []
        avg = movie.get('promedio_valoracion', 0.0)

        with col:
            st.markdown(f"""
            <div class="movie-card">
                <div class="movie-title">{titulo} ({anio})</div>
                <div class="movie-info"><strong>Duración:</strong> {dur}</div>
                <div class="movie-info"><strong>MPA:</strong> {mpa}</div>
                <div class="movie-info"><strong>Géneros:</strong> {', '.join(genres[:3])}</div>
                <div class="movie-info"><strong>Valoración:</strong> {avg:.2f}/5 ({votes})</div>
                <div class="movie-info"><strong>Recaudación mundial:</strong> ${gross}</div>
                <div class="movie-info"><strong>Presupuesto:</strong> ${budget}</div>
                <div class="movie-info"><strong>Reparto:</strong> {', '.join(stars[:3])}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def show_sidebar(process_input_callback):
    """Muestra la barra lateral con opciones y ejemplos."""
    with st.sidebar:
        st.markdown(f"### 🎬 CineBot - {st.session_state.current_username}")
        st.markdown("### ⚙️ Opciones")

        if st.button("🔄 Reiniciar Chat", key="reset_button"):
            st.session_state.messages = []
            st.session_state.input_key += 1
            st.rerun()

        if st.button("⭐ Actualizar valoraciones", key="update_ratings"):
            st.session_state.preferences_completed = False
            st.session_state.is_new_user = True
            st.rerun()

        if st.button("🚪 Cerrar Sesión", key="logout_button"):
            success, msg = logout_user()
            if success:
                st.success(msg)
                st.rerun()

        st.markdown("---")
        st.markdown("### 💡 Ejemplos de consultas")

        example_queries = [
            "Recomiéndame películas de acción con buenas valoraciones",
            "¿Cuáles son las mejores películas de Christopher Nolan?",
            "Busco películas de comedia romántica de los años 90",
            "Quiero ver una película de acción que no dure más de 2 horas"
        ]

        for i, query in enumerate(example_queries):
            if st.button(f"📝 {query}...", key=f"example_{i}"):
                process_input_callback(query)
                st.rerun()

        st.markdown("---")
        st.markdown("""
                ### ℹ️ Acerca de
                Este chatbot utiliza Neo4j para recomendar películas basándose en tus valoraciones previas.

                Puedes preguntar por:
                - Géneros específicos
                - Directores
                - Películas similares
                - Combinaciones de criterios
                """)


def configure_page():
    """Configura las propiedades básicas de la página."""
    st.set_page_config(
        page_title="Movie Recommendation Chatbot",
        page_icon="🎬",
        layout="wide"
    )
    load_css()