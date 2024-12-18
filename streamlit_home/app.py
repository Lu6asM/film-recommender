import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Accueil - Film Recommender",
    page_icon="🎥",
    layout="centered",
)

def main():
    # Titre principal avec une couleur personnalisée
    st.markdown("<h1 style='text-align: center; color: #FF5733;'>Bienvenue dans votre système de recommandation de films</h1>", unsafe_allow_html=True)

    # Description de l'application
    st.markdown(
        """

        <h4 style='text-align: center; color:rgb(255, 156, 134);'>Trouvez votre prochain film préféré !</h4>
        

        Cette application utilise des données avancées pour vous recommander des films en fonction de vos goûts et tendances actuelles.
        Découvrez des recommandations, explorez les films populaires, ou recherchez des informations spécifiques sur vos films préférés.
        """
    , unsafe_allow_html=True)

    # Gestion de la navigation avec des colonnes pour un meilleur design
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🌟 Recommandations", use_container_width=True):
            st.switch_page("pages/recommandations.py")
        st.caption("Découvrez des films recommandés spécialement pour vous.")

    with col2:
        if st.button("📈 Tendances", use_container_width=True):
            st.switch_page("pages/top_movies.py")
        st.caption("Explorez les films les plus populaires du moment.")

    with col3:
        if st.button("🔍 Rechercher", use_container_width=True):
            st.switch_page("pages/recherche.py")
        st.caption("Recherchez des informations sur vos films préférés.")

    # Section informative supplémentaire
    st.markdown("## 🎯 Comment ça marche ?")

    with st.expander("Comprendre nos recommandations"):
        st.write("""
        En combinant ces techniques, notre système vous offre une expérience personnalisée et dynamique, qui évolue avec vos préférences et vos découvertes.  

        Notre système de recommandation utilise une combinaison de :
        - **Analyse des préférences des utilisateurs** : Nous identifions vos préférences en nous basant sur des données recoltés à partir des films comme le nombre de vote, la popularité, la réputation et bien d'autre.

        - **Popularité et tendances actuelles** : Nous prenons également en compte les films populaires et les tendances du moment, car ils pourraient correspondre à vos centres d'intérêt actuels.

        - **Données historiques de notation** : Les notes attribuées par l'ensemble des utilisateurs nous permettent de repérer les tendances générales et de mieux comprendre quels films sont généralement appréciés.

        - **TF-IDF (Term Frequency-Inverse Document Frequency)** : Cette technique évalue l'importance des mots dans un document par rapport à l'ensemble des documents. En l'utilisant sur les descriptions et les casts de films, nous affinons la pertinence des recommandations.   
        """)

    # Statistiques dynamiques (à remplacer avec vos données réelles)
    st.markdown("## 📊 Quelques Chiffres")

    col_stats1, col_stats2, col_stats3 = st.columns(3)

    with col_stats1:
        st.metric("Films", "5 000+")

    with col_stats2:
        st.metric("Genres", "10+")

    with col_stats3:
        st.metric("Utilisateurs", "5 000+")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="color: #909294;">
            Développé avec ❤️ par Lucas Meireles, Farid El Fardi, Elisabeth Tran
        </div>
        <div>
            <a href="https://github.com/Lu6asM/film-recommender" style="color:rgb(0, 255, 170); text-decoration: none;">
                <img src="https://cdn-icons-png.flaticon.com/512/919/919847.png" alt="Github" width="25" height="25">
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: right;">
        <a href="https://film-recommender-74upg7d4c67tatqzqfwdhn.streamlit.app/" style="color:rgb(0, 255, 170); text-decoration: none;">
            <img src="https://cdn0.iconfinder.com/data/icons/ui-essential-filled-line/32/folder-data-file-explorer-finder-512.png" alt="DataSets Explorer" width="25" height="25">
            </a>
    </div>""", unsafe_allow_html=True)

    st.caption("© 2024 Film Recommender | Tous droits réservés")

if __name__ == "__main__":
    main()
