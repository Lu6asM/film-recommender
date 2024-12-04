import pandas as pd
#! === IMPORT ===
#* Les datasets importants
df_title_basics = pd.read_csv('https://datasets.imdbws.com/title.basics.tsv.gz', sep = '\t', compression='gzip', na_values='\\N')
df_title_ratings = pd.read_csv('https://datasets.imdbws.com/title.ratings.tsv.gz', sep = '\t', compression='gzip', na_values='\\N')

#* Les datasets intéressants
df_title_akas = pd.read_csv('https://datasets.imdbws.com/title.akas.tsv.gz', sep = '\t', compression='gzip', na_values='\\N')
df_title_crew = pd.read_csv('https://datasets.imdbws.com/title.crew.tsv.gz', sep = '\t', compression='gzip', na_values='\\N')
df_name_basics = pd.read_csv('https://datasets.imdbws.com/name.basics.tsv.gz', sep = '\t', compression='gzip', na_values='\\N')
df_title_principals = pd.read_csv('https://datasets.imdbws.com/title.principals.tsv.gz', sep='\t', compression='gzip', na_values='\\N')



#! === SETUP ===
#? title_basics

#* Garder uniquement les films
df_title_basics_clean = df_title_basics[df_title_basics['titleType'] == 'movie']

#* Supprimer les lignes avec des données manquantes essentielles
df_title_basics_clean = df_title_basics_clean.dropna(subset=['startYear', 'genres'])

#* Convertir startYear en entier et filtrer les années valides
df_title_basics_clean['startYear'] = df_title_basics_clean['startYear'].astype(int)
df_title_basics_clean = df_title_basics_clean[(df_title_basics_clean['startYear'] >= 1970) & (df_title_basics_clean['startYear'] <= 2024)]

#* Garder les colonnes essentiels
df_title_basics_clean = df_title_basics_clean[['tconst', 'primaryTitle', 'startYear', 'genres', 'runtimeMinutes']]


#? title_rating

#* Supprimer les films avec peu de votes
df_title_ratings_clean = df_title_ratings[df_title_ratings['numVotes'] > 1000]


#? title_akas

#* Garder uniquement les titres de film français
df_title_akas_clean = df_title_akas[df_title_akas['region'] == 'FR']

#* Garder les colonnes essentiels
df_title_akas_clean = df_title_akas_clean[['titleId', 'title']]

#* Renommer l'identifiant
df_title_akas_clean.rename(columns={'titleId' : 'tconst'}, inplace=True)


#? title_crew

#* Remplir les valeurs manquantes avec un indicateur, par exemple 'Unknown'
df_title_crew_clean = df_title_crew.fillna({'directors': 'Unknown'})

#* Transformer la colonne 'directors' en une liste
df_title_crew_clean['directors'] = df_title_crew_clean['directors'].str.split(',')

#* Exploser la colonne 'directors' en lignes individuelles
df_title_crew_clean = df_title_crew_clean.explode('directors')

#* Fusionner les 'directors' avec 'name_basics' pour obtenir les 'primaryName'
title_crew_with_directors = df_title_crew_clean.merge(df_name_basics[['nconst', 'primaryName']], 
                                                     how='left', 
                                                     left_on='directors', 
                                                     right_on='nconst')

#* Regrouper les résultats par 'tconst' pour remettre les réalisateurs sous forme de liste
title_crew_with_directors = title_crew_with_directors.groupby('tconst')['primaryName'].apply(list).reset_index()


#? title_principals

#* Supprimer les lignes avec des valeurs manquantes dans 'category'
df_title_principals_clean = df_title_principals.dropna(subset=['category'])

#* Filtrer les acteurs dans title.principals
df_title_principals_clean = df_title_principals_clean[df_title_principals_clean['category'] == 'actor']

#* Fusionner avec name.basics pour obtenir les noms des acteurs
actors_with_names = pd.merge(df_title_principals_clean, df_name_basics[['nconst', 'primaryName']], on='nconst', how='left')

#* Créer une liste d'acteurs par film
actors_list_per_film = actors_with_names.groupby('tconst')['primaryName'].apply(list).reset_index()



