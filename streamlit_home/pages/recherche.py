from auth import auth_component, sidebar_favorites, favorite_button
import streamlit as st
import pandas as pd
import traceback
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Explorer - Film Recommender",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def generate_tmdb_image_url(file_path, size='w500'):
    if not file_path or pd.isna(file_path):
        return "https://via.placeholder.com/500x750.png?text=No+Image"
    file_path = file_path.lstrip('/')
    base_url = "https://image.tmdb.org/t/p/"
    valid_sizes = ['w92', 'w154', 'w185', 'w342', 'w500', 'w780', 'original']
    size = size if size in valid_sizes else 'w500'
    return f"{base_url}{size}/{file_path}"

@st.cache_data
def charger_donnees_films(chemin_fichier):
    df = pd.read_csv(chemin_fichier, sep=',')
    df['genres'] = df['Genres'].str.split(', ')
    df['acteurs'] = df['Acteurs'].str.split(', ')
    df['pays'] = df['Pays de Production'].str.split(', ')
    df['langues'] = df['Langues Parlées'].fillna('English').str.split(', ')
    df['companies'] = df['Compagnies de Production'].str.split(', ')
    df['release_year'] = pd.to_datetime(df['Date de Sortie']).dt.year
    df['box_office_millions'] = pd.to_numeric(df['Box Office'], errors='coerce') / 1000000
    df['budget_millions'] = pd.to_numeric(df['Budget'], errors='coerce') / 1000000
    return df

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

def recherche_films(df, genres=None, note_min=0, decennie=None, langue=None, duree_max=None):
    filtered_df = df.copy()
    
    if genres:
        filtered_df = filtered_df[filtered_df['genres'].apply(lambda x: any(genre in x for genre in genres))]
    
    if note_min > 0:
        filtered_df = filtered_df[
            ((filtered_df['Note tmdb'].astype(float) + filtered_df['Note imdb'].astype(float)) / 2) >= note_min
        ]
    
    if decennie:
        filtered_df = filtered_df[filtered_df['Décennie'] == decennie]
        
    if langue:
        filtered_df = filtered_df[filtered_df['langues'].apply(lambda x: langue in x)]
        
    if duree_max:
        filtered_df = filtered_df[filtered_df['Durée'] <= duree_max]
    
    return filtered_df

def afficher_film(movie):
    with st.container():
        st.markdown("---")
        
        # Création des colonnes principales
        poster_col, info_col = st.columns([1, 3])
        
        with poster_col:
            # Affiche du film
            poster_url = generate_tmdb_image_url(movie['Affiche'])
            st.image(poster_url, use_container_width =True)
            # Ajout du bouton favoris
            favorite_button(movie['ID tmdb'], movie['Titre Original'], "search")
        
        with info_col:
            # En-tête avec titre et année
            st.markdown(f"### {movie['Titre Original']} ({movie['release_year']})")
            if movie['Titre Original'] != movie['Titre Français']:
                st.markdown(f"*Titre français : {movie['Titre Français']}*")
            
            # Informations principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Durée :** {format_duration(movie['Durée'])}")
                st.markdown(f"**Genre(s) :** {', '.join(movie['genres'])}")
            
            with col2:
                st.markdown(f"**Budget :** {format_currency(movie['budget_millions'])}")
                st.markdown(f"**Box Office :** {format_currency(movie['box_office_millions'])}")
            
            with col3:
                st.markdown(f"**Réalisateur :** {movie['Réalisateur(s)']}")
                st.markdown(f"**Pays :** {', '.join(movie['pays'])}")
            
            # Notes et votes
            st.markdown("#### Évaluations")
            metric_col1, metric_col2, metric_col3 = st.columns([1, 1, 2])
            with metric_col1:
                st.metric("Note IMDB", f"{movie['Note imdb']:.1f}/10", f"{movie['Votes imdb']:,} votes")
            with metric_col2:
                st.metric("Note TMDB", f"{movie['Note tmdb']:.1f}/10", f"{movie['Votes tmdb']:,} votes")
            
            # Synopsis
            st.markdown("**Synopsis :**")
            st.markdown(f"{movie['Synopsis']}")
            
            # Liste des acteurs
            with st.expander("Voir les acteurs"):
                st.write(', '.join(movie['acteurs']))
            
            # Liens externes
            col1, col2, col_empty = st.columns([1, 1, 4])
            with col1:
                st.link_button("🎬 IMDb", f"https://www.imdb.com/title/{movie['ID imdb']}", use_container_width=True)
            with col2:
                st.link_button("🎥 TMDb", f"https://www.themoviedb.org/movie/{movie['ID tmdb']}", use_container_width=True)

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
        
        # Titre de l'application
        st.title("🔍 Explorer")
        
        # Chargement des données
        movies_df = charger_donnees_films('../data/processed/df_movie_cleaned.csv')
        
        # Authentification
        user_id = auth_component()

        if user_id:
            sidebar_favorites(movies_df)

            # Sauvegarder l'état de la recherche dans la session
            if 'search_term' not in st.session_state:
                st.session_state.search_term = ''
            if 'selected_genres' not in st.session_state:
                st.session_state.selected_genres = []

        

            # Interface de recherche
            with st.sidebar:
                search_term = st.text_input('Rechercher un film', value=st.session_state.search_term)
                st.session_state.search_term = search_term

                selected_genres = st.multiselect('Filtrer par genre', 
                                               options=sorted(set([genre for genres in movies_df['genres'] for genre in genres])),
                                               default=st.session_state.selected_genres)
                st.session_state.selected_genres = selected_genres

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
                options=[""] + sorted(movies_df['Décennie'].unique().tolist()),
                help="Filtrer par décennie"
            )
            
            # Sélection de la langue
            langue = st.selectbox(
                "Langue",
                options=[""] + sorted(set([lang for langs in movies_df['langues'] for lang in langs])),
                help="Filtrer par langue"
            )
            
            # Durée maximale
            duree_max = st.slider(
                "Durée maximale (minutes)",
                min_value=0,
                max_value=int(movies_df['Durée'].max()),
                value=int(movies_df['Durée'].max()),
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
                langue=langue if langue != "" else None,
                duree_max=duree_max
            )
            
            # Affichage des résultats
            if not filtered_df.empty:
                st.success(f"📽️ {len(filtered_df)} films trouvés")
                
                # Options de tri
                sort_options = {
                    "Note IMDB (décroissant)": ("Note imdb", False),
                    "Note TMDB (décroissant)": ("Note tmdb", False),
                    "Date de sortie (plus récent)": ("Date de Sortie", False),
                    "Date de sortie (plus ancien)": ("Date de Sortie", True),
                    "Durée (croissant)": ("Durée", True),
                    "Durée (décroissant)": ("Durée", False),
                }
                
                sort_by = st.selectbox("Trier par:", options=list(sort_options.keys()))
                sort_column, ascending = sort_options[sort_by]
                filtered_df = filtered_df.sort_values(by=sort_column, ascending=ascending)
                
                # Affichage des films
                for _, movie in filtered_df.iterrows():
                    afficher_film(movie)
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