import streamlit as st
import pandas as pd
from auth import auth_component, sidebar_favorites

# Configuration de la page
st.set_page_config(
    page_title="Accueil - Film Recommender",
    page_icon="🎥",
    layout="wide",
)

@st.cache_data
def charger_donnees_films(chemin_fichier='https://raw.githubusercontent.com/Lu6asM/film-recommender/refs/heads/main/data/processed/df_movie_cleaned.csv'):
    try:
        df = pd.read_csv(chemin_fichier)
        df['genres'] = df['Genres'].str.split(', ')
        df['acteurs'] = df['Acteurs'].str.split(', ')
        df['pays'] = df['Pays de Production'].str.split(', ')
        df['langues'] = df['Langues Parlées'].str.split(', ')
        df['companies'] = df['Compagnies de Production'].str.split(', ')
        df['release_year'] = pd.to_datetime(df['Date de Sortie']).dt.year
        df['box_office_millions'] = pd.to_numeric(df['Box Office'], errors='coerce') / 1000000
        df['budget_millions'] = pd.to_numeric(df['Budget'], errors='coerce') / 1000000
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {str(e)}")
        return pd.DataFrame()

def format_large_number(n):
    try:
        n = float(n)
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f}B"
        elif n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        else:
            return str(int(n))
    except (ValueError, TypeError):
        return "0"

def load_stats(movies_df):
    try:
        nb_films = len(movies_df)
        nb_genres = len(set([genre for genres in movies_df['Genres'].str.split(', ') for genre in genres]))
        total_votes = movies_df['Votes imdb'].sum() + movies_df['Votes tmdb'].sum()
        return {
            "films": format_large_number(nb_films),
            "genres": str(nb_genres),
            "votes": format_large_number(total_votes)
        }
    except:
        return {
            "films": "5K",
            "genres": "10",
            "votes": "1M"
        }

def main():
    # Style CSS personnalisé
    st.markdown("""
    <style>
    .feature-card {
        background-color: rgba(255, 87, 51, 0.1);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: 100%;
        border: 1px solid rgba(255, 87, 51, 0.2);
    }
    .metric-card {
        background-color: rgba(255, 87, 51, 0.1);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid rgba(255, 87, 51, 0.2);
    }
    .feature-icon {
        font-size: 2em;
        margin-bottom: 10px;
        color: #FF5733;
    }
    .feature-title {
        color: #FF5733;
        font-size: 1.2em;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #FF5733;
    }
    .metric-label {
        color: #666;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Chargement des données
    movies_df = charger_donnees_films()

    # Ajout du composant d'authentification
    user_id = auth_component()
    
    if user_id:
        sidebar_favorites(movies_df)

    # En-tête Hero
    st.markdown("""
        <div style='text-align: center; padding: 40px 0;'>
            <h1 style='color: #FF5733; font-size: 3em; margin-bottom: 20px;'>
                🎬 Film Recommender
            </h1>
            <h3 style='color: #666; font-weight: normal; margin-bottom: 30px;'>
                Découvrez votre prochain film préféré
            </h3>
        </div>
    """, unsafe_allow_html=True)

    # Section Navigation
    st.markdown("### 🎯 Nos Services")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>✨</div>
            <div class='feature-title'>Pour Vous</div>
            <p>Obtenez des recommandations personnalisées basées sur vos films préférés grâce à notre algorithme avancé.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Découvrir", key="btn_pour_vous", use_container_width=True):
            st.switch_page("pages/1_✨_Pour_Vous.py")

    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🏆</div>
            <div class='feature-title'>Top Films</div>
            <p>Explorez les films les plus populaires et les mieux notés du moment.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explorer", key="btn_trending", use_container_width=True):
            st.switch_page("pages/3_🏆_A_l'affiche.py")

    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🔍</div>
            <div class='feature-title'>Explorer</div>
            <p>Recherchez et filtrez parmi notre vaste collection de films pour trouver exactement ce que vous cherchez.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Rechercher", key="btn_explorer", use_container_width=True):
            st.switch_page("pages/2_🔍_Découvrir.py")

    # Section Comment ça marche
    st.markdown("### 🛠️ Notre Technologie")
    
    with st.expander("En savoir plus sur notre système de recommandation"):
        col_tech1, col_tech2 = st.columns(2)
        
        with col_tech1:
            st.markdown("""
            #### 📊 Analyse des Données
            - **Préférences utilisateurs** : Analyse approfondie des tendances
            - **Données historiques** : Exploitation des notes et avis
            - **Popularité** : Prise en compte des tendances actuelles
            """)
            
        with col_tech2:
            st.markdown("""
            #### 🔬 Technologies Avancées
            - **TF-IDF** : Analyse sémantique des descriptions
            - **Similarité Cosinus** : Mesure précise des correspondances
            - **Filtrage Collaboratif** : Recommandations personnalisées
            """)

    # Statistiques
    st.markdown("### 📈 Statistiques")
    
    stats = load_stats(movies_df)
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{stats["films"]}+</div>
            <div class='metric-label'>Films disponibles</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_stat2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{stats["genres"]}+</div>
            <div class='metric-label'>Genres différents</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_stat3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{stats["votes"]}+</div>
            <div class='metric-label'>Votes utilisateurs</div>
        </div>
        """, unsafe_allow_html=True)

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
                <img src='https://cdn-icons-png.flaticon.com/512/919/919847.png' width='25'>
            </a>
            <a href='https://film-recommender-74upg7d4c67tatqzqfwdhn.streamlit.app/' target='_blank' style='margin-left: 10px;'>
                <img src='https://cdn0.iconfinder.com/data/icons/ui-essential-filled-line/32/folder-data-file-explorer-finder-512.png' width='25'>
            </a>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()