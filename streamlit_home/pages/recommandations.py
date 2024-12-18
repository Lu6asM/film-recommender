from auth import auth_component, sidebar_favorites, favorite_button
import streamlit as st
import pandas as pd
import numpy as np
import traceback
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import ast

# Configuration de la page
st.set_page_config(
    page_title="Pour Vous - Film Recommender",
    page_icon="✨",
    layout="wide",
)

def generate_tmdb_image_url(file_path, size='w500'):
    if not file_path or pd.isna(file_path):
        return "https://via.placeholder.com/500x750.png?text=No+Image"
    file_path = file_path.lstrip('/')
    base_url = "https://image.tmdb.org/t/p/"
    valid_sizes = ['w92', 'w154', 'w185', 'w342', 'w500', 'w780', 'original']
    size = size if size in valid_sizes else 'w500'
    return f"{base_url}{size}/{file_path}"

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

def safe_eval(value):
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []

@st.cache_data
def charger_donnees_films(chemin_fichier):
    try:
        df = pd.read_csv(chemin_fichier, sep=',')
        
        # Traitement des colonnes
        df['genres'] = df['Genres'].str.split(', ')
        df['acteurs'] = df['Acteurs'].str.split(', ')
        df['pays'] = df['Pays de Production'].str.split(', ')
        df['langues'] = df['Langues Parlées'].str.split(', ')
        df['keywords'] = df['Mots-Clés'].fillna('').str.split(', ')
        df['companies'] = df['Compagnies de Production'].str.split(', ')
        
        # Colonnes calculées
        df['release_year'] = pd.to_datetime(df['Date de Sortie']).dt.year
        df['box_office_millions'] = pd.to_numeric(df['Box Office'], errors='coerce') / 1000000
        df['budget_millions'] = pd.to_numeric(df['Budget'], errors='coerce') / 1000000
        df['average_rating'] = (df['Note tmdb'].astype(float) + df['Note imdb'].astype(float)) / 2
        
        # Colonnes renommées pour compatibilité
        df['title'] = df['Titre Original']
        df['title_fr'] = df['Titre Français']
        df['overview'] = df['Synopsis']
        df['release_date'] = df['Date de Sortie']
        df['director'] = df['Réalisateur(s)']
        df['poster_path'] = df['Affiche']
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {str(e)}")
        return pd.DataFrame()

@st.cache_data
def recommander_films_v3(movie_title, movies_df, k=5, lang='en'):
    """
    Advanced movie recommendation system using flexible feature mapping and weighted similarities.
    """
    # Mapping of feature names with flexibility
    feature_mapping = {
        'genres': ['genres', 'Genres'],
        'keywords': ['keywords', 'Mots-Clés'],
        'directors': ['director', 'Réalisateur(s)'],
        'actors': ['cast', 'Acteurs'],
        'description': ['overview', 'Synopsis']
    }

    # Find the first matching column for each feature
    def find_column(feature_options):
        for col in feature_options:
            if col in movies_df.columns:
                return col
        return None

    # Mapped columns with error handling
    mapped_columns = {
        key: find_column(cols)
        for key, cols in feature_mapping.items()
    }

    # Default feature weights
    default_weights = {
        'genres': 0.4,
        'keywords': 0.2,
        'directors': 0.15,
        'actors': 0.15,
        'description': 0.1
    }

    # Validate movie exists
    if movie_title not in movies_df['Titre Original'].values:
        raise ValueError(f"Le film '{movie_title}' n'a pas été trouvé dans la base de données.")

    # Reference movie details
    ref_movie = movies_df[movies_df['Titre Original'] == movie_title].iloc[0]

    # Prepare feature matrices
    vectorizers = {
        feature: TfidfVectorizer(token_pattern=r'\b\w+\b')
        for feature in mapped_columns.keys() if mapped_columns[feature]
    }

    # Compute similarity for each feature
    feature_similarities = {}
    for feature, vectorizer in vectorizers.items():
        if not mapped_columns[feature]:
            continue

        def process_feature_data(data):
            if isinstance(data, list):
                return ' '.join(map(str, data))
            elif isinstance(data, str):
                return data
            return ''

        feature_data = movies_df[mapped_columns[feature]].apply(process_feature_data).fillna('')
        feature_matrix = vectorizer.fit_transform(feature_data)
        ref_feature_vector = vectorizer.transform([process_feature_data(ref_movie[mapped_columns[feature]])])
        similarity = cosine_similarity(ref_feature_vector, feature_matrix)[0]
        feature_similarities[feature] = similarity

    # Combine similarities with weighted average
    combined_similarity = np.zeros(len(movies_df))
    for feature, similarity in feature_similarities.items():
        combined_similarity += similarity * default_weights.get(feature, 0)

    # Additional filtering considerations
    def compute_additional_scores(ref_movie, movies_df):
        scores = np.zeros(len(movies_df))
        year_diff = np.abs(pd.to_datetime(movies_df['Date de Sortie']).dt.year - 
                          pd.to_datetime(ref_movie['Date de Sortie']).year)
        year_score = 1 / (1 + year_diff)
        return year_score * 0.1

    # Add additional scoring
    additional_scores = compute_additional_scores(ref_movie, movies_df)
    combined_similarity += additional_scores

    # Get indices of top k similar movies
    movie_indices = combined_similarity.argsort()[::-1][1:k+1]
    
    # Get complete records for recommended movies
    recommended_films = movies_df.iloc[movie_indices].copy()
    recommended_films['similarity_distance'] = combined_similarity[movie_indices]
    
    # Trier par similarité
    recommended_films = recommended_films.sort_values('similarity_distance', ascending=False)
    
    return recommended_films