#! === MERGEUP ===
#* Merge de title_basics & title_ratings
df_merged_v1 = df_title_basics_clean.merge(df_title_ratings_clean, on="tconst")

#* Merge de df_merged_v1 & df_title_akas
df_merged_v2 = df_merged_v1.merge(df_title_akas_clean, on='tconst', how='left')

#* Merge de df_merged_v2 & title_crew_with_directors
df_merged_v3 = df_merged_v2.merge(title_crew_with_directors, on='tconst', how='left')

#* Merge de df_merged_v3 & actors_list_per_film
df_merged_v3['Acteurs'] = df_merged_v3['tconst'].map(dict(zip(actors_list_per_film['tconst'], actors_list_per_film['primaryName'])))



#! === EXPORT ===
df_merged_v3.to_csv("../data/raw/df_movie.csv", index=False)



#! === RENAMEUP ===
df_movie = df_merged_v3

#* Renommer les colonnes du dataframe
df_movie.rename(columns={'tconst': 'ID',
                         'primaryTitle': 'Titre Original',
                         'startYear': 'Année',
                         'genres':  'Genres', 
                         'runtimeMinutes': 'Durée (minutes)',
                         'averageRating': 'Note',
                         'numVotes': 'Votes',
                         'title': 'Titre Français',
                         'primaryName': 'Réalisateur(s)'}, inplace=True)



#! === ADDUP ===
#* Ajout de la colonne 'popularité'
def categorize_votes(votes):
    if votes < 25000:
        return "Connu"
    elif 25000 <= votes < 100000:
        return "Populaire"
    elif 100000 <= votes < 500000:
        return "Très populaire"
    else:
        return "Blockbuster"

df_movie['Popularité'] = df_movie['Votes'].apply(categorize_votes)

#* Ajout de la colonne "métrage"
def categorize_times(duree):
    if duree < 60:
        return "Court-métrage"
    elif 60 <= duree <= 90:
        return "Moyen-métrage"
    else:
        return "Long-métrage"

df_movie['Métrage'] = df_movie['Durée (minutes)'].apply(categorize_times)

#* Ajout de la colonne 'décennie'
def categorize_years(year):
    if 1970 <= year <= 1979:
        return "70°s"
    if 1980 <= year <= 1989:
        return "80°s"
    if 1990 <= year <= 1999:
        return "90°s"
    if 2000 <= year <= 2009:
        return "2000"
    if 2010 <= year <= 2019:
        return "2010"
    if 2020 <= year <= 2029:
        return "2020"

df_movie['Décennie'] = df_movie['Année'].apply(categorize_years)

#* Repositionner les colonnes
df_movie = df_movie[['ID', 'Réalisateur(s)', 'Titre Original', 'Titre Français', 'Métrage', 'Durée (minutes)', 'Année', 'Décennie', 'Genres', 'Note', 'Votes', 'Popularité', 'Acteurs']]



#! === CLEANUP V1 ===
#* Supprimer les doublons
df_movie_cleaned_v1 = df_movie.drop_duplicates(subset='ID')

#* Supprimer les films avec moins de 15 000 votes
df_movie_cleaned_v1 = df_movie_cleaned_v1[df_movie_cleaned_v1['Votes'] > 15000]

#* Remplacer les valeurs manquantes dans 'Titre Français' par les valeurs de 'Titre'
df_movie_cleaned_v1['Titre Français'] = df_movie_cleaned_v1['Titre Français'].fillna(df_movie_cleaned_v1['Titre Original'])



#! === CLEANUP V2 ===
#* Supprimer les films avec une note inférieur à 5
df_movie_cleaned_v2 = df_movie_cleaned_v1[df_movie_cleaned_v1['Note'] > 5]

#* Supprimer les films avec une note inférieur à 8 et sortis avant 2000
df_movie_cleaned_v2 = df_movie_cleaned_v2[~((df_movie_cleaned_v2['Note'] < 8) & (df_movie_cleaned_v2['Année'] < 2000))]



#! === EXPORT ===
df_movie_cleaned_v2.to_csv("../data/processed/df_movie_cleaned.csv", index=False)
