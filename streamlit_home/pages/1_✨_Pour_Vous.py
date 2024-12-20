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

def get_trailer_url(tmdb_id, api_key):
    """Récupère l'URL de la bande-annonce d'un film à partir de son ID TMDb."""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={api_key}&language=fr"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Cherche la bande-annonce
        for video in data.get('results', []):
            if video['type'] == 'Trailer':
                return f"https://www.youtube.com/embed/{video['key']}"
    return None  # Retourne None si aucune bande-annonce n'est trouvée

def get_movie_card(movie, i, j, title_lang="Titre Original"):
    """
    Génère une carte de film cliquable avec animation au survol
    """
    display_title = movie['title_fr'] if title_lang == "Titre Français" else movie['title']
    poster_url = generate_tmdb_image_url(movie['poster_path'])
    
    content = f"""
        <div style="text-align: center;">
            <a href="#" id="movie_{movie['tmdb_id']}_{i}_{j}">
                <img src="{poster_url}"
                    style="width: 100%; object-fit: cover; border-radius: 8px; margin-bottom: 15px; 
                           cursor: pointer; transition: filter .2s ease-in-out, transform .2s ease-in-out;"
                    onmouseover="this.style.filter='brightness(70%)'; this.style.transform='scale(1.05)'"
                    onmouseout="this.style.filter='brightness(100%)'; this.style.transform='scale(1)'">
            </a>
            <div style='margin-bottom: 5px;'><strong>{display_title}</strong> ({movie['release_year']})</div>
            <div style='color: gray; font-size: 0.8em; margin-bottom: 5px;'>{movie['director']}</div>
            <div style='color: #FF5733; font-size: 0.8em; margin-bottom: 10px;'>Score: {movie['similarity_score']:.2f}</div>
        </div>
    """
    
    # Créer un détecteur de clic unique pour ce film
    unique_key = f"movie_card_{movie['tmdb_id']}_{i}_{j}"
    clicked = click_detector(content, key=unique_key)
    
    return clicked

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
    """
    Système de recommandation de films basé sur plusieurs critères.
    """
    with st.spinner("Calcul des recommandations en cours..."):
        # Configuration des features à utiliser
        feature_mapping = {
            'genres': 0.4,
            'keywords': 0.2, 
            'director': 0.15,
            'actors': 0.15,
            'overview': 0.1
        }

        # Vérification du film
        if movie_title not in movies_df['title'].values:
            raise ValueError(f"Le film '{movie_title}' n'est pas dans la base de données.")

        ref_movie = movies_df[movies_df['title'] == movie_title].iloc[0]

        # Calcul des similarités pour chaque feature
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

        # Ajout du score basé sur l'année
        year_diff = abs(pd.to_datetime(movies_df['release_date']).dt.year - 
                        pd.to_datetime(ref_movie['release_date']).year)
        year_score = 1 / (1 + year_diff)
        combined_similarity += year_score * 0.1

        # Sélection des films les plus similaires
        movie_indices = combined_similarity.argsort()[::-1][1:k+1]
        recommended_films = movies_df.iloc[movie_indices].copy()
        recommended_films['similarity_score'] = combined_similarity[movie_indices]
        
        return recommended_films.sort_values('similarity_score', ascending=False)

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

        # Bande-annonce (sous les boutons)
        trailer_url = get_trailer_url(movie['tmdb_id'], TMDB_API_KEY)  # Remplacez 'YOUR_API_KEY' par votre clé d'API
        st.markdown("---")
        st.markdown("#### 🎥 Bande-annonce")
        if trailer_url:
            st.video(trailer_url)
        else:
            st.markdown("Aucune bande-annonce disponible.")
        
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
        
        if 'selected_movie' not in st.session_state:
            st.session_state.selected_movie = None
            
        # Sélection du film
        titles = movies_df['title_fr' if title_lang == "Titre Français" else 'title'].tolist()
        reference_movie = st.selectbox(
            "Choisir un film",
            options=titles,
            key="movie_selector"
        )
        
        current_movie = None

        if st.session_state.selected_movie:
            # Si un film a été sélectionné via la sidebar (structure dictionnaire)
            if isinstance(st.session_state.selected_movie, dict):
                current_movie = st.session_state.selected_movie['title']
            # Si un film a été sélectionné via "Watch Now" (chaîne simple)
            else:
                current_movie = st.session_state.selected_movie
            # Réinitialiser pour permettre une nouvelle sélection via selectbox
            st.session_state.selected_movie = None
        elif reference_movie:
            # Si un film a été sélectionné via le selectbox
            current_movie = reference_movie

        if current_movie:
            if title_lang == "Titre Français":
                filtered_df = movies_df[movies_df['title_fr'] == current_movie]
                if not filtered_df.empty:
                    current_movie = filtered_df['title'].iloc[0]
                else:
                    st.error(f"Film non trouvé : {current_movie}")
                    current_movie = None
            
            if current_movie:
                # Vérifier si le film existe avant d'essayer de l'afficher
                filtered_movies = movies_df[movies_df['title'] == current_movie]
                if not filtered_movies.empty:
                    main_movie = filtered_movies.iloc[0]
                    render_main_movie(main_movie, title_lang)
                    
                    # Calculer et afficher les recommandations...
                    st.markdown("""
                        <div style='padding: 20px 0;'>
                            <h2>Films similaires recommandés</h2>
                            <div style='margin: 30px 0;'></div>
                        </div>
                    """, unsafe_allow_html=True)
                    recommended_movies = recommend_movies(current_movie, movies_df, num_recommendations)
                    
                    # Affichage des recommandations...
                else:
                    st.error(f"Film non trouvé : {current_movie}")
            
        # Dans la boucle d'affichage des recommandations
        for i in range(0, len(recommended_movies), 5):
            cols = st.columns(5)
            for j, (_, movie) in enumerate(recommended_movies[i:i+5].iterrows()):
                with cols[j]:
                    display_title = movie['title_fr'] if title_lang == "Titre Français" else movie['title']
                    poster_url = generate_tmdb_image_url(movie['poster_path'])

                    # Afficher l'image et les infos en dessous du bouton
                    # Afficher l'image et les infos en dessous du bouton
                    st.markdown(f"""
                        <div style='margin-top: 0px; padding: 10px; text-align: center;'>
                            <div style='position: relative; width: 100%; padding-top: 150%; margin-bottom: 10px;'>
                                <a href="?selected_movie={movie['title']}">
                                    <img src='{poster_url}' 
                                        style='position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; border-radius: 8px;'>
                                </a>
                            </div>
                            <div style='margin-bottom: 5px;'><strong>{movie['title']}</strong> ({movie['release_year']})</div>
                            <div style='color: gray; font-size: 0.8em; margin-bottom: 5px;'>{movie['director']}</div>
                        </div>
                    """, unsafe_allow_html=True)

                    if st.button(
                        f"Voir les détails",
                        key=f"movie_{movie['tmdb_id']}_{i}_{j}",
                        use_container_width=True,
                        type="secondary",
                        help=f"Voir les détails de {display_title}"
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