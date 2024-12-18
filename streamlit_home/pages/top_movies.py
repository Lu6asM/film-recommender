from auth import auth_component, sidebar_favorites, favorite_button
import streamlit as st
import pandas as pd
import traceback

# Configuration de la page
st.set_page_config(
    page_title="Trending - Film Recommender",
    page_icon="🏆",
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

@st.cache_data
def charger_donnees_films(chemin_fichier):
    df = pd.read_csv(chemin_fichier, sep=',')
    df['genres'] = df['Genres'].str.split(', ')
    df['acteurs'] = df['Acteurs'].str.split(', ')
    df['pays'] = df['Pays de Production'].str.split(', ')
    df['langues'] = df['Langues Parlées'].str.split(', ')
    df['companies'] = df['Compagnies de Production'].str.split(', ')
    df['release_year'] = pd.to_datetime(df['Date de Sortie']).dt.year
    df['box_office_millions'] = pd.to_numeric(df['Box Office'], errors='coerce') / 1000000
    df['budget_millions'] = pd.to_numeric(df['Budget'], errors='coerce') / 1000000
    df['average_rating'] = (df['Note tmdb'].astype(float) + df['Note imdb'].astype(float)) / 2
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

def afficher_film_top(movie, rank):
    with st.container():
        st.markdown("---")
        cols = st.columns([1, 3])
        
        # Colonne de gauche : Poster et rang
        with cols[0]:
            # Affichage du rang
            st.markdown(f"""
            <div style='position: relative; text-align: center;'>
                <h1 style='font-size: 3em; color: #1E88E5; margin: 0;'>#{rank}</h1>
            </div>
            """, unsafe_allow_html=True)

            # Affiche du film
            poster_url = generate_tmdb_image_url(movie['Affiche'])
            st.image(poster_url, use_container_width =True)
        
            # Ajout du bouton favoris
            favorite_button(movie['ID tmdb'], movie['Titre Original'], f"top_{rank}")

        # Colonne de droite : Informations
        with cols[1]:
            # Titre et année
            st.markdown(f"### {movie['Titre Original']} ({movie['release_year']})")
            if movie['Titre Original'] != movie['Titre Français']:
                st.markdown(f"*Titre français : {movie['Titre Français']}*")
            
            # Informations principales en colonnes
            info_cols = st.columns(3)
            with info_cols[0]:
                st.markdown(f"**Durée :** {format_duration(movie['Durée'])}")
                st.markdown(f"**Genre(s) :** {', '.join(movie['genres'])}")
                st.markdown(f"**Langue(s) :** {', '.join(movie['langues'])}")
            
            with info_cols[1]:
                st.markdown(f"**Budget :** {format_currency(movie['budget_millions'])}")
                st.markdown(f"**Box Office :** {format_currency(movie['box_office_millions'])}")
                st.markdown(f"**Popularité :** {movie['Réputation']}")
            
            with info_cols[2]:
                st.markdown(f"**Réalisateur :** {movie['Réalisateur(s)']}")
                st.markdown(f"**Pays :** {', '.join(movie['pays'])}")
                st.markdown(f"**Décennie :** {movie['Décennie']}")
            
            # Notes et votes
            st.markdown("#### Évaluations")
            rating_cols = st.columns([1, 1, 2])
            with rating_cols[0]:
                st.metric("Note IMDB", f"{movie['Note imdb']:.1f}/10", f"{movie['Votes imdb']:,} votes")
            with rating_cols[1]:
                st.metric("Note TMDB", f"{movie['Note tmdb']:.1f}/10", f"{movie['Votes tmdb']:,} votes")
            
            # Synopsis
            st.markdown("**Synopsis :**")
            st.markdown(f"{movie['Synopsis']}")
            
            # Liste des acteurs dans un expander
            with st.expander("Voir les acteurs"):
                st.write(', '.join(movie['acteurs']))
            
            # Liens externes
            link_cols = st.columns([1, 1, 4])
            with link_cols[0]:
                st.link_button("🎬 IMDb", f"https://www.imdb.com/title/{movie['ID imdb']}", use_container_width=True)
            with link_cols[1]:
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
        
        # Titre de la page
        st.title("🏆 Top Films")
        
        # Charger les données
        movies_df = charger_donnees_films('https://raw.githubusercontent.com/Lu6asM/film-recommender/refs/heads/main/data/processed/df_movie_cleaned.csv')

        # Authentification
        user_id = auth_component()
    
        if user_id:
            sidebar_favorites(movies_df)

        # Séparateur visuel
        st.sidebar.divider()


        st.sidebar.markdown("### 🔄 Options d'affichage")
        with st.sidebar:
            
            tri_options = {
                "Popularité": "Popularité",
                "Note IMDB": "Note imdb",
                "Note TMDB": "Note tmdb",
                "Note moyenne": "average_rating",
                "Box Office": "box_office_millions",
                "Plus récents": "release_year"
            }
            
            tri_choix = st.selectbox(
                "Trier par :",
                options=list(tri_options.keys())
            )
            
            nombre_films = st.slider(
                "Nombre de films à afficher",
                min_value=5,
                max_value=50,
                value=10,
                step=5
            )
        
        # Trier les films selon le critère choisi
        sort_column = tri_options[tri_choix]
        sorted_df = movies_df.sort_values(by=sort_column, ascending=False)
        
        # Afficher les films
        st.info(f"📽️ Top {nombre_films} des films triés par {tri_choix}")
        
        for rank, (_, movie) in enumerate(sorted_df.head(nombre_films).iterrows(), 1):
            afficher_film_top(movie, rank)
    
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