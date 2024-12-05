import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Fonction pour charger les données
@st.cache_data
def load_data():
    try:
        url = "https://raw.githubusercontent.com/Lu6asM/film-recommender/main/data/processed/df_movie_cleaned.csv"
        df = pd.read_csv(url)
        df["Genres"] = df["Genres"].apply(lambda x: x.split(",") if isinstance(x, str) else x)
        df["Réalisateur(s)"] = df["Réalisateur(s)"].apply(lambda x: x.split(",") if isinstance(x, str) else x)
        return df
    except FileNotFoundError:
        st.error("Le fichier 'df_movie_cleaned.csv' est introuvable.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        st.stop()

# Chargement des données
df = load_data()

# Sidebar
st.sidebar.header("Options")

# Afficher le dataset original
if st.sidebar.checkbox("Afficher le dataset original"):
    st.subheader("Dataset original :")
    st.write(df)

# Filtrage des données
def filter_data(df):
    st.sidebar.subheader("Filtres")
    selected_genre = st.sidebar.multiselect("Sélectionnez un ou plusieurs genres", 
                                            options=np.unique(sum(df["Genres"], [])),
                                            help="Attention cela s'applique à tout les graphique!",
                                            default=None)
    if selected_genre:
        df = df[df["Genres"].apply(lambda x: any(genre in x for genre in selected_genre))]
    
    min_year, max_year = st.sidebar.slider("Année", int(df["Année"].min()), int(df["Année"].max()), (1970, 2013))
    df = df[(df["Année"] >= min_year) & (df["Année"] <= max_year)]
    
    return df

df_filtered = filter_data(df)

# Section d'analyse primaire
def primary_analysis(df):
    st.markdown("# Analyses Primaires 🔍")
    # Répartition des films par genre
    st.subheader("Répartition des Films par Genre")
    genre_counts = df["Genre Principal"].value_counts()
    fig = px.pie(genre_counts, names=genre_counts.index, values=genre_counts, title="Répartition des Films par Genre")
    st.plotly_chart(fig)

    # Matrice de corrélation
    st.subheader("Matrice de Corrélation")
    selected_columns = st.multiselect("Sélectionnez les colonnes numériques", options=df.select_dtypes(include=["float64", "int64"]).columns.tolist())
    if len(selected_columns) > 1:
        corr = df[selected_columns].corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("Veuillez sélectionner au moins deux colonnes pour afficher la matrice de corrélation.")

    st.subheader("Distribution des Notes et Votes")
    genre_filter = st.selectbox("Filtrer par Genre Principal", options=["Tous"] + df["Genre Principal"].unique().tolist(), index=0)
    if genre_filter != "Tous":
        df_filtered = df[df["Genre Principal"] == genre_filter]
    else:
        df_filtered = df

    if 'Note' in df_filtered.columns:
        fig = px.histogram(df_filtered, x="Note", nbins=20, color="Popularité", title="Distribution des Notes", hover_data=["Titre Français"])
        st.plotly_chart(fig)

    if 'Votes' in df_filtered.columns:
        fig = px.histogram(df_filtered, x="Votes", nbins=20, color="Genre Principal", title="Distribution des Votes", log_y=True, hover_data=["Titre Français"])
        st.plotly_chart(fig)

    st.subheader("Nombre de Films par Année")
    if 'Année' in df_filtered.columns:
        films_par_annee = df.groupby("Année").size().reset_index(name="Nombre de Films")
        fig = px.line(films_par_annee, x="Année", y="Nombre de Films", title="Evolution du Nombre de Films par Année")
        st.plotly_chart(fig)

    st.subheader("Distribution des Durées des Films")
    if 'Durée (minutes)' in df_filtered.columns:
        fig = px.box(df, y="Durée (minutes)", title="Distribution des Durées des Films")
        fig.update_layout(yaxis_title="Durée (minutes)")
        st.plotly_chart(fig)

    st.subheader("Relation entre Note et Popularité")
    if 'Note' in df_filtered.columns:
        fig = px.scatter(df, x="Note", y="Popularité", color="Popularité", hover_data=["Titre Français"])
        fig.update_layout(xaxis_title="Note", yaxis_title="Popularité")
        st.plotly_chart(fig)

    st.subheader("Top 10 des Films")
    if 'Genre Principal' in df.columns and 'Votes' in df.columns:
        top_popular_movies = df.nlargest(10, 'Votes')[["Titre Français", "Votes", "Genre Principal"]]
    
        fig = px.bar(top_popular_movies, 
                 x="Titre Français", 
                 y="Votes", 
                 color="Genre Principal",
                 title="Top 10 des Films les Plus Populaires",
                 color_continuous_scale='Viridis')
    
        fig.update_layout(xaxis_title="Titre du Film", yaxis_title="Votes")
    
        st.plotly_chart(fig)
    else:
        st.warning("Les colonnes 'Popularité' ou 'Votes' sont manquantes dans les données.")



# Fonction pour créer des graphiques personnalisés
def custom_chart(df):
    st.markdown("# Your Own Chart 📈")
    st.subheader("Faites votre propre analyse 🕵️")

    # Sélection des colonnes pour les axes
    x_axis = st.selectbox("Choisissez la colonne pour l'axe X", options=df.columns, index=5)
    y_axis = st.selectbox("Choisissez la colonne pour l'axe Y", options=df.columns, index=7)

    # Sélection de la colonne pour la couleur (hue)
    hue_column = st.selectbox("Choisissez la colonne pour la couleur (hue)", options=df.columns)

    # Sélection du type de graphique
    chart_type = st.radio("Type de graphique", 
                          ["Scatter Plot", "Bar Plot", "Line Plot", "Area Plot", "Histogram", 
                           "Box Plot", "Pie Chart", "Violin Plot", "Bubble Chart"], index=0)

    # Gestion du type de graphique selon les types de données
    if chart_type == "Scatter Plot":
        if df[x_axis].dtype in ['float64', 'int64'] and df[y_axis].dtype in ['float64', 'int64']:
            fig = px.scatter(df, x=x_axis, y=y_axis, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("Le Scatter Plot nécessite des colonnes numériques.")
            return
    elif chart_type == "Bar Plot":
        if df[x_axis].dtype == 'object' and df[y_axis].dtype in ['float64', 'int64']:
            fig = px.bar(df, x=x_axis, y=y_axis, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("Le Bar Plot nécessite une colonne catégorique pour l'axe X et une colonne numérique pour l'axe Y.")
            return
    elif chart_type == "Line Plot":
        if df[x_axis].dtype in ['int64', 'float64'] and df[y_axis].dtype in ['int64', 'float64']:
            fig = px.line(df, x=x_axis, y=y_axis, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("Le Line Plot nécessite des colonnes numériques pour les axes X et Y.")
            return
    elif chart_type == "Area Plot":
        if df[x_axis].dtype in ['int64', 'float64'] and df[y_axis].dtype in ['int64', 'float64']:
            fig = px.area(df, x=x_axis, y=y_axis, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("L'Area Plot nécessite des colonnes numériques pour les axes X et Y.")
            return
    elif chart_type == "Histogram":
        if df[x_axis].dtype in ['int64', 'float64']:
            fig = px.histogram(df, x=x_axis, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("L'Histogram nécessite une colonne numérique.")
            return
    elif chart_type == "Box Plot":
        if df[x_axis].dtype == 'object' and df[y_axis].dtype in ['int64', 'float64']:
            fig = px.box(df, x=x_axis, y=y_axis, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("Le Box Plot nécessite une colonne catégorique pour l'axe X et une colonne numérique pour l'axe Y.")
            return
    elif chart_type == "Pie Chart":
        if df[x_axis].dtype == 'object' and df[y_axis].dtype in ['int64', 'float64']:
            fig = px.pie(df, names=x_axis, values=y_axis, hover_data=["Titre Français"])
        else:
            st.warning("Le Pie Chart nécessite une colonne catégorique pour l'axe X et une colonne numérique pour l'axe Y.")
            return
    elif chart_type == "Violin Plot":
        if df[x_axis].dtype == 'object' and df[y_axis].dtype in ['int64', 'float64']:
            fig = px.violin(df, x=x_axis, y=y_axis, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("Le Violin Plot nécessite une colonne catégorique pour l'axe X et une colonne numérique pour l'axe Y.")
            return
    elif chart_type == "Bubble Chart":
        if df[x_axis].dtype in ['float64', 'int64'] and df[y_axis].dtype in ['float64', 'int64']:
            fig = px.scatter(df, x=x_axis, y=y_axis, size=hue_column, color=hue_column, hover_data=["Titre Français"])
        else:
            st.warning("Le Bubble Chart nécessite des colonnes numériques pour les axes X et Y.")
            return

    st.plotly_chart(fig)

# Sidebar pour choisir les sections
st.sidebar.subheader("Analyse")
if st.sidebar.checkbox("Analyse Primaire 🔍"):
    primary_analysis(df_filtered)

st.sidebar.subheader("Analyse Intéractive")
if st.sidebar.checkbox("Your Own Chart 📈"):
    custom_chart(df_filtered)

# Suggestion de films par popularité et genre
def movie_suggester(df):
    st.markdown("# Pocket Suggester 👝")
    st.subheader("Suggestion par Popularité")
    selected_popularity = st.radio("Filtrer par Popularité", df["Popularité"].unique(), index=0)
    suggested_movies = df[df["Popularité"] == selected_popularity][["Réalisateur(s)", "Titre Français", "Note", "Genres"]]
    st.write(suggested_movies)

    st.subheader("Suggestion par Genre Principal")
    selected_genre = st.radio("Filtrer par Genre", df["Genre Principal"].unique(), index=0)
    suggested_movies = df[df["Genre Principal"] == selected_genre][["Réalisateur(s)", "Titre Français", "Note", "Genres", "Popularité"]]
    st.write(suggested_movies)

st.sidebar.subheader("Analyse Suggestion")
if st.sidebar.checkbox("Pocket Suggester 👝"):
    movie_suggester(df_filtered)
