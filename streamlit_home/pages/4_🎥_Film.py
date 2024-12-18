import streamlit as st
import pandas as pd
from auth import auth_component, sidebar_favorites, favorite_button

st.set_page_config(
    page_title="Film - Film Recommender",
    page_icon="🎥",
    layout="wide",
)

def format_currency(value):
    if pd.isna(value):
        return "Non disponible"
    return f"{value:,.2f}M $"

def format_duration(minutes):
    if pd.isna(minutes):
        return "Non disponible"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes:02d}min"

def generate_tmdb_image_url(file_path, size='w500'):
    if not file_path or pd.isna(file_path):
        return "https://via.placeholder.com/500x750.png?text=No+Image"
    file_path = file_path.lstrip('/')
    base_url = "https://image.tmdb.org/t/p/"
    valid_sizes = ['w92', 'w154', 'w185', 'w342', 'w500', 'w780', 'original']
    size = size if size in valid_sizes else 'w500'
    return f"{base_url}{size}/{file_path}"

def afficher_details_film(movie):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Affiche du film
        poster_url = generate_tmdb_image_url(movie['Affiche'])
        st.image(poster_url, use_column_width=True)
        
        # Bouton favoris
        favorite_button(movie['ID tmdb'], movie['Titre Original'], "detail")
        
        # Métriques
        st.metric("Note IMDB", f"{movie['Note imdb']:.1f}/10", f"{movie['Votes imdb']:,} votes")
        st.metric("Note TMDB", f"{movie['Note tmdb']:.1f}/10", f"{movie['Votes tmdb']:,} votes")
    
    with col2:
        # En-tête
        st.title(movie['Titre Original'])
        if movie['Titre Original'] != movie['Titre Français']:
            st.markdown(f"*{movie['Titre Français']}*")
        
        # Informations principales
        st.markdown("### ℹ️ Informations")
        info_cols = st.columns(2)
        
        with info_cols[0]:
            st.markdown(f"**Date de sortie :** {pd.to_datetime(movie['Date de Sortie']).strftime('%d/%m/%Y')}")
            st.markdown(f"**Durée :** {format_duration(movie['Durée'])}")
            st.markdown(f"**Genre(s) :** {', '.join(movie['genres'])}")
            st.markdown(f"**Langue(s) :** {', '.join(movie['langues'])}")
        
        with info_cols[1]:
            st.markdown(f"**Budget :** {format_currency(movie['budget_millions'])}")
            st.markdown(f"**Box Office :** {format_currency(movie['box_office_millions'])}")
            st.markdown(f"**Pays :** {', '.join(movie['pays'])}")
            st.markdown(f"**Réputation :** {movie['Réputation']}")
        
        # Synopsis
        st.markdown("### 📝 Synopsis")
        st.markdown(movie['Synopsis'])
        
        # Distribution
        st.markdown("### 👥 Distribution")
        cast_cols = st.columns(2)
        
        with cast_cols[0]:
            st.markdown("**Réalisateur(s) :**")
            for real in movie['Réalisateur(s)'].split(', '):
                st.markdown(f"- {real}")
        
        with cast_cols[1]:
            with st.expander("Voir les acteurs"):
                for acteur in movie['Acteurs'].split(', '):
                    st.markdown(f"- {acteur}")
        
        # Liens externes
        st.markdown("### 🔗 Liens")
        link_cols = st.columns([1, 1, 4])
        with link_cols[0]:
            st.link_button("🎬 IMDb", f"https://www.imdb.com/title/{movie['ID imdb']}", use_container_width=True)
        with link_cols[1]:
            st.link_button("🎥 TMDb", f"https://www.themoviedb.org/movie/{movie['ID tmdb']}", use_container_width=True)

def main():
    # Charger les données
    movies_df = pd.read_csv('https://raw.githubusercontent.com/Lu6asM/film-recommender/refs/heads/main/data/processed/df_movie_cleaned.csv')
    
    # Authentification
    user_id = auth_component()
    if user_id:
        sidebar_favorites(movies_df)
    
    # Vérifier si un ID de film est passé dans l'URL
    params = st.experimental_get_query_params()
    movie_id = params.get('id', [None])[0]
    
    if movie_id:
        # Afficher les détails du film
        movie = movies_df[movies_df['ID tmdb'] == movie_id].iloc[0]
        afficher_details_film(movie)
    else:
        st.warning("Aucun film sélectionné. Veuillez choisir un film depuis vos favoris ou la recherche.")

if __name__ == "__main__":
    main()