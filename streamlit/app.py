import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import plotly.express as px


st.title('Analyse sur les films 🎞️')



# Setup
try:
    df = pd.read_csv("../data/processed/df_movie_cleaned.csv", nrows=4000)
    df['Genre Principal'] = df['Genres'].apply(lambda x: x.split(',')[0] if isinstance(x, str) else x)
    df["Genres"] = df["Genres"].apply(lambda x: x.split(",") if isinstance(x, str) else x)
    df["Nom du/des Réalisateur(s)"] = df["Nom du/des Réalisateur(s)"].apply(lambda x: x.split(",") if isinstance(x, str) else x)
except FileNotFoundError:
    st.error("Le fichier 'df_cleaned_v2.csv' est introuvable.")
    st.stop()
except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
    st.stop()



# Sidebar
st.sidebar.header("Options")
if st.sidebar.checkbox("Afficher le dataset original"):
    st.subheader("Dataset original :")
    st.write(df)
    
# Filtrage des données
if st.sidebar.checkbox("Appliquer un filtre"):
    st.sidebar.subheader("Filtres")
    selected_genre = st.sidebar.multiselect("Sélectionnez un ou plusieurs genres", 
                                            options=np.unique(sum(df["Genres"], [])),
                                            default=None)


    if selected_genre:
        df_filtered = df[df["Genres"].apply(lambda x: any(genre in x for genre in selected_genre))]
    else:
        df_filtered = df


    min_year, max_year = st.sidebar.slider("Année", int(df["Année"].min()), int(df["Année"].max()), (1970, 2001))
    df_filtered = df_filtered[(df_filtered["Année"] >= min_year) & (df_filtered["Année"] <= max_year)]


    st.subheader("Dataset filtré :")
    df_filtered


# Section
st.sidebar.header("Sections")
st.sidebar.subheader("Analyse")


# Section : Analyse Primaire
if st.sidebar.checkbox("Primary Analysis"):


    # Répartition des Films par Genre
    st.subheader("Répartition des Films par Genre")
    genre_counts = df["Genre Principal"].value_counts()
    fig3 = px.pie(genre_counts, names=genre_counts.index, values=genre_counts, title="Répartition des Films par Genre")
    st.plotly_chart(fig3)


    # Matrice de Corrélation
    st.subheader("Matrice de Corrélation")
    selected_columns = st.multiselect("Sélectionnez les colonnes numériques", options=df.select_dtypes(include=["float64", "int64"]).columns.tolist(), default=df.select_dtypes(include=["float64", "int64"]).columns.tolist())
    

    if len(selected_columns) > 1:  # Assurez-vous que plus d'une colonne est sélectionnée
        corr = df[selected_columns].corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("Veuillez sélectionner au moins deux colonnes pour afficher la matrice de corrélation.")


    # Histogramme des Notes/Votes
    st.subheader("Distribution des Notes/Votes")
    genre_filter = st.selectbox("Filtrer par Genre Principal", options=["Tous"] + df["Genre Principal"].unique().tolist(), index=0)

    if genre_filter != "Tous":
        df_filtered = df[df["Genre Principal"] == genre_filter]
    else:
        df_filtered = df


    # Vérification de la présence des colonnes nécessaires avant d'afficher les graphiques
    if 'Note' in df_filtered.columns:
        fig = px.histogram(df_filtered, x="Note", nbins=20, color="Popularité", title="Distribution des Notes", hover_data=["Titre Français"])
        st.plotly_chart(fig)
    else:
        st.warning("La colonne 'Note' n'est pas présente dans les données filtrées.")


    if 'Votes' in df_filtered.columns:
        fig2 = px.histogram(df_filtered, x="Votes", nbins=20, color="Popularité", title="Distribution des Votes", hover_data=["Titre Français"])
        st.plotly_chart(fig2)
    else:
        st.warning("La colonne 'Votes' n'est pas présente dans les données filtrées.")



# if st.sidebar.checkbox("Analyse Primaire"):
#     st.subheader("Répartition des Films par Genre")
#     genre_counts = df["Genre Principal"].value_counts()
#     fig3 = px.pie(genre_counts, names=genre_counts.index, values=genre_counts, title="Répartition des Films par Genre")
#     st.plotly_chart(fig3)

