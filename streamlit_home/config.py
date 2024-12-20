# config.py
CSV_URL = 'https://raw.githubusercontent.com/Lu6asM/film-recommender/refs/heads/main/data/processed/df_movie_cleaned.csv'
THEME_COLOR = '#FF5733'
TMDB_API_KEY = "f26ef44bcadc5d6ffa22263ea37741ce"
TMDB_BASE_URL = "https://image.tmdb.org/t/p/"
VALID_POSTER_SIZES = ['w92', 'w154', 'w185', 'w342', 'w500', 'w780', 'original']

# Mapping des colonnes
COLUMN_MAPPING = {
    'Titre Original': 'title',
    'Titre Français': 'title_fr',
    'Synopsis': 'overview',
    'Date de Sortie': 'release_date',
    'Réalisateur(s)': 'director',
    'Affiche': 'poster_path',
    'Genres': 'genres',
    'Acteurs': 'actors',
    'Pays de Production': 'countries',
    'Langues Parlées': 'languages',
    'Mots-Clés': 'keywords',
    'Compagnies de Production': 'companies',
    'Box Office': 'box_office',
    'Budget': 'budget',
    'Durée': 'runtime',
    'Note imdb': 'imdb_rating',
    'Note tmdb': 'tmdb_rating',
    'Votes imdb': 'imdb_votes',
    'Votes tmdb': 'tmdb_votes',
    'ID imdb': 'imdb_id',
    'ID tmdb': 'tmdb_id',
    'Réputation': 'popularity',
    'Décennie': 'decade'
}

# CSS commun
COMMON_CSS = """
<style>
    /* Reset link styles */
    a {
        text-decoration: none !important;
        border-bottom: none !important;
    }
    
    /* Cards */
    .movie-card {
        background-color: rgba(255, 87, 51, 0.1);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255, 87, 51, 0.2);
    }
    
    /* Metrics */
    .stMetric .css-1wivap2 {
        background-color: rgba(255, 87, 51, 0.1);
        border-radius: 8px;
        padding: 10px;
    }
    
    .stMetric .css-1wivap2 p {
        color: #FF5733;
    }
</style>
"""