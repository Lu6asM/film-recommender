# **data_cleaning.py**
# ===============================================
# Script de nettoyage et de préparation des datasets IMDb et TMDB
# ===============================================

import pandas as pd
import os



# ===============================================
# **1. Chargement des Datasets IMDb**
# ===============================================
def load_imdb_data():
    """Charge les datasets IMDb nécessaires."""
    print("Étape 1 : Chargement des datasets IMDb...")
    df_title_basics = pd.read_csv('https://datasets.imdbws.com/title.basics.tsv.gz', sep='\t', compression='gzip', na_values='\\N', low_memory=False)
    df_title_ratings = pd.read_csv('https://datasets.imdbws.com/title.ratings.tsv.gz', sep='\t', compression='gzip', na_values='\\N', low_memory=False)
    df_title_akas = pd.read_csv('https://datasets.imdbws.com/title.akas.tsv.gz', sep='\t', compression='gzip', na_values='\\N', low_memory=False)
    df_title_crew = pd.read_csv('https://datasets.imdbws.com/title.crew.tsv.gz', sep='\t', compression='gzip', na_values='\\N', low_memory=False)
    df_name_basics = pd.read_csv('https://datasets.imdbws.com/name.basics.tsv.gz', sep='\t', compression='gzip', na_values='\\N', low_memory=False)
    df_title_principals = pd.read_csv('https://datasets.imdbws.com/title.principals.tsv.gz', sep='\t', compression='gzip', na_values='\\N', low_memory=False)
    print("Étape 1 terminée : Datasets IMDb chargés.")
    return df_title_basics, df_title_ratings, df_title_akas, df_title_crew, df_name_basics, df_title_principals



# ===============================================
# **2. Nettoyage des Datasets IMDb**
# ===============================================
def clean_title_basics(df):
    print("Étape 2.1 : Nettoyage du dataset title.basics...")
    result = (
        df[df['titleType'] == 'movie']
        .dropna(subset=['startYear', 'genres'])
        .assign(startYear=lambda x: x['startYear'].astype(int))
        .query('1970 <= startYear <= 2025')
        [['tconst', 'primaryTitle']]
    )
    print("Étape 2.1 terminée : title.basics nettoyé.")
    return result

def clean_title_ratings(df):
    print("Étape 2.2 : Nettoyage du dataset title.ratings...")
    result = df[df['numVotes'] > 1000]
    print("Étape 2.2 terminée : title.ratings nettoyé.")
    return result

def clean_title_akas(df):
    print("Étape 2.3 : Nettoyage du dataset title.akas...")
    result = (
        df[df['region'] == 'FR']
        [['titleId', 'title']]
        .rename(columns={'titleId': 'tconst', 'title': 'Titre Français'})
    )
    print("Étape 2.3 terminée : title.akas nettoyé.")
    return result

def clean_title_crew(df_crew, df_names):
    print("Étape 2.4 : Nettoyage du dataset title.crew...")
    result = (
        df_crew.fillna({'directors': 'Unknown'})
        .assign(directors=lambda x: x['directors'].str.split(','))
        .explode('directors')
        .merge(df_names[['nconst', 'primaryName']], left_on='directors', right_on='nconst', how='left')
        .groupby('tconst')['primaryName'].apply(list).reset_index()
    )
    print("Étape 2.4 terminée : title.crew nettoyé.")
    return result

def clean_title_principals(df_principals, df_names):
    print("Étape 2.5 : Nettoyage du dataset title.principals...")
    result = (
        df_principals.dropna(subset=['category'])
        .query("category == 'actor'")
        .merge(df_names[['nconst', 'primaryName']], on='nconst', how='left')
        .groupby('tconst')['primaryName'].apply(list).reset_index()
    )
    print("Étape 2.5 terminée : title.principals nettoyé.")
    return result



