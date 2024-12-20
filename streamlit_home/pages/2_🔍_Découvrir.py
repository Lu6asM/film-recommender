import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *
from auth import auth_component, sidebar_favorites, favorite_button
from util import (
    COMMON_STYLES,
    render_main_movie,
    recherche_films,
    load_movie_data,
)
import streamlit as st
import traceback

# Configuration de la page
st.set_page_config(
    page_title="Explorer - Film Recommender",
    page_icon="🔍",
    layout="wide",
)

def main():
    try:
        # Chargement CSS et données
        st.markdown(COMMON_CSS, unsafe_allow_html=True)
        movies_df = load_movie_data()

        # Authentification
        user_id = auth_component()

        st.sidebar.divider()

        if user_id:
            sidebar_favorites(movies_df)
        
        # Titre de l'application
        st.title("🔍 Explorer")

        # Barre latérale pour les filtres
        st.sidebar.divider()
        
        st.sidebar.markdown("### 🔍 Options de recherche")
        with st.sidebar:
            
            # Sélection des genres
            genres = st.multiselect(
                "Genres",
                options=sorted(set([genre for genres in movies_df['genres'] for genre in genres])),
                help="Sélectionnez un ou plusieurs genres"
            )
            
            # Note minimale
            note_min = st.slider(
                "Note minimale",
                min_value=0.0,
                max_value=10.0,
                value=7.0,
                step=0.5,
                help="Sélectionnez la note minimale (moyenne IMDB/TMDB)"
            )
            
            # Sélection de la décennie
            decennie = st.selectbox(
                "Décennie",
                options=[""] + sorted(movies_df['decade'].unique().tolist()),
                help="Filtrer par décennie"
            )
            
            # Durée maximale
            duree_max = st.slider(
                "Durée maximale (minutes)",
                min_value=0,
                max_value=int(movies_df['runtime'].max()),
                value=int(movies_df['runtime'].max()),
                step=30,
                help="Sélectionnez la durée maximale du film"
            )

        # Bouton de recherche
        if st.sidebar.button("Rechercher", type="primary", use_container_width=True):
            # Filtrage des films
            filtered_df = recherche_films(
                movies_df,
                genres=genres,
                note_min=note_min,
                decennie=decennie if decennie != "" else None,
                duree_max=duree_max
            )
            
            # Affichage des résultats
            if not filtered_df.empty:
                st.success(f"📽️ {len(filtered_df)} films trouvés")
                
                # Options de tri
                sort_options = {
                    "Note IMDB (décroissant)": ("imdb_rating", False),
                    "Note TMDB (décroissant)": ("tmdb_rating", False),
                    "Date de sortie (plus récent)": ("release_date", False),
                    "Date de sortie (plus ancien)": ("release_date", True),
                    "Durée (croissant)": ("runtime", True),
                    "Durée (décroissant)": ("runtime", False),
                }
                
                sort_by = st.selectbox("Trier par:", options=list(sort_options.keys()))
                sort_column, ascending = sort_options[sort_by]
                filtered_df = filtered_df.sort_values(by=sort_column, ascending=ascending)
                
                # Affichage des films
                for _, movie in filtered_df.iterrows():
                    render_main_movie(movie, title_lang='fr')
            else:
                st.warning("🔍 Aucun film ne correspond à vos critères de recherche.")
    
    except FileNotFoundError:
        st.error("❌ Fichier de données introuvable. Veuillez vérifier le chemin du fichier.")
    except Exception as e:
        st.error(f"❌ Une erreur s'est produite : {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
    main()

# Footer
st.markdown("---")
st.caption("Développé avec ❤️ par Lucas Meireles, Farid El Fardi, Elisabeth Tran")
st.caption("© 2024 Film Recommender | Tous droits réservés")