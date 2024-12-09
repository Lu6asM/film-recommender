# **data_cleaning.py**
# ===============================================
# Script de nettoyage et de préparation des datasets IMDb et TMDB
# ===============================================

import pandas as pd

# Fonction pour classifier les votes
def categorize_votes(votes):
    if votes > 5000:
        return 'Popular'
    elif votes > 1000:
        return 'Average'
    else:
        return 'Low'

# Fonction pour classifier la durée des films
def categorize_times(duration):
    if pd.isna(duration) or duration < 60:
        return 'Short'
    elif duration < 150:
        return 'Medium'
    else:
        return 'Long'

# Fonction pour classifier les décennies de sortie
def categorize_years(year):
    if year < 1980:
        return 'Before 1980'
    elif year < 2000:
        return '1980s - 1990s'
    elif year < 2020:
        return '2000s - 2010s'
    else:
        return '2020s'
    


# ===============================================
# **1. Chargement des Datasets IMDb**
# ===============================================
def load_and_clean_data():
    # Import des données IMDb
    print("Importation des données IMDb...")
    df_title_basics = pd.read_csv('https://datasets.imdbws.com/title.basics.tsv.gz', sep='\t', compression='gzip', na_values='\\N')
    df_title_ratings = pd.read_csv('https://datasets.imdbws.com/title.ratings.tsv.gz', sep='\t', compression='gzip', na_values='\\N')
    df_title_akas = pd.read_csv('https://datasets.imdbws.com/title.akas.tsv.gz', sep='\t', compression='gzip', na_values='\\N')
    df_title_crew = pd.read_csv('https://datasets.imdbws.com/title.crew.tsv.gz', sep='\t', compression='gzip', na_values='\\N')
    df_name_basics = pd.read_csv('https://datasets.imdbws.com/name.basics.tsv.gz', sep='\t', compression='gzip', na_values='\\N')
    df_title_principals = pd.read_csv('https://datasets.imdbws.com/title.principals.tsv.gz', sep='\t', compression='gzip', na_values='\\N')



# ===============================================
# **2. Nettoyage des Datasets IMDb**
# ===============================================

    # Nettoyage des données title.basics
    print("Nettoyage des données IMDb - title.basics...")
    df_title_basics_clean = (
        df_title_basics[df_title_basics['titleType'] == 'movie']
        .dropna(subset=['startYear', 'genres'])
        .assign(startYear=lambda x: x['startYear'].astype(int))
        .query('1970 <= startYear <= 2025')
        [['tconst', 'primaryTitle']]
    )

    # Nettoyage des données title.ratings
    print("Nettoyage des données IMDb - title.ratings...")
    df_title_ratings_clean = df_title_ratings[df_title_ratings['numVotes'] > 1000]

    # Nettoyage des données title.akas
    print("Nettoyage des données IMDb - title.akas...")
    df_title_akas_clean = (
        df_title_akas[df_title_akas['region'] == 'FR']
        [['titleId', 'title']]
        .rename(columns={'titleId': 'tconst', 'title': 'Titre Français'})
    )

    # Nettoyage des données title.crew
    print("Nettoyage des données IMDb - title.crew...")
    df_title_crew_clean = (
        df_title_crew.fillna({'directors': 'Unknown'})
        .assign(directors=lambda x: x['directors'].str.split(','))
        .explode('directors')
        .merge(df_name_basics[['nconst', 'primaryName']], left_on='directors', right_on='nconst', how='left')
        .groupby('tconst')['primaryName'].apply(list).reset_index()
    )

    # Nettoyage des données title.principals
    print("Nettoyage des données IMDb - title.principals...")
    df_title_principals_clean = (
        df_title_principals.dropna(subset=['category'])
        .query("category == 'actor'")
        .merge(df_name_basics[['nconst', 'primaryName']], on='nconst', how='left')
        .groupby('tconst')['primaryName'].apply(list).reset_index()
    )



# ===============================================
# **3. Fusion des Datasets IMDb**
# ===============================================

    # Fusionner les datasets
    print("Fusion des datasets IMDb...")
    df_merged_v1 = df_title_basics_clean.merge(df_title_ratings_clean, on='tconst')
    df_merged_v2 = df_merged_v1.merge(df_title_akas_clean, on='tconst', how='left')
    df_merged_v3 = df_merged_v2.merge(df_title_crew_clean, on='tconst', how='left')
    df_merged_v3['Acteurs'] = df_merged_v3['tconst'].map(dict(zip(df_title_principals_clean['tconst'], df_title_principals_clean['primaryName'])))

    # Export du dataframe IMDb final
    print("Export du dataframe IMDb final...")
    df_merged_v3.to_csv("../data/raw/df_movie.csv", index=False)



