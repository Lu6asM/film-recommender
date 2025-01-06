import streamlit as st

# Configuration de base
CSV_URL = 'https://raw.githubusercontent.com/Lu6asM/film-recommender/refs/heads/main/data/processed/df_movie_cleaned.csv'
THEME_COLOR = '#FF5733'
SECONDARY_COLOR = '#E64A19'
BACKGROUND_COLOR = '#FFFFFF'
TEXT_COLOR = '#333333'

# Configuration TMDB
TMDB_API_KEY = "f26ef44bcadc5d6ffa22263ea37741ce"
TMDB_BASE_URL = "https://image.tmdb.org/t/p/"
VALID_POSTER_SIZES = ['w92', 'w154', 'w185', 'w342', 'w500', 'w780', 'original']

# Configuration Streamlit
st.set_page_config(
    page_title="Recommandateur de Films",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# CSS amélioré pour Streamlit
COMMON_CSS = """
<style>
    /* Variables CSS */
    :root {
        --primary-color: #FF5733;
        --primary-light: rgba(255, 87, 51, 0.05);
        --primary-medium: rgba(255, 87, 51, 0.1);
        --secondary-color: #E64A19;
        --transition-speed: 0.3s;
    }

    /* Headers */
    [data-theme="dark"] h1, 
    [data-theme="dark"] h2, 
    [data-theme="dark"] h3 {
        color: #FFFFFF !important;
    }

    [data-theme="light"] h1,
    [data-theme="light"] h2,
    [data-theme="light"] h3 {
        color: #2C3E50 !important;
    }
    
    .main-title {
        color: var(--primary-color) !important;
    }
    
    /* Cards et éléments de fond */
    .movie-card, div[data-testid="metric-container"], .filter-container {
        background-color: rgba(44, 62, 80, 0.05);
        border: 1px solid rgba(44, 62, 80, 0.1);
    }
    
    /* Boutons */
    div.stButton > button {
        background-color: #2C3E50 !important;
    }

    div.stButton > button:hover {
        background-color: #34495E !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(44, 62, 80, 0.03);
    }

    /* Accents */
    .filter-title, div.stAlert {
        color: #2C3E50;
    }
    
    /* Orange subtil uniquement pour les interactions */
    div[data-testid="stImage"] img:hover,
    .movie-card:hover,
    footer a:hover svg {
        border-color: var(--primary-color);
    }
    
    .main-title {
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    
    .filter-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Cards */
    .movie-card {
        background-color: rgba(255, 87, 51, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 87, 51, 0.2);
        transition: transform var(--transition-speed);
        backdrop-filter: blur(10px);
    }
    
    .movie-card:hover {
        transform: translateY(-5px);
    }

    /* Métriques */
    div[data-testid="metric-container"] {
        background-color: rgba(255, 87, 51, 0.1);
        border-radius: 10px;
        padding: 1rem;
        transition: transform var(--transition-speed);
    }

    div[data-testid="metric-container"]:hover {
        transform: scale(1.02);
    }

    /* Boutons */
    div.stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: all var(--transition-speed) !important;
    }

    div.stButton > button:hover {
        background-color: var(--secondary-color) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button[kind="primary"] {
        background-color: var(--primary-color) !important;
        border: none !important;
    }

    .stButton > button[kind="secondary"] {
        background-color: var(--primary-color) !important;
        border: 1px solid var(--primary-color) !important;
    }

    button[data-baseweb="button"] {
        background-color: var(--primary-color) !important;
    }

    /* Images */
    div[data-testid="stImage"] img {
        border-radius: 12px;
        transition: all var(--transition-speed);
    }

    div[data-testid="stImage"] img:hover {
        transform: scale(1.03);
    }

    /* Select boxes et inputs */
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 87, 51, 0.1);
        border-radius: 8px;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 87, 51, 0.1);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 87, 51, 0.05);
    }

    /* Filter Container */
    .filter-container {
        background: rgba(255, 87, 51, 0.05);
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
    }
    
    .filter-section {
        padding: 1rem;
        border-radius: 8px;
    }

    /* No Results */
    .no-results {
        text-align: center;
        padding: 2rem;
        font-size: 1.2rem;
        color: rgba(255, 87, 51, 0.8);
        background: rgba(255, 87, 51, 0.1);
        border-radius: 8px;
        margin: 2rem 0;
    }

    /* Footer */
    footer {
        margin-top: 2rem;
        padding: 1rem 0;
        border-top: 1px solid rgba(255, 87, 51, 0.2);
    }
    
    footer svg path {
        fill: var(--primary-color);
    }
    
    footer a:hover svg {
        transform: scale(1.1);
        transition: transform var(--transition-speed);
    }

</style>
"""

# Fonction pour appliquer les styles
def load_css():
    st.markdown(COMMON_CSS, unsafe_allow_html=True)