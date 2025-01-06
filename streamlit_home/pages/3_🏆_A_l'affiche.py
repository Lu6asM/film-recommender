import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *
from auth import auth_component, sidebar_favorites, favorite_button
from util import (
    render_movie_with_rank,
    load_movie_data,
)
import streamlit as st
import traceback

# Configuration de la page
st.set_page_config(
    page_title="Trending - Film Recommender",
    page_icon="🏆",
    layout="wide",
)


def main():
    try:
        # Chargement CSS et données
        st.markdown(COMMON_CSS, unsafe_allow_html=True)
        movies_df = load_movie_data()

        # Authentification
        user_id = auth_component()


        if user_id:
            st.sidebar.divider()
            sidebar_favorites(movies_df)

        # Titre principal
        st.title("🏆 A l'affiche")

        # Configuration d'affichage (sidebar)
        st.sidebar.divider()
        st.sidebar.markdown("### 🔄 Options d'affichage")

        tri_options = {
            "Note moyenne": "average_rating",
            "Box Office": "box_office_millions",
            "Plus récents": "release_year"
        }

        tri_choix = st.sidebar.selectbox(
            "Trier par :",
            options=list(tri_options.keys())
        )

        nombre_films = st.sidebar.slider(
            "Nombre de films à afficher",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )

        # Trier les films selon le critère choisi
        sort_column = tri_options[tri_choix]
        sorted_df = movies_df.sort_values(by=sort_column, ascending=False)

        # Affichage des films
        st.info(f"📽️ Top {nombre_films} des films triés par {tri_choix}")
        for rank, (_, movie) in enumerate(sorted_df.head(nombre_films).iterrows(), 1):
            render_movie_with_rank(movie=movie, title_lang='fr', rank=rank)

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