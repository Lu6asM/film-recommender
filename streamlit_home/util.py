from config import *
from auth import auth_component, sidebar_favorites, favorite_button
import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Fonctions de données et de recherche
def get_movie_by_title(movies_df, title, title_lang):
    """Recherche un film par son titre en tenant compte de la langue sélectionnée"""
    if title_lang == "Titre Français":
        filtered_df = movies_df[movies_df['title_fr'] == title]
        if not filtered_df.empty:
            return filtered_df.iloc[0]
    else:  # Titre Original
        filtered_df = movies_df[movies_df['title'] == title]
        if not filtered_df.empty:
            return filtered_df.iloc[0]
    return None

def get_random_movie(movies_df):
    """Sélectionne un film aléatoire dans le DataFrame"""
    return movies_df.sample(n=1).iloc[0]

def recherche_films(df, genres=None, note_min=0, decennie=None, duree_max=None):
    """Recherche avancée de films avec plusieurs critères"""
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

# Fonctions API TMDb
@st.cache_data
def get_person_id(name):
    """Récupère l'ID d'une personne via l'API TMDb"""
    url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={name}&language=fr"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['id']
    return None

def generate_tmdb_person_image_url(person_id):
    """Génère l'URL de l'image d'une personne"""
    url = f"https://api.themoviedb.org/3/person/{person_id}?api_key={TMDB_API_KEY}&language=fr"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        profile_path = data.get('profile_path')
        if profile_path:
            return generate_tmdb_image_url(profile_path, size='w500')
    return "https://via.placeholder.com/500x750.png?text=No+Image"

def generate_tmdb_image_url(file_path, size='w500'):
    """Génère l'URL d'une image TMDb"""
    if not file_path or pd.isna(file_path):
        return "https://via.placeholder.com/500x750.png?text=No+Image"
    file_path = file_path.lstrip('/')
    size = size if size in VALID_POSTER_SIZES else 'w500'
    return f"{TMDB_BASE_URL}{size}/{file_path}"

def get_trailer_url(tmdb_id, api_key):
    """Récupère l'URL de la bande-annonce d'un film"""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={api_key}&language=fr"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        for video in data.get('results', []):
            if video['type'] == 'Trailer':
                return f"https://www.youtube.com/embed/{video['key']}"
    return None

# Fonctions de formatage
def format_currency(value):
    """Formate une valeur monétaire"""
    return "Non disponible" if pd.isna(value) else f"{value:,.2f}M $"

def format_duration(minutes):
    """Formate une durée en heures et minutes"""
    if pd.isna(minutes):
        return "Non disponible"
    return f"{minutes // 60}h {minutes % 60:02d}min"

def clean_name(name):
    """Nettoie et formate un nom"""
    return name.strip().replace(',', ', ')

def parse_actor_info(actor_list):
    """Parse les informations des acteurs"""
    if not isinstance(actor_list, str):
        return []
        
    actors = []
    for actor in actor_list.split(', '):
        try:
            name_part = actor.split(' (')
            if len(name_part) == 2:
                name = name_part[0]
                role = name_part[1].rstrip(')')
                actors.append((name, role))
            else:
                actors.append((actor, ""))
        except:
            continue
    return actors

# Chargement et préparation des données
@st.cache_data
def load_movie_data(file_path=CSV_URL):
    """Charge et prépare les données des films"""
    try:
        df = pd.read_csv(file_path)
        
        # Renommer les colonnes
        df = df.rename(columns=COLUMN_MAPPING)
        
        # Traiter les colonnes de type liste
        list_columns = ['genres', 'countries', 'languages', 'keywords', 'companies']
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

# Système de recommandation
@st.cache_data
def recommend_movies(movie_title, movies_df, k=5):
    """Système de recommandation de films"""
    with st.spinner("Calcul des recommandations en cours..."):
        feature_mapping = {
            'genres': 0.4,
            'keywords': 0.2, 
            'director': 0.15,
            'actors': 0.15,
            'overview': 0.1
        }

        if movie_title not in movies_df['title'].values:
            raise ValueError(f"Le film '{movie_title}' n'est pas dans la base de données.")

        ref_movie = movies_df[movies_df['title'] == movie_title].iloc[0]
        combined_similarity = np.zeros(len(movies_df))
        
        for feature, weight in feature_mapping.items():
            if feature not in movies_df.columns:
                continue

            vectorizer = TfidfVectorizer(token_pattern=r'\b\w+\b')
            
            def process_feature(data):
                if isinstance(data, list):
                    return ' '.join(map(str, data))
                return str(data)

            feature_data = movies_df[feature].apply(process_feature).fillna('')
            feature_matrix = vectorizer.fit_transform(feature_data)
            ref_vector = vectorizer.transform([process_feature(ref_movie[feature])])
            similarity = cosine_similarity(ref_vector, feature_matrix)[0]
            
            combined_similarity += similarity * weight

        year_diff = abs(pd.to_datetime(movies_df['release_date']).dt.year - 
                       pd.to_datetime(ref_movie['release_date']).year)
        year_score = 1 / (1 + year_diff)
        combined_similarity += year_score * 0.1

        movie_indices = combined_similarity.argsort()[::-1][1:k+1]
        recommended_films = movies_df.iloc[movie_indices].copy()
        recommended_films['similarity_score'] = combined_similarity[movie_indices]
        
        return recommended_films.sort_values('similarity_score', ascending=False)

