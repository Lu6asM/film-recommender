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
    page_title="Explorer - Film Recommender",
    page_icon="🔍",
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

def recherche_films(df, genres=None, note_min=0, decennie=None, duree_max=None):
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

def render_main_movie(movie, title_lang):
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
        display_title = movie['title_fr'] if title_lang == "Titre Français" else movie['title']
        st.markdown(f"### {display_title} ({movie['release_year']})")
        
        if movie['title'] != movie['title_fr']:
            other_title = movie['title'] if title_lang == "Titre Français" else movie['title_fr']
            st.markdown(f"<p style='color: gray; font-style: italic;'>{other_title}</p>", unsafe_allow_html=True)
        
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