# ===============================================
# **3. Fusion des Datasets IMDb**
# ===============================================
def merge_imdb_data(df_basics, df_ratings, df_akas, df_crew, df_principals):
    """Fusionne tous les datasets IMDb nettoyés."""
    df_merged = df_basics.merge(df_ratings, on='tconst')
    df_merged = df_merged.merge(df_akas, on='tconst', how='left')
    df_merged = df_merged.merge(df_crew, on='tconst', how='left')
    df_merged['Acteurs'] = df_merged['tconst'].map(dict(zip(df_principals['tconst'], df_principals['primaryName'])))
    
    # Renommage des colonnes après fusion pour plus de clarté
    df_merged.rename(columns={
        'tconst': 'ID',
        'primaryTitle': 'Titre',
        'numVotes': 'Nombre de Votes',
        'Titre Français': 'Titre en Français',
        'primaryName': 'Réalisateur',
        'Acteurs': 'Acteurs'
    }, inplace=True)
    
    return df_merged



# ===============================================
# **4. Nettoyage du Dataset TMDB**
# ===============================================
def clean_tmdb_data(df):
    print("Étape 4 : Nettoyage du dataset TMDB...")
    df = df[[
        'backdrop_path', 'budget', 'genres', 'imdb_id', 'original_language', 'popularity',
        'poster_path', 'production_countries', 'release_date', 'revenue', 'runtime',
        'spoken_languages', 'vote_average', 'vote_count', 'production_companies_name'
    ]]
    df.rename(columns={
        'backdrop_path': 'Image de Fond',
        'budget': 'Budget',
        'genres': 'Genres',
        'imdb_id': 'ID IMDb',
        'original_language': 'Langue Originale',
        'popularity': 'Popularité',
        'poster_path': 'Affiche',
        'production_countries': 'Pays de Production',
        'release_date': 'Date de Sortie',
        'revenue': 'Box Office',
        'runtime': 'Durée',
        'spoken_languages': 'Langues Parlées',
        'vote_average': 'Note tmdb',
        'vote_count': 'Votes tmdb',
        'production_companies_name': 'Compagnies de Production'
    }, inplace=True)
    print("Étape 4 terminée : TMDB nettoyé.")
    return df



# ===============================================
# **5. Fusion IMDb et TMDB**
# ===============================================
def merge_final_data(df_movie, df_tmdb):
    print("Étape 5 : Fusion des datasets IMDb et TMDB...")
    result = pd.merge(df_movie, df_tmdb, left_on='ID', right_on='ID IMDb')
    print("Étape 5 terminée : Fusion des datasets réalisée.")
    return result



# ===============================================
# **6. Exportation des Données**
# ===============================================
def export_data(df, path):
    print(f"Étape 6 : Exportation des données vers {path}...")
    df.to_csv(path, index=False)
    print("Étape 6 terminée : Données exportées.")



# ===============================================
# **Exécution Principale**
# ===============================================
if __name__ == "__main__":
    # Chargement des données
    print("Chargement des datasets IMDb...")
    df_title_basics, df_title_ratings, df_title_akas, df_title_crew, df_name_basics, df_title_principals = load_imdb_data()
    
    # Lecture du dataset TMDB
    print("Lecture du dataset TMDB...")
    df_tmdb = pd.read_csv("C:/Users/koke7/github/film-recommender/data/raw/tmdb_full.csv")
    
    # Nettoyage des données IMDb
    print("Nettoyage du dataset IMDb...")
    df_basics_clean = clean_title_basics(df_title_basics)
    df_ratings_clean = clean_title_ratings(df_title_ratings)
    df_akas_clean = clean_title_akas(df_title_akas)
    df_crew_clean = clean_title_crew(df_title_crew, df_name_basics)
    df_principals_clean = clean_title_principals(df_title_principals, df_name_basics)

    # Fusion des données IMDb
    print("Fusion des données IMDb...")
    df_imdb_clean = merge_imdb_data(df_basics_clean, df_ratings_clean, df_akas_clean, df_crew_clean, df_principals_clean)
    
    # Nettoyage du dataset TMDB
    print("Nettoyage du dataset TMDB...")
    df_tmdb_clean = clean_tmdb_data(df_tmdb)
    
    # Fusion finale des données
    print("Fusion des données IMDb et TMDB...")
    df_final = merge_final_data(df_imdb_clean, df_tmdb_clean)

    # Exportation des données
    print("Exportation des données nettoyées...")
    export_data(df_final, "C:/Users/koke7/github/film-recommender/data/processed/df_movie_cleaned.csv")
    print("Nettoyage et exportation terminés.")