# # Matrice de corrélation
#     if st.sidebar.checkbox("Afficher la matrice de corrélation"):
#         corr = df.select_dtypes(include=["float64", "int64"]).corr()
#         fig, ax = plt.subplots()
#         sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
#         st.pyplot(fig)

# # Section : Histogramme des Notes/Votes
#     if st.sidebar.checkbox("Histogramme des Notes/Votes"):

#         st.subheader("Distribution des Notes/Votes")
#         if 'Note' in df_filtered.columns:
#             fig = px.histogram(df_filtered, x="Note", nbins=20, color="Popularité", title="Distribution des Notes", 
#                            hover_data=["Titre Français"])
#             st.plotly_chart(fig)

#         if 'Votes' in df_filtered.columns:
#             fig2 = px.histogram(df_filtered, x="Votes", nbins=20, color="Popularité", title="Distribution des Votes", 
#                                 hover_data=["Titre Français"])
#             st.plotly_chart(fig2)


# Section : Analyse Intéractive
st.sidebar.subheader("Analyse Intéractive")
if st.sidebar.checkbox("Your Own Chart"):
    st.subheader("Faites votre propre analyse 🕵️")


    st.subheader("Paramètres")
    x_axis = st.selectbox("Choisissez la colonne pour l'axe X", options=df.columns, index=5)
    y_axis = st.selectbox("Choisissez la colonne pour l'axe Y", options=df.columns, index=7)
    chart_type = st.radio("Type de graphique", 
                          ["Scatter Plot", "Bar Plot", "Line Plot", "Area Plot", "Histogram", 
                           "Box Plot", "Pie Chart", "Violin Plot", "Bubble Chart"], index=0)

    if chart_type == "Scatter Plot":
        fig = px.scatter(df, x=x_axis, y=y_axis, color="Popularité", hover_data=["Titre Français"])
    elif chart_type == "Bar Plot":
        fig = px.bar(df, x=x_axis, y=y_axis, color="Popularité", hover_data=["Titre Français"])
    elif chart_type == "Line Plot":
        fig = px.line(df, x=x_axis, y=y_axis, color="Popularité", hover_data=["Titre Français"])
    elif chart_type == "Area Plot":
        fig = px.area(df, x=x_axis, y=y_axis, color="Popularité", hover_data=["Titre Français"])
    elif chart_type == "Histogram":
        fig = px.histogram(df, x=x_axis, color="Popularité", hover_data=["Titre Français"])
    elif chart_type == "Box Plot":
        fig = px.box(df, x=x_axis, y=y_axis, color="Popularité", hover_data=["Titre Français"])
    elif chart_type == "Pie Chart":
        fig = px.pie(df, names=x_axis, values=y_axis, hover_data=["Titre Français"])
    elif chart_type == "Violin Plot":
        fig = px.violin(df, x=x_axis, y=y_axis, color="Popularité", hover_data=["Titre Français"])
    elif chart_type == "Bubble Chart":
        fig = px.scatter(df, x=x_axis, y=y_axis, size="Popularité", color="Popularité", hover_data=["Titre Français"])


    st.plotly_chart(fig)


# Section : Suggestion de films
st.sidebar.subheader("Analyse Suggestion")
if st.sidebar.checkbox("Pocket Suggester"):
    

    st.subheader("Suggestion par Popularité")
    selected_popularity = st.radio("Filtrer par Popularité", df["Popularité"].unique(), index=0)
    suggested_movies = df[df["Popularité"] == selected_popularity][["Nom du/des Réalisateur(s)", "Titre Français", "Note", "Genres"]]
    st.write(suggested_movies)
    

    st.subheader("Suggestion par Genres Principal")
    selected_popularity = st.radio("Filtrer par Genres", df["Genre Principal"].unique(), index=0)
    suggested_movies = df[df["Genre Principal"] == selected_popularity][["Nom du/des Réalisateur(s)", "Titre Français", "Note", "Genres", "Popularité"]]
    st.write(suggested_movies)