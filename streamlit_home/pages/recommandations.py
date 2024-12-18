import streamlit as st
import pandas as pd
import numpy as np
import traceback
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import ast

# Configuration de la page
st.set_page_config(
    page_title="Recommandation - Film Recommender",
    page_icon="🎥",
    layout="centered",
)

def generate_tmdb_image_url(file_path, size='w500'):
    """
    Génère une URL complète pour les images TMDb
    """
    if not file_path or pd.isna(file_path):
        return "https://via.placeholder.com/500x750.png?text=No+Image"
    file_path = file_path.lstrip('/')
    base_url = "https://image.tmdb.org/t/p/"
    valid_sizes = ['w92', 'w154', 'w185', 'w342', 'w500', 'w780', 'original']
    size = size if size in valid_sizes else 'w500'
    return f"{base_url}{size}/{file_path}"

# Function to safely evaluate the string as a list
def safe_eval(value):
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []

@st.cache_data
def charger_donnees_films(chemin_fichier):
    """
    Charger et préparer les données de films à partir d'un fichier texte
    """
    try:
        # Lire le fichier
        df = pd.read_csv(chemin_fichier, sep=',')

        # Préparation des colonnes
        df['genres'] = df['Genres'].str.split(', ')
        df['Mots-Clés'] = df['Mots-Clés'].fillna('')
        df['keywords'] = df['Mots-Clés'].apply(lambda x: x.split(', ') if isinstance(x, str) else [])
        df['title'] = df['Titre Original']
        df['overview'] = df['Synopsis']
        df['release_date'] = df['Date de Sortie']
        df['director'] = df['Réalisateur(s)']
        df['cast'] = df['Acteurs'].str.split(', ')
        df['poster_path'] = df['Affiche']

        # Supprimer les lignes sans mots-clés
        df = df[df['keywords'].apply(lambda x: isinstance(x, list) and len(x) > 0)]

        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {str(e)}")
        return pd.DataFrame()