def afficher_film_recommande(film, langue_titre):
    with st.container():
        st.markdown("---")
        cols = st.columns([1, 3])
        
        # Colonne gauche : Poster
        with cols[0]:
            poster_url = generate_tmdb_image_url(film['Affiche'])
            st.image(poster_url, use_container_width=True)

            # Bouton favoris
            favorite_button(film['ID tmdb'], film['Titre Original'], "recommend")

        # Colonne droite : Informations
        with cols[1]:
            # Titre et année
            titre_display = film['Titre Français'] if langue_titre == "Titre Français" else film['Titre Original']
            annee = pd.to_datetime(film['Date de Sortie']).year
            st.markdown(f"### {titre_display} ({annee})")
            
            if film['Titre Original'] != film['Titre Français']:
                other_title = film['Titre Original'] if langue_titre == "Titre Français" else film['Titre Français']
                st.markdown(f"*Titre {'original' if langue_titre == 'Titre Français' else 'français'} : {other_title}*")
            
            # Score de similarité
            st.metric("Score de similarité", f"{film['similarity_distance']:.2f}")
            
            # Informations principales
            info_cols = st.columns(3)
            
            with info_cols[0]:
                st.markdown(f"**Durée :** {format_duration(film['Durée'])}")
                st.markdown(f"**Genre(s) :** {', '.join(film['genres']) if isinstance(film['genres'], list) else film['Genres']}")
                st.markdown(f"**Langue(s) :** {', '.join(film['langues']) if isinstance(film['langues'], list) else film['Langues Parlées']}")
            
            with info_cols[1]:
                st.markdown(f"**Budget :** {format_currency(film['budget_millions'])}")
                st.markdown(f"**Box Office :** {format_currency(film['box_office_millions'])}")
                st.markdown(f"**Popularité :** {film['Réputation']}")
            
            with info_cols[2]:
                st.markdown(f"**Réalisateur :** {film['Réalisateur(s)']}")
                st.markdown(f"**Pays :** {', '.join(film['pays']) if isinstance(film['pays'], list) else film['Pays de Production']}")
                st.markdown(f"**Décennie :** {film['Décennie']}")
            
            # Notes
            st.markdown("#### Évaluations")
            rating_cols = st.columns([1, 1, 2])
            with rating_cols[0]:
                st.metric("Note IMDB", f"{film['Note imdb']:.1f}/10", f"{film['Votes imdb']:,} votes")
            with rating_cols[1]:
                st.metric("Note TMDB", f"{film['Note tmdb']:.1f}/10", f"{film['Votes tmdb']:,} votes")
            
            # Synopsis
            st.markdown("**Synopsis :**")
            st.markdown(f"{film['Synopsis']}")
            
            # Liste des acteurs
            with st.expander("Voir les acteurs"):
                st.write(', '.join(film['acteurs']) if isinstance(film['acteurs'], list) else film['Acteurs'])
            
            # Liens externes
            link_cols = st.columns([1, 1, 4])
            with link_cols[0]:
                st.link_button("🎬 IMDb", f"https://www.imdb.com/title/{film['ID imdb']}", use_container_width=True)
            with link_cols[1]:
                st.link_button("🎥 TMDb", f"https://www.themoviedb.org/movie/{film['ID tmdb']}", use_container_width=True)

def main():
    try:
        # Style CSS personnalisé
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
        
        # Charger les données
        movies_df = charger_donnees_films('../data/processed/df_movie_cleaned.csv')

        # Authentification
        user_id = auth_component()
    
        if user_id:
            sidebar_favorites(movies_df)
        
            # Sauvegarder l'état de la recherche dans la session
            if 'selected_movie' not in st.session_state:
                st.session_state.selected_movie = None

        # Séparateur visuel
        st.sidebar.divider()

        # Titre de la page
        st.title("✨ Pour Vous")
        
        # Sidebar pour les préférences
        st.sidebar.markdown("### ⚙️ Préférences")
        with st.sidebar:
            
            langue_titre = st.radio(
                "Afficher les titres en",
                ["Titre Original", "Titre Français"]
            )
            
            nb_recommandations = st.slider(
                "Nombre de recommandations",
                min_value=1,
                max_value=10,
                value=5
            )

        
        # Sélection du film de référence
        st.header("🎬 Choisissez votre film de référence")
        
        titles_list = movies_df['title_fr' if langue_titre == "Titre Français" else 'title'].tolist()
        film_reference = st.selectbox(
            "Basé sur ce film, nous vous recommanderons des films similaires",
            options=titles_list
        )
        
        if film_reference:
            if langue_titre == "Titre Français":
                film_reference = movies_df[movies_df['title_fr'] == film_reference]['title'].values[0]
        
            # Bouton de recommandation
            if st.button("🔍 Obtenir des recommandations", type="primary", use_container_width=True):
                with st.spinner("Recherche des films similaires en cours..."):
                    recommended_films = recommander_films_v3(
                        film_reference,
                        movies_df,
                        k=nb_recommandations,
                        lang='fr' if langue_titre == "Titre Français" else 'en'
                    )
                
                st.success(f"📽️ Voici {nb_recommandations} films similaires à {film_reference}")
                
                # Afficher chaque film recommandé
                for _, film in recommended_films.iterrows():
                    afficher_film_recommande(film, langue_titre)
    
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