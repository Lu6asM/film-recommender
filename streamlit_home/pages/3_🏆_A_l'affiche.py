from config import *
from auth import auth_component, sidebar_favorites, favorite_button
import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import traceback

# Configuration de la page
st.set_page_config(
    page_title="Trending - Film Recommender",
    page_icon="🏆",
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

@st.cache_data
def get_person_id(name):
    url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={name}&language=fr"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['id']  # Retourne l'ID du premier résultat
    return None  # Retourne None si non trouvé

def generate_tmdb_person_image_url(person_id):
    url = f"https://api.themoviedb.org/3/person/{person_id}?api_key={TMDB_API_KEY}&language=fr"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        profile_path = data.get('profile_path')
        if profile_path:
            return generate_tmdb_image_url(profile_path, size='w500')
    return "https://via.placeholder.com/500x750.png?text=No+Image"  # Image par défaut si pas d'image trouvée

# Fonctions utilitaires
def generate_tmdb_image_url(file_path, size='w500'):
    if not file_path or pd.isna(file_path):
        return "https://via.placeholder.com/500x750.png?text=No+Image"
    file_path = file_path.lstrip('/')
    size = size if size in VALID_POSTER_SIZES else 'w500'
    return f"{TMDB_BASE_URL}{size}/{file_path}"

def format_currency(value):
    return "Non disponible" if pd.isna(value) else f"{value:,.2f}M $"

def format_duration(minutes):
    if pd.isna(minutes):
        return "Non disponible"
    return f"{minutes // 60}h {minutes % 60:02d}min"

def clean_name(name):
    """Nettoie et formate un nom"""
    return name.strip().replace(',', ', ')

def parse_actor_info(actor_list):
    """
    Parse le format "Meg Ryan (Kate McKay), Hugh Jackman (Leopold)"
    Retourne une liste de tuples (nom_acteur, role)
    """
    if not isinstance(actor_list, str):
        return []
        
    actors = []
    # Split sur la virgule suivie d'un espace
    for actor in actor_list.split(', '):
        try:
            # Séparer le nom et le rôle
            name_part = actor.split(' (')
            if len(name_part) == 2:
                name = name_part[0]
                role = name_part[1].rstrip(')')  # Enlever la parenthèse finale
                actors.append((name, role))
            else:
                # Si pas de rôle spécifié
                actors.append((actor, ""))
        except:
            continue
    return actors

# Chargement des données
@st.cache_data
def load_movie_data(file_path=CSV_URL):
    try:
        df = pd.read_csv(file_path)
        
        # Renommer les colonnes
        df = df.rename(columns=COLUMN_MAPPING)
        
        # Traiter les colonnes de type liste
        list_columns = ['genres', 'countries', 'keywords', 'companies']
        for col in list_columns:
            df[col] = df[col].str.split(', ')

        # Traitement spécial pour les acteurs
        df['actors'] = df['actors'].apply(parse_actor_info)
        
        # Traiter les données numériques
        df['release_year'] = pd.to_datetime(df['release_date']).dt.year
        df['box_office_millions'] = pd.to_numeric(df['box_office'], errors='coerce') / 1_000_000
        df['budget_millions'] = pd.to_numeric(df['budget'], errors='coerce') / 1_000_000
        df['average_rating'] = (df['tmdb_rating'].astype(float) + df['imdb_rating'].astype(float)) / 2
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {str(e)}")
        return pd.DataFrame()

def recherche_films(df, genres=None, note_min=0, decennie=None, langue=None, duree_max=None):
    filtered_df = df.copy()
    
    if genres:
        filtered_df = filtered_df[filtered_df['genres'].apply(lambda x: any(genre in x for genre in genres))]
    
    if note_min > 0:
        filtered_df = filtered_df[
            ((filtered_df['tmdb_rating'].astype(float) + filtered_df['imdb_rating'].astype(float)) / 2) >= note_min
        ]
    
    if decennie:
        filtered_df = filtered_df[filtered_df['decade'] == decennie]
        
    if duree_max:
        filtered_df = filtered_df[filtered_df['runtime'] <= duree_max]
    
    return filtered_df

def render_main_movie(movie, rank):
    """Affiche le film principal en grand format"""
    # Layout principal : poster et infos
    poster_col, main_col, rating_col = st.columns([1, 2, 1])
    


    # Colonne Poster
    with poster_col:
        poster_url = generate_tmdb_image_url(movie['poster_path'])
        st.image(poster_url, use_container_width=True)
        
    # Colonne centrale (info + overview + cast)
    with main_col:
        # Titre
        st.markdown(f"### {movie['title']} ({movie['release_year']})")
        if movie['title'] != movie['title_fr']:
            st.markdown(f"*{movie['title_fr']}*")
        
        # Infos principales sur une ligne
        info_cols = st.columns(2)
        with info_cols[0]:
            st.markdown(f"**Durée :** {format_duration(movie['runtime'])}")
            st.markdown(f"**Genre(s) :** {', '.join(movie['genres'])}")
        
        with info_cols[1]:
            st.markdown(f"**Budget :** {format_currency(movie['budget_millions'])}")
            st.markdown(f"**Box Office :** {format_currency(movie['box_office_millions'])}")
        
        # Synopsis
        st.markdown("---")
        st.markdown("**Synopsis**")
        st.markdown(f"{movie['overview']}")
        
        # Cast et réalisation
        st.markdown("---")
        
        # Titres sur la même ligne
        st.markdown("""
        <div style='display: flex; margin-bottom: 0px;'>
            <div style='flex: 1;'><h4>🎬 Réalisation</h4></div>
            <div style='flex: 0.1;'></div>
            <div style='flex: 5;'><h4>🎭 Têtes d'affiche</h4></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Utiliser 7 colonnes : 1 pour réal, 1 pour séparateur, 5 pour acteurs
        cast_cols = st.columns([1, 0.1, 1, 1, 1, 1, 1])
        
        # Réalisateur
        with cast_cols[0]:
            directors = movie['director'].split(', ') if isinstance(movie['director'], str) else [movie['director']]
            for director in directors[:1]:
                director_id = get_person_id(director)
                director_image_url = generate_tmdb_person_image_url(director_id)
                st.markdown(f"""
                    <div style='text-align: center;'>
                        <img src='{director_image_url}' style='width: 120px; margin-bottom: 10px;'>
                        <div><strong>{clean_name(director)}</strong></div>
                        <div style='color: gray; font-size: 0.9em;'>Réalisateur</div>
                    </div>
                """, unsafe_allow_html=True)

        # Séparateur vertical
        with cast_cols[1]:
            st.markdown("""
                <div style='width: 2px; background-color: #ddd; height: 200px; margin: 0 auto;'></div>
            """, unsafe_allow_html=True)

        # Acteurs dans les 5 dernières colonnes
        actors = movie['actors'][:5] if isinstance(movie['actors'], list) else []
        for idx, (actor, role) in enumerate(actors):
            with cast_cols[idx + 2]:
                actor_id = get_person_id(actor)
                actor_image_url = generate_tmdb_person_image_url(actor_id)
                st.markdown(f"""
                    <div style='text-align: center;'>
                        <img src='{actor_image_url}' style='width: 120px; margin-bottom: 10px;'>
                        <div><strong>{actor}</strong></div>
                        <div style='color: gray; font-size: 0.9em;'>{role}</div>
                    </div>
                """, unsafe_allow_html=True)
        
    st.markdown("---")
    # Colonne Notes (droite)
    with rating_col:
        st.markdown(f"""
            <div style='position: relative; text-align: center;'>
                <h1 style='font-size: 3em; color: #1E88E5; margin: 0;'>#{rank}</h1>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("#### Évaluations")
        st.metric("Note IMDb", f"{movie['imdb_rating']:.1f}/10", f"{movie['imdb_votes']:,} votes")
        st.metric("Note TMDb", f"{movie['tmdb_rating']:.1f}/10", f"{movie['tmdb_votes']:,} votes")
        
        # Petits boutons alignés horizontalement
        st.markdown("---")
        button_cols = st.columns([1, 1, 1])
        with button_cols[0]:
            st.link_button("IMDb", f"https://www.imdb.com/title/{movie['imdb_id']}", use_container_width=True, type="secondary")
        with button_cols[1]:
            st.link_button("TMDb", f"https://www.themoviedb.org/movie/{movie['tmdb_id']}", use_container_width=True, type="secondary")
        with button_cols[2]:
            favorite_button(
                movie['tmdb_id'],
                movie['title'],
                f"rec_{movie['tmdb_id']}",
                "main_view"  # Un identifiant unique pour différencier du reste
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

        # Titre principal
        st.title("✨ Recommander des films")

        # Chargement CSS personnalisé
        st.markdown("""
        <style>
        .stMetric .css-1wivap2 {
            background-color: rgba(28, 131, 225, 0.1);
            border-radius: 8px;
            padding: 10px;
        }
        .stMetric .css-1wivap2 p {
            color: rgb(28, 131, 225);
        }
        </style>
        """, unsafe_allow_html=True)

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
            render_main_movie(movie, rank)

    except Exception as e:
        st.error(f"❌ Une erreur s'est produite : {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
   main()

# Footer
st.markdown("---")
footer_col1, footer_col2 = st.columns([3, 1])
with footer_col1:
   st.markdown("Développé avec ❤️ par Lucas Meireles, Farid El Fardi, Elisabeth Tran")
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