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



# st.title("Manipulation de données")

# # df_ = st.selectbox("Quel dataset veux-tu utiliser",['Weather', 'Iris'], index=0)
# # if df_ == 'Weather' :
# #     df = df_weather
# # elif df_ == 'Iris':
# #     df = df_iris

# # st.dataframe(df)

# if len(df) > 500:
#     df_sample = df.sample(500, random_state=42)
#     st.warning("Les graphiques sont basés sur un échantillon de 500 points pour des raisons de performance.")
# else:
#     df_sample = df


# numeric_columns = list(df.select_dtypes(include=['float64', 'int64']).columns)
# if not numeric_columns:
#     st.error("Le DataFrame ne contient pas de colonnes numériques.")
#     st.stop()


# st.title("Création de graphique")

# X = st.selectbox("Choisissez la colonne X", list(df.columns), index=0)
# Y = st.selectbox("Choisissez la colonne Y", list(df.select_dtypes(include=['float64', 'int64']).columns), index=1)

# graph = st.selectbox("Quel graphique veux-tu utiliser",['scatter_chart', 'line_chart', 'bar_chart'], index=0)

# if graph == 'scatter_chart':
#     size = st.selectbox("Choisissez une colonne pour la taille (optionnel)", [None] + numeric_columns, index=0)
#     color = st.selectbox("Choisissez une colonne pour la couleur (optionnel)", [None] + list(df.columns), index=0)
#     fig = px.scatter(df, x=X, y=Y, size=size, color=color)
#     st.plotly_chart(fig)
# elif graph == 'line_chart':
#     fig = px.line(df, x = X, y = Y)
#     st.plotly_chart(fig)
# elif graph == 'bar_chart':
#     fig = px.bar(df, x = X, y = Y)
#     st.plotly_chart(fig)

# matrice = st.checkbox('Afficher la matrice de corrélation')

# if matrice:
#     st.pyplot(fig)






# if st.checkbox('Afficher les premières lignes du DataFrame'):
#     st.write(df.head())

# # Histogramme des notes moyennes
# st.subheader('Répartition des Notes Moyennes des Films')
# fig1, ax1 = plt.subplots(figsize=(8,6))
# ax1.hist(df['Note'], bins=20, color='skyblue', edgecolor='black')
# ax1.set_title('Répartition des Notes Moyennes des Films')
# ax1.set_xlabel('Note Moyenne')
# ax1.set_ylabel('Fréquence')
# st.pyplot(fig1)

# # Nuage de points de Popularité vs Notes
# st.subheader('Popularité vs Note des Films')
# fig2, ax2 = plt.subplots(figsize=(8,6))
# ax2.scatter(df['Note'], df['Popularité'], alpha=0.5, color='orange')
# ax2.set_title('Popularité vs Note des Films')
# ax2.set_xlabel('Note Moyenne')
# ax2.set_ylabel('Popularité')
# st.pyplot(fig2)

# # Diagramme en barres des genres de films
# st.subheader('Répartition des Films par Genre')
# fig3, ax3 = plt.subplots(figsize=(10,6))
# sns.countplot(data=df, x='Genre Principal', palette='viridis', ax=ax3)
# ax3.set_title('Répartition des Films par Genre')
# ax3.set_xlabel('Genres')
# ax3.set_ylabel('Nombre de Films')
# ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45)
# st.pyplot(fig3)

# # Graphique en secteurs pour la répartition des genres
# st.subheader('Répartition des Films par Genre (Graphique en Secteurs)')
# genre_counts = df['Genre Principal'].value_counts()
# fig4, ax4 = plt.subplots(figsize=(8,6))
# ax4.pie(genre_counts, labels=genre_counts.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("Set3", len(genre_counts)))
# ax4.set_title('Répartition des Films par Genre')
# ax4.axis('equal')  # Pour que le graphique soit circulaire
# st.pyplot(fig4)

# # Graphique de la popularité par année
# st.subheader('Popularité des Films par Année')
# popularity_by_year = df.groupby('Décennie')['Votes'].mean().reset_index()
# fig5, ax5 = plt.subplots(figsize=(10,6))
# sns.lineplot(data=popularity_by_year, x='Décennie', y='Votes', marker='o', color='green', ax=ax5)
# ax5.set_title('Popularité des Films par Année')
# ax5.set_xlabel('Année')
# ax5.set_ylabel('Popularité Moyenne')
# st.pyplot(fig5)

# # Boxplot des notes par catégorie de popularité
# st.subheader('Distribution des Notes par Catégorie de Popularité')
# fig6, ax6 = plt.subplots(figsize=(10,6))
# sns.boxplot(data=df, x='Popularité', y='Note', palette='coolwarm', ax=ax6)
# ax6.set_title('Distribution des Notes par Catégorie de Popularité')
# ax6.set_xlabel('Popularité')
# ax6.set_ylabel('Note Moyenne')
# st.pyplot(fig6)

# # Heatmap des réalisateurs par genre
# st.subheader('Répartition des Notes par Genre')
# heatmap_data = pd.crosstab(df['Popularité'], df['Genre Principal'])
# fig7, ax7 = plt.subplots(figsize=(12,8))
# sns.heatmap(heatmap_data, annot=False, cmap='YlGnBu', fmt='d', ax=ax7)
# ax7.set_title('Répartition des Notes par Genre')
# ax7.set_xlabel('Genres')
# ax7.set_ylabel('Réalisateur')
# st.pyplot(fig7)

# # Scatter plot avec les votes
# st.subheader('Votes vs Note Moyenne des Films')
# fig8, ax8 = plt.subplots(figsize=(8,6))
# ax8.scatter(df['Votes'], df['Note'], alpha=0.5, color='purple')
# ax8.set_title('Votes vs Note Moyenne des Films')
# ax8.set_xlabel('Nombre de Votes')
# ax8.set_ylabel('Note Moyenne')
# st.pyplot(fig8)