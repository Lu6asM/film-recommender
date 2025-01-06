from config import *
from auth import auth_component, sidebar_favorites
import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Accueil - Film Recommender",
    page_icon="🎥",
    layout="wide",
)
# Chargement des données
@st.cache_data
def load_movie_data(file_path=CSV_URL):
    try:
        df = pd.read_csv(file_path)
        
        # Renommer les colonnes
        df = df.rename(columns=COLUMN_MAPPING)
        
        # Traiter les colonnes de type liste
        list_columns = ['genres', 'actors', 'countries', 'languages', 'keywords', 'companies']
        for col in list_columns:
            df[col] = df[col].str.split(', ')
        
        # Traiter les données numériques
        df['release_year'] = pd.to_datetime(df['release_date']).dt.year
        df['box_office_millions'] = pd.to_numeric(df['box_office'], errors='coerce') / 1_000_000
        df['budget_millions'] = pd.to_numeric(df['budget'], errors='coerce') / 1_000_000
        df['average_rating'] = (df['tmdb_rating'].astype(float) + df['imdb_rating'].astype(float)) / 2
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {str(e)}")
        return pd.DataFrame()

def format_number(number):
    try:
        number = float(number)
        if number >= 1e9:
            return f"{number/1e9:.1f}B"
        elif number >= 1e6:
            return f"{number/1e6:.1f}M"
        elif number >= 1e3:
            return f"{number/1e3:.1f}K"
        return str(int(number))
    except (ValueError, TypeError):
        return "0"

def calculate_stats(df):
    try:
        stats = {
            "films": len(df),
            "genres": len(set([genre for genres in df['genres'] for genre in genres])),
            "votes": df['imdb_votes'].sum() + df['tmdb_votes'].sum()
        }
        return {k: format_number(v) for k, v in stats.items()}
    except:
        return {"films": "5K", "genres": "10", "votes": "1M"}

def render_hero_section():
    st.markdown(f"""
        <div style='text-align: center; padding: 40px 0;'>
            <h1 style='color: {THEME_COLOR}; font-size: 3em; margin-bottom: 20px;'>
                🎬 Film Recommender
            </h1>
            <h3 style='color: #666; font-weight: normal; margin-bottom: 30px;'>
                Découvrez votre prochain film préféré
            </h3>
        </div>
    """, unsafe_allow_html=True)