# ===============================================
# **4. Nettoyage du Dataset TMDB**
# ===============================================

    # Chargement des données TMDB
    print("Chargement des données TMDB...")
    df_tmdb = pd.read_csv('../data/raw/tmdb_full.csv')
    df_movie = pd.read_csv('../data/raw/df_movie.csv')


    # Nettoyage des colonnes pour le dataset IMDb (df_movie)
    print("Nettoyage des colonnes pour le dataset IMDb...")
    df_movie.rename(columns={
        'tconst': 'ID',
        'primaryTitle': 'Titre Original',
        'averageRating': 'Note imdb',
        'numVotes': 'Votes imdb',
        'title': 'Titre Français',
        'actors': 'Acteurs',
        'primaryName': 'Réalisateur(s)'
    }, inplace=True)
    df_movie['Réalisateur(s)'] = df_movie['Réalisateur(s)'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x).str.strip("[]").str.replace("'", "")
    df_movie['Acteurs'] = df_movie['Acteurs'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x).str.strip("[]").str.replace("'", "")



# ===============================================
# **5. Fusion IMDb et TMDB**
# ===============================================

    # Nettoyage des colonnes pour le dataset TMDB (df_tmdb)
    print("Nettoyage des colonnes pour le dataset TMDB...")
    df_tmdb.rename(columns={
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
    df_tmdb['Pays de Production'] = df_tmdb['Pays de Production'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x).str.strip("[]").str.replace("'", "")
    df_tmdb['Compagnies de Production'] = df_tmdb['Compagnies de Production'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x).str.strip("[]").str.replace("'", "")
    df_tmdb['Langues Parlées'] = df_tmdb['Langues Parlées'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x).str.strip("[]").str.replace("'", "")
    df_tmdb['Genres'] = df_tmdb['Genres'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x).str.strip("[]").str.replace("'", "")

    # Fusionner les datasets pour créer df_final
    print("Fusion des datasets IMDb et TMDB...")
    df_final = pd.merge(df_movie, df_tmdb, left_on='ID', right_on='ID IMDb')

    # Critères de sélection pour le nettoyage final
    print("Nettoyage final des données IMDb...")
    df_movie_cleaned_v1 = df_final[
        ((df_final['Votes imdb'] > 5000) & (df_final['Popularité'] > 2.5) & (df_final['Langue Originale'] == 'fr')) |
        ((df_final['Votes imdb'] > 15000) & (df_final['Popularité'] > 7.5) & (df_final['Langues Parlées'].apply(lambda x: 'fr' in x))) |
        ((df_final['Votes imdb'] > 30000) & (df_final['Popularité'] > 15) & (df_final['Langue Originale'] == 'en')) |
        (df_final['Votes imdb'] > 50000) & (df_final['Popularité'] > 25)
    ]
    df_movie_cleaned_v2 = df_movie_cleaned_v1[(df_movie_cleaned_v1['Note imdb'] > 4) & (df_movie_cleaned_v1['Note tmdb'] > 4)]
    df_movie_cleaned_v3 = df_movie_cleaned_v2[~((df_movie_cleaned_v2['Note imdb'] < 8) & (df_movie_cleaned_v2['Date de Sortie'] < '2000-01-01'))]
    df_movie_cleaned_v4 = df_movie_cleaned_v3.drop_duplicates(subset='Titre Original').copy()
    df_movie_cleaned_v4['Durée'] = pd.to_numeric(df_movie_cleaned_v4['Durée'], errors='coerce')

    # Colonnes catégoriques
    print("Création de colonnes catégoriques pour le nettoyage final...")
    df_movie_cleaned_v4['Réputation'] = df_movie_cleaned_v4['Votes imdb'].apply(categorize_votes)
    df_movie_cleaned_v4['Métrage'] = df_movie_cleaned_v4['Durée'].apply(categorize_times)
    df_movie_cleaned_v4['Décennie'] = df_movie_cleaned_v4['Date de Sortie'].apply(lambda x: categorize_years(int(str(x)[:4])) if isinstance(x, str) else None)
    df_movie_cleaned_v4['Genre Principal'] = df_movie_cleaned_v4['Genres'].apply(lambda x: x.split(',')[0] if isinstance(x, str) else x)
    df_movie_cleaned_v4 = df_movie_cleaned_v4[df_movie_cleaned_v4['Genre Principal'] != 'Documentary']
    df_movie_cleaned_v4 = df_movie_cleaned_v4[
        ['ID', 'Titre Original', 'Titre Français', 'Réalisateur(s)', 'Acteurs', 'Budget', 'Genres', 'Genre Principal', 'Date de Sortie', 'Décennie',
         'Langue Originale', 'Langues Parlées', 'Réputation', 'Métrage', 'Durée', 'Affiche', 'Image de Fond', 'Note imdb', 'Note tmdb', 'Popularité', 'Votes imdb', 'Votes tmdb', 'Box Office', 'Compagnies de Production']
    ]

    # Export du dataframe final
    print("Données traitées et nettoyées exportées avec succès.")
    df_movie_cleaned_v4.to_csv("../data/cleaned/df_movie_cleaned.csv", index=False)



# ===============================================
# **Exécution Principale**
# ===============================================
if __name__ == "__main__":
    load_and_clean_data()