@st.cache_data
def recommander_films_v3(movie_title, movies_df, k=5):
    """
    Advanced movie recommendation system using flexible feature mapping and weighted similarities.

    Args:
    - movie_title (str): Title of the reference movie
    - movies_df (DataFrame): Preprocessed movie dataset
    - k (int): Number of recommendations to return

    Returns:
    - DataFrame of recommended movies with similarity scores
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
    if movie_title not in movies_df['title'].values:
        raise ValueError(f"Le film '{movie_title}' n'a pas été trouvé dans la base de données.")

    # Reference movie details
    ref_movie = movies_df[movies_df['title'] == movie_title].iloc[0]

    # Prepare feature matrices
    vectorizers = {
        feature: TfidfVectorizer(token_pattern=r'\b\w+\b')
        for feature in mapped_columns.keys() if mapped_columns[feature]
    }

    # Compute similarity for each feature
    feature_similarities = {}
    for feature, vectorizer in vectorizers.items():
        # Skip if no column found for the feature
        if not mapped_columns[feature]:
            continue

        # Prepare feature data
        def process_feature_data(data):
            # Handle different data types (list, string)
            if isinstance(data, list):
                return ' '.join(map(str, data))
            elif isinstance(data, str):
                return data
            return ''

        feature_data = movies_df[mapped_columns[feature]].apply(process_feature_data).fillna('')

        # Vectorize
        feature_matrix = vectorizer.fit_transform(feature_data)
        ref_feature_vector = vectorizer.transform([process_feature_data(ref_movie[mapped_columns[feature]])])

        # Compute cosine similarity
        similarity = cosine_similarity(ref_feature_vector, feature_matrix)[0]
        feature_similarities[feature] = similarity

    # Combine similarities with weighted average
    combined_similarity = np.zeros(len(movies_df))
    for feature, similarity in feature_similarities.items():
        combined_similarity += similarity * default_weights.get(feature, 0)

    # Additional filtering considerations
    def compute_additional_scores(ref_movie, movies_df):
        scores = np.zeros(len(movies_df))

        # Release year proximity
        year_col = find_column(['release_year', 'release_date', 'Année'])
        if year_col:
            # Convert release date to year if needed
            if 'release_date' in movies_df.columns:
                movies_df['release_year'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year

            year_diff = np.abs(movies_df['release_year'] - pd.to_datetime(ref_movie['release_date'], errors='coerce').year)
            year_score = 1 / (1 + year_diff)
        else:
            year_score = np.ones(len(movies_df))

        return year_score * 0.1

    # Add additional scoring
    additional_scores = compute_additional_scores(ref_movie, movies_df)
    combined_similarity += additional_scores

    # Prepare recommendations
    # Exclude the original movie and sort by combined similarity
    movie_indices = combined_similarity.argsort()[::-1][1:k+1]
    recommended_films = movies_df.iloc[movie_indices].copy()
    recommended_films['similarity_distance'] = combined_similarity[movie_indices]

    # Select and format output columns
    output_columns = [
        'title', 'release_date', 'genres', 'overview',
        'similarity_distance', 'poster_path'
    ]

    return recommended_films[output_columns].sort_values('similarity_distance', ascending=True)


def page_recommandations():
    st.title("🎬 Film Recommender")

    # Charger les données
    try:
        movies_df = charger_donnees_films('https://raw.githubusercontent.com/Lu6asM/film-recommender/refs/heads/main/data/processed/df_movie_cleaned.csv')

        # Vérification des lignes sans mots-clés
        missing_keywords = movies_df[movies_df['keywords'].apply(lambda x: len(x) == 0)]
        if not missing_keywords.empty:
            st.warning(f"Il y a {len(missing_keywords)} lignes sans mots-clés.")
            st.write(missing_keywords)

        # Générer la liste de genres avant la sélection
        genres_list = sorted(set([
            genre
            for genres in movies_df['genres']
            for genre in (genres.split(', ') if isinstance(genres, str) else genres)
        ]))

        # Sidebar pour les filtres
        st.sidebar.header("Paramètres de Recommandation")

        # Filtres dans la sidebar
        with st.sidebar:
            selected_genres = st.multiselect("Filtrer par Genres", genres_list)

            # Convertir la date de sortie en année
            movies_df['release_year'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year

            year_range = st.slider(
                "Année de sortie",
                min_value=int(movies_df['release_year'].min()),
                max_value=int(movies_df['release_year'].max()),
                value=(
                    int(movies_df['release_year'].min()),
                    int(movies_df['release_year'].max())
                )
            )

        # Sélection du film de référence
        film_reference = st.selectbox(
            "Choisissez un film de référence",
            movies_df['title'].tolist()
        )

        # Nombre de recommandations
        nb_recommandations = st.slider(
            "Nombre de recommandations",
            min_value=1,
            max_value=10,
            value=5
        )

        # Bouton de recommandation
        if st.button("Obtenir des Recommandations"):
            try:
                # Filtrer les films si des genres sont sélectionnés
                filtered_movies_df = movies_df.copy()

                if selected_genres:
                    filtered_movies_df = filtered_movies_df[
                        filtered_movies_df['genres'].apply(
                            lambda x: any(
                                genre in (x.split(', ') if isinstance(x, str) else x)
                                for genre in selected_genres
                            )
                        )
                    ]

                # Filtrer par année
                filtered_movies_df = filtered_movies_df[
                    (filtered_movies_df['release_year'] >= year_range[0]) &
                    (filtered_movies_df['release_year'] <= year_range[1])
                ]

                # Obtenir les recommandations
                recommended_films = recommander_films_v3(
                    film_reference,
                    filtered_movies_df,
                    k=nb_recommandations
                )

                # Afficher les recommandations
                st.subheader(f"Films similaires à {film_reference}")

                for index, film in recommended_films.iterrows():
                    with st.expander(f"{film['title']} ({film['release_date']})"):
                        col1, col2 = st.columns([1, 3])

                        with col1:
                            # Utiliser la fonction pour générer l'URL de l'image
                            poster_url = generate_tmdb_image_url(film['poster_path'], size='w500')
                            st.image(poster_url, width=150)

                        with col2:
                            # Gestion des genres pour différents types de formats
                            genres_display = film['genres']
                            if isinstance(genres_display, list):
                                genres_display = ', '.join(genres_display)
                            elif isinstance(genres_display, str):
                                genres_display = genres_display

                            st.markdown(f"**Genres :** {genres_display}")
                            st.markdown(f"**Synopsis :** {film['overview']}")
                            st.markdown(f"**Similarité :** {film['similarity_distance']:.2f}")

            except ValueError as e:
                st.error(str(e))

    except FileNotFoundError:
        st.error("Fichier de données introuvable. Veuillez vérifier le chemin du fichier.")
    except Exception as e:
        st.error(f"Une erreur s'est produite : {str(e)}")
        st.error(traceback.format_exc())  # Ajout du traceback pour le débogage

# Point d'entrée principal
def main():
    page_recommandations()

if __name__ == "__main__":
    main()

st.markdown("---")
st.caption("Développé avec ❤️ par Lucas Meireles, Farid El Fardi, Elisabeth Tran")
st.caption("© 2024 Film Recommender | Tous droits réservés")
