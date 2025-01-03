import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *
from auth import auth_component, sidebar_favorites, favorite_button
from util import (
    COMMON_STYLES,
    generate_tmdb_image_url,
    render_main_movie,
    get_movie_by_title, 
    get_random_movie,
    load_movie_data,
    recommend_movies
)
import streamlit as st
import traceback


# Configuration de la page
st.set_page_config(
    page_title="Pour Vous - Film Recommender",
    page_icon="✨",
    layout="wide",
)

# Ajouter après st.set_page_config
st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #FF5733;
        color: white;
        border-radius: 5px;
        border: none;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #E64A19;
        border: none;
    }
    div[data-testid="stImage"] img {
        border-radius: 8px;
        transition: transform 0.3s;
    }
    div[data-testid="stImage"] img:hover {
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)
        
def main():
    try:
        # Chargement CSS et données
        st.markdown(COMMON_CSS, unsafe_allow_html=True)
        movies_df = load_movie_data()

        # Initialisation des états de session
        if 'random_movie_id' not in st.session_state:
            random_movie = get_random_movie(movies_df)
            st.session_state.random_movie_id = random_movie['tmdb_id']
        
        if 'selected_movie_id' not in st.session_state:
            st.session_state.selected_movie_id = st.session_state.random_movie_id
            
        if 'selected_movie' not in st.session_state:
            st.session_state.selected_movie = None

        # Authentification
        user_id = auth_component()

        st.sidebar.divider()

        if user_id:
            sidebar_favorites(movies_df)
            
        st.sidebar.divider()
        
        # Titre de la page
        st.title("✨ Pour Vous")
        
        # Préférences
        st.sidebar.markdown("### ⚙️ Préférences")
        title_lang = st.sidebar.radio(
            "Afficher les titres en",
            ["Titre Original", "Titre Français"],
            key="title_lang_selector"
        )
        
        num_recommendations = st.sidebar.slider(
            "Nombre de recommandations",
            min_value=5,
            max_value=20,
            value=10,
            step=5,
            key="num_recommendations_slider"
        )

        # Sélection du film avec la bonne langue
        titles = movies_df['title_fr'] if title_lang == "Titre Français" else movies_df['title']
        titles = titles.dropna().sort_values().unique().tolist()
        
        # Trouver le titre correspondant au film actuel dans la langue sélectionnée
        current_movie = movies_df[movies_df['tmdb_id'] == st.session_state.selected_movie_id].iloc[0]
        default_title = current_movie['title_fr'] if title_lang == "Titre Français" else current_movie['title']
        
        reference_movie = st.selectbox(
            "Choisir un film",
            options=titles,
            index=titles.index(default_title) if default_title in titles else 0,
            key="movie_selector"
        )

        # Ajouter un bouton pour obtenir un nouveau film aléatoire
        if st.button("🎲 Film aléatoire", key="random_movie_button"):
            random_movie = get_random_movie(movies_df)
            st.session_state.random_movie_id = random_movie['tmdb_id']
            st.session_state.selected_movie_id = random_movie['tmdb_id']
            st.rerun()

        # Gérer la sélection manuelle d'un film
        if reference_movie != default_title:
            selected = get_movie_by_title(movies_df, reference_movie, title_lang)
            if selected is not None:
                st.session_state.selected_movie_id = selected['tmdb_id']
                st.session_state.selected_movie = None

        # Gérer la sélection via sidebar ou "Watch Now"
        if st.session_state.selected_movie is not None:
            if isinstance(st.session_state.selected_movie, dict):
                movie_title = st.session_state.selected_movie['title']
            else:
                movie_title = st.session_state.selected_movie
                
            selected = get_movie_by_title(movies_df, movie_title, "Titre Original")
            if selected is not None:
                st.session_state.selected_movie_id = selected['tmdb_id']
            st.session_state.selected_movie = None

        # Afficher le film et les recommandations
        current_movie = movies_df[movies_df['tmdb_id'] == st.session_state.selected_movie_id].iloc[0]
        render_main_movie(current_movie, title_lang)
        
        # Calculer et afficher les recommandations
        recommended_movies = recommend_movies(current_movie['title'], movies_df, num_recommendations)
        
        st.markdown("---")
        st.markdown("""
            <div style='padding: 20px 0;'>
                <h2>Films similaires recommandés</h2>
                <div style='margin: 30px 0;'></div>
            </div>
        """, unsafe_allow_html=True)
            
        # Dans la boucle d'affichage des recommandations
        for i in range(0, len(recommended_movies), 5):
            cols = st.columns(5)
            for j, (_, movie) in enumerate(recommended_movies[i:i+5].iterrows()):
                with cols[j]:
                    display_title = movie['title_fr'] if title_lang == "Titre Français" else movie['title']
                    poster_url = generate_tmdb_image_url(movie['poster_path'])

                    # Afficher l'image et les infos en dessous du bouton
                    st.markdown(f"""
                        <div style='margin-top: 0px; padding: 10px; text-align: center;'>
                            <div style='position: relative; width: 100%; padding-top: 150%; margin-bottom: 10px;'>
                                <img src='{poster_url}' 
                                    style='position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; border-radius: 8px; cursor: pointer;'
                                    onclick="selectMovie('{movie['title']}')"
                                >
                            </div>
                            <div style='margin-bottom: 5px;'><strong>{movie['title']}</strong> ({movie['release_year']})</div>
                            <div style='color: gray; font-size: 0.8em; margin-bottom: 5px;'>{movie['director']}</div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Ajouter un bouton invisible qui sera déclenché par le clic sur l'image
                    if st.button(
                        "Voir",
                        key=f"img_{movie['tmdb_id']}_{i}_{j}",
                        use_container_width=True,
                        type="secondary",
                        help=f"Voir les détails de {display_title}",
                        # Le rendre invisible avec du CSS
                        args=('style', 'display: none;')
                    ):
                        st.session_state.selected_movie = movie['title']
                        st.rerun()
                    
                    # Bouton favori en bas
                    favorite_button(
                        movie['tmdb_id'],
                        movie['title'],
                        f"rec_{movie['tmdb_id']}",
                        f"{i}_{j}"
                    )

                        
    
    except Exception as e:
        st.error(f"❌ Une erreur s'est produite : {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
   main()

# Footer
st.markdown("---")
footer_col1, footer_col2 = st.columns([3, 1])
with footer_col1:
   st.markdown("Développé avec ❤️ par Lucas Meireles, Farid El Fardi, Elisabeth Tran, Anais Cid")
   st.caption("© 2024 Film Recommender | Tous droits réservés")

with footer_col2:
   st.markdown("""
        <div style='text-align: right;'>
            <a href='https://github.com/Lu6asM/film-recommender' target='_blank'>
                <svg width='25' height='25' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'>
                    <path d='M50 5C25.147 5 5 25.147 5 50c0 19.87 12.87 36.723 30.804 42.656 2.25.418 3.079-.975 3.079-2.163 0-1.071-.041-4.616-.06-8.356-12.537 2.727-15.185-5.285-15.185-5.285-2.05-5.207-5.004-6.594-5.004-6.594-4.09-2.797.309-2.74.309-2.74 4.525.32 6.907 4.646 6.907 4.646 4.019 6.885 10.543 4.895 13.107 3.742.405-2.91 1.572-4.896 2.862-6.024-10.014-1.14-20.545-5.006-20.545-22.283 0-4.923 1.76-8.944 4.644-12.102-.467-1.137-2.013-5.722.436-11.926 0 0 3.787-1.213 12.407 4.624 3.598-1.001 7.46-1.502 11.295-1.518 3.834.016 7.698.517 11.301 1.518 8.614-5.837 12.396-4.624 12.396-4.624 2.454 6.204.91 10.789.443 11.926 2.89 3.158 4.64 7.179 4.64 12.102 0 17.327-10.546 21.132-20.583 22.25 1.616 1.396 3.057 4.14 3.057 8.345 0 6.026-.053 10.878-.053 12.366 0 1.2.814 2.604 3.095 2.163C82.145 86.714 95 69.87 95 50 95 25.147 74.853 5 50 5z' fill='#333'/>
                </svg>
            </a>
            <a href='https://film-recommender-appviz.streamlit.app/' target='_blank' style='margin-left: 10px;'>
                <svg width='25' height='25' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'>
                    <rect x='10' y='60' width='15' height='30' fill='#2196F3'/>
                    <rect x='32' y='40' width='15' height='50' fill='#4CAF50'/>
                    <rect x='54' y='20' width='15' height='70' fill='#FFC107'/>
                    <rect x='76' y='30' width='15' height='60' fill='#9C27B0'/>
                    <path d='M17 55 L40 35 L62 15 L84 25' stroke='#FF5722' stroke-width='3' fill='none'/>
                    <circle cx='17' cy='55' r='3' fill='#FF5722'/>
                    <circle cx='40' cy='35' r='3' fill='#FF5722'/>
                    <circle cx='62' cy='15' r='3' fill='#FF5722'/>
                    <circle cx='84' cy='25' r='3' fill='#FF5722'/>
                </svg>
            </a>
        </div>
        """, unsafe_allow_html=True)