def render_features_section():
    features = [
        {
            "icon": "✨",
            "title": "Pour Vous",
            "description": "Découvrez des recommandations sur mesure adaptées à vos films préférés grâce à notre système de recommandation avancé.",
            "button": "Découvrir",
            "page": "pages/1_✨_Pour_Vous.py"
        },
        {
            "icon": "🏆",
            "title": "A l'affiche",
            "description": "Explorez les films les plus populaires et les mieux notés du moment.",
            "button": "Explorer",
            "page": "pages/3_🏆_A_l'affiche.py"
        },
        {
            "icon": "🔍",
            "title": "Découvrir",
            "description": "Explorez et affinez vos recherches en fonction de nombreux critères au sein de notre vaste collection de films.",
            "button": "Rechercher",
            "page": "pages/2_🔍_Découvrir.py"
        }
    ]
    
    st.markdown("### 🎯 Nos Services")
    cols = st.columns(3)
    
    for col, feature in zip(cols, features):
        with col:
            st.markdown(f"""
            <div class='movie-card'>
                <div style='font-size: 2em; margin-bottom: 10px; color: {THEME_COLOR};'>{feature['icon']}</div>
                <div style='color: {THEME_COLOR}; font-size: 1.2em; margin-bottom: 10px;'>{feature['title']}</div>
                <p>{feature['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(feature['button'], key=f"btn_{feature['title'].lower()}", use_container_width=True):
                st.switch_page(feature['page'])

def render_technology_section():
    st.markdown("### 🛠️ Notre Technologie")
    
    with st.expander("💡 Comment fonctionne notre système de recommandation ?"):
        # Utilisation de colonnes pour une meilleure organisation
        left_col, right_col = st.columns([3, 2])
        
        with left_col:
            st.markdown("""
                #### 🎯 Notre Algorithme en un Coup d'Œil
                
                Notre système de recommandation utilise une approche sophistiquée basée sur plusieurs critères clés :
                """)
            
            # Utilisation de progress bars pour visualiser les poids
            st.markdown("##### Poids des critères dans l'analyse")
            st.progress(0.4, "📚 Genres (40%)")
            st.progress(0.2, "🔑 Mots-clés (20%)")
            st.progress(0.15, "🎬 Réalisateur (15%)")
            st.progress(0.15, "🎭 Acteurs (15%)")
            st.progress(0.1, "📝 Synopsis (10%)")

        with right_col:
            st.markdown("#### 🔬 Technologies Avancées")
            st.markdown("Notre système s'appuie sur des technologies de pointe :")
            
            # Technologie 1
            st.markdown("""
                <div style='background-color: #131720; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <div style='font-weight: bold;'>🧮 TF-IDF Vectorization</div>
                    <div style='color: #666; font-style: italic;'>Analyse sémantique approfondie</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Technologie 2
            st.markdown("""
                <div style='background-color: #131720; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <div style='font-weight: bold;'>📊 Similarité Cosinus</div>
                    <div style='color: #666; font-style: italic;'>Mesure précise des correspondances</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Technologie 3
            st.markdown("""
                <div style='background-color: #131720; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <div style='font-weight: bold;'>⚡ Traitement en Temps Réel</div>
                    <div style='color: #666; font-style: italic;'>Recommandations instantanées</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Technologie 4
            st.markdown("""
                <div style='background-color: #131720; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <div style='font-weight: bold;'>🔄 Mise à Jour Continue</div>
                    <div style='color: #666; font-style: italic;'>Base de données enrichie régulièrement</div>
                </div>
            """, unsafe_allow_html=True)

        # Section bonus en bas de l'expander
        st.markdown("---")
        bonus_col1, bonus_col2, bonus_col3 = st.columns(3)
        
        with bonus_col1:
            st.markdown("""
                #### 🎯 Pertinence
                Une précision accrue grâce à la pondération intelligente des critères
            """)
            
        with bonus_col2:
            st.markdown("""
                #### ⚡ Performance
                Résultats instantanés grâce à l'optimisation algorithmique
            """)
            
        with bonus_col3:
            st.markdown("""
                #### 🔄 Évolution
                Système qui s'améliore avec chaque nouvelle donnée
            """)

        # Note informative avec un style amélioré
        st.info("""
            **💡 Le saviez-vous ?** Notre système utilise un algorithme sophistiqué qui combine 5 critères principaux 
            et analyse la proximité temporelle pour vous proposer des recommandations personnalisées !
        """)

def render_stats_section(stats):
    st.markdown("### 📈 Statistiques")
    
    metrics = [
        {"value": stats["films"], "label": "Films disponibles"},
        {"value": stats["genres"], "label": "Genres différents"},
        {"value": stats["votes"], "label": "Votes utilisateurs"}
    ]
    
    cols = st.columns(3)
    for col, metric in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class='movie-card' style='text-align: center;'>
                <div style='font-size: 2em; font-weight: bold; color: {THEME_COLOR};'>{metric['value']}+</div>
                <div style='color: #666; margin-top: 5px;'>{metric['label']}</div>
            </div>
            """, unsafe_allow_html=True)

def render_footer():
    st.markdown("---")
    cols = st.columns([3, 1])
    
    with cols[0]:
        st.markdown("Développé avec ❤️ par Lucas Meireles, Farid El Fardi, Elisabeth Tran, Anais Cid")
        st.caption("© 2024 Film Recommender | Tous droits réservés")
    
    with cols[1]:
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

def main():
    # Charger le CSS commun
    st.markdown(COMMON_CSS, unsafe_allow_html=True)
    
    # Charger les données
    movies_df = load_movie_data()
    
    # Authentification
    user_id = auth_component()

    
    if user_id:
        st.sidebar.divider()
        sidebar_favorites(movies_df)
    
    # Interface principale
    render_hero_section()
    render_features_section()
    render_technology_section()
    render_stats_section(calculate_stats(movies_df))
    render_footer()

if __name__ == "__main__":
    main()