# Fonctions de rendu
def render_cast_section(movie):
    """Rendu de la section casting"""
    section_title_col1, section_title_col2 = st.columns([1, 4])

    with section_title_col1:
        st.markdown("##### 🎬 Réalisation")
        
    with section_title_col2:
        st.markdown("##### 🎭 Têtes d'affiche")

    cast_cols = st.columns([1, 0.1, 1, 1, 1, 1])

    # Réalisateur
    with cast_cols[0]:
        director = movie.get('director', 'Non spécifié')
        directors = director.split(', ') if isinstance(director, str) else ['Non spécifié']
        
        for director in directors[:1]:
            if director != 'Non spécifié':
                director_id = get_person_id(director)
                director_image_url = generate_tmdb_person_image_url(director_id)
            else:
                director_image_url = "https://via.placeholder.com/120x180.png?text=Non+spécifié"
                
            st.markdown(f"""
                <div style='text-align: center;'>
                    <img src='{director_image_url}' style='width: 120px; margin-bottom: 10px; border-radius: 8px;'>
                    <div><strong>{clean_name(director)}</strong></div>
                    <div style='color: gray; font-size: 0.9em;'>Réalisateur</div>
                </div>
            """, unsafe_allow_html=True)

    # Séparateur
    with cast_cols[1]:
        st.markdown("""
            <div style='width: 2px; background-color: #ddd; height: 200px; margin: 0 auto;'></div>
        """, unsafe_allow_html=True)

    # Acteurs
    actors = movie['actors'][:4] if isinstance(movie['actors'], list) else []
    for idx, (actor, role) in enumerate(actors):
        with cast_cols[idx + 2]:
            actor_id = get_person_id(actor)
            actor_image_url = generate_tmdb_person_image_url(actor_id)
            st.markdown(f"""
                <div style='text-align: center;'>
                    <img src='{actor_image_url}' style='width: 120px; margin-bottom: 10px; border-radius: 8px;'>
                    <div><strong>{actor}</strong></div>
                    <div style='color: gray; font-size: 0.9em;'>{role}</div>
                </div>
            """, unsafe_allow_html=True)

def render_movie_with_rank(movie, title_lang, rank: int):
    """Affiche le film principal en grand format avec un badge de classement optionnel"""
    st.markdown("---")
    
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

        st.markdown("---")
        
        render_cast_section(movie)
        
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
                "main_view"
            )

        # Bande-annonce
        trailer_url = get_trailer_url(movie['tmdb_id'], TMDB_API_KEY)
        st.markdown("---")
        st.markdown("#### 🎥 Bande-annonce")
        if trailer_url:
            st.video(trailer_url)
        else:
            st.markdown("Aucune bande-annonce disponible.")

def render_main_movie(movie, title_lang):
    """Affiche le film principal en grand format"""
    # Layout principal : poster et infos
    st.markdown("---")
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

        st.markdown("---")
        
        render_cast_section(movie)
        
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
                "main_view"
            )

        # Bande-annonce (sous les boutons)
        trailer_url = get_trailer_url(movie['tmdb_id'], TMDB_API_KEY)
        st.markdown("---")
        st.markdown("#### 🎥 Bande-annonce")
        if trailer_url:
            st.video(trailer_url)
        else:
            st.markdown("Aucune bande-annonce disponible.")

# Trieur générique pour les films
def sort_movies(movies_df, sort_by, ascending=False):
    """Trie les films selon différents critères"""
    sort_options = {
        "Note Global": "average_rating",
        "Nouveautés": "release_year",
        "Box Office": "box_office_millions",
    }
    
    if sort_by in sort_options:
        return movies_df.sort_values(by=sort_options[sort_by], ascending=ascending)
    return movies_df