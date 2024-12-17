import os
import logging
import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dotenv import load_dotenv
from functools import lru_cache

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('movie_data_cleaning.log'),
        logging.StreamHandler()
    ]
)

# Charger les variables d'environnement
load_dotenv()

class MovieDataCleaner:
    def __init__(self, config: Dict = None):
        """
        Initialise le nettoyeur de données de films.
        
        Args:
            config (Dict, optional): Configuration personnalisée pour le nettoyage
        """
        self.tmdb_api_key = os.getenv('TMDB_API_KEY')
        if not self.tmdb_api_key:
            raise ValueError("La clé API TMDB n'est pas définie. Veuillez la configurer dans le fichier .env.")
        
        # Configuration par défaut
        self.default_config = {
            'min_votes_imdb': 5000,
            'min_popularity': 2.5,
            'min_rating_imdb': 4,
            'min_rating_tmdb': 4,
            'allowed_languages': ['fr', 'en']
        }
        
        # Mettre à jour avec la configuration personnalisée
        self.config = {**self.default_config, **(config or {})}
        
        logging.info("Initialisation du nettoyeur de données de films")

    @staticmethod
    def _safe_read_csv(url_or_path: str, **kwargs) -> pd.DataFrame:
        """
        Lecture sécurisée des fichiers CSV/TSV avec gestion des erreurs.
        
        Args:
            url_or_path (str): URL ou chemin du fichier
            **kwargs: Arguments supplémentaires pour pd.read_csv
        
        Returns:
            pd.DataFrame: DataFrame chargé
        """
        try:
            return pd.read_csv(url_or_path, na_values='\\N', **kwargs)
        except Exception as e:
            logging.error(f"Erreur lors du chargement du fichier {url_or_path}: {e}")
            raise

    @lru_cache(maxsize=1000)
    def get_movie_keywords(self, movie_id: int, max_retries: int = 3) -> List[str]:
        """
        Récupère les mots-clés d'un film via l'API TMDB avec mise en cache.
        
        Args:
            movie_id (int): Identifiant du film
            max_retries (int): Nombre maximum de tentatives
        
        Returns:
            List[str]: Liste des mots-clés
        """
        url_keywords = f'https://api.themoviedb.org/3/movie/{movie_id}/keywords'
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url_keywords, 
                    params={'api_key': self.tmdb_api_key, 'language': 'en-US'},
                    timeout=10
                )
                response.raise_for_status()
                
                keywords_data = response.json()
                return [kw['name'] for kw in keywords_data.get('keywords', [])]
            
            except requests.exceptions.RequestException as e:
                logging.warning(f"Tentative {attempt + 1} échouée pour récupérer les mots-clés : {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Impossible de récupérer les mots-clés pour le film {movie_id}")
                    return []

    @staticmethod
    def categorize_votes(votes: int) -> str:
        """Catégorise le nombre de votes."""
        if votes < 50000:
            return "Connu"
        elif 50000 <= votes < 200000:
            return "Populaire"
        elif 200000 <= votes < 1000000:
            return "Très populaire"
        else:
            return "Blockbuster"

    @staticmethod
    def categorize_times(duration: float) -> str:
        """Catégorise la durée des films."""
        if duration < 100:
            return "Court"
        elif 100 <= duration <= 200:
            return "Moyen"
        else:
            return "Long"

    @staticmethod
    def categorize_years(year: int) -> Optional[str]:
        """Catégorise les décennies de sortie."""
        decade_map = {
            (1970, 1979): "70°s",
            (1980, 1989): "80°s",
            (1990, 1999): "90°s",
            (2000, 2009): "2000",
            (2010, 2019): "2010",
            (2020, 2029): "2020"
        }
        
        for (start, end), label in decade_map.items():
            if start <= year <= end:
                return label
        return None

    def clean_data(self, output_path: str = '../data/cleaned/df_movie_cleaned.csv'):
        """
        Processus complet de nettoyage des données.
        
        Args:
            output_path (str): Chemin de sauvegarde du fichier nettoyé
        """
        logging.info("Début du nettoyage des données")

        # Chargement des données IMDb
        logging.info("Chargement des datasets IMDb")
        df_title_basics = self._safe_read_csv(
            'https://datasets.imdbws.com/title.basics.tsv.gz', 
            sep='\t', compression='gzip'
        )
        df_title_ratings = self._safe_read_csv(
            'https://datasets.imdbws.com/title.ratings.tsv.gz', 
            sep='\t', compression='gzip'
        )
        df_title_akas = self._safe_read_csv(
            'https://datasets.imdbws.com/title.akas.tsv.gz', 
            sep='\t', compression='gzip'
        )
        df_title_crew = self._safe_read_csv(
            'https://datasets.imdbws.com/title.crew.tsv.gz', 
            sep='\t', compression='gzip'
        )
        df_name_basics = self._safe_read_csv(
            'https://datasets.imdbws.com/name.basics.tsv.gz', 
            sep='\t', compression='gzip'
        )
        df_title_principals = self._safe_read_csv(
            'https://datasets.imdbws.com/title.principals.tsv.gz', 
            sep='\t', compression='gzip'
        )

        # Nettoyage des données IMDb
        logging.info("Nettoyage des données IMDb")
        
        # Nettoyage title.basics
        df_title_basics_clean = (
            df_title_basics[df_title_basics['titleType'] == 'movie']
            .dropna(subset=['startYear', 'genres'])
            .assign(startYear=lambda x: x['startYear'].astype(int))
            .query('1970 <= startYear <= 2025')
            [['tconst', 'primaryTitle']]
        )

        # Nettoyage title.ratings
        df_title_ratings_clean = df_title_ratings[df_title_ratings['numVotes'] > 1000]

        # Nettoyage title.akas
        df_title_akas_clean = (
            df_title_akas[df_title_akas['region'] == 'FR']
            [['titleId', 'title']]
            .rename(columns={'titleId': 'tconst', 'title': 'Titre Français'})
        )

        # Nettoyage title.crew
        df_title_crew_clean = (
            df_title_crew.fillna({'directors': 'Unknown'})
            .assign(directors=lambda x: x['directors'].str.split(','))
            .explode('directors')
            .merge(df_name_basics[['nconst', 'primaryName']], left_on='directors', right_on='nconst', how='left')
            .groupby('tconst')['primaryName'].apply(list).reset_index()
        )

        # Nettoyage title.principals
        df_title_principals_clean = (
            df_title_principals.dropna(subset=['category'])
            .query("category == 'actor'")
            .merge(df_name_basics[['nconst', 'primaryName']], on='nconst', how='left')
            .groupby('tconst')['primaryName'].apply(list).reset_index()
        )

        # Fusion des datasets IMDb
        logging.info("Fusion des datasets IMDb")
        df_merged_v1 = df_title_basics_clean.merge(df_title_ratings_clean, on='tconst')
        df_merged_v2 = df_merged_v1.merge(df_title_akas_clean, on='tconst', how='left')
        df_merged_v3 = df_merged_v2.merge(df_title_crew_clean, on='tconst', how='left')
        
        # Ajout des acteurs
        actors_map = dict(zip(df_title_principals_clean['tconst'], df_title_principals_clean['primaryName']))
        df_merged_v3['Acteurs'] = df_merged_v3['tconst'].map(actors_map)

        # Chargement des données TMDB
        logging.info("Chargement des données TMDB")
        df_tmdb = self._safe_read_csv('../data/raw/tmdb_full.csv')

        # Nettoyage des colonnes pour le dataset IMDb
        logging.info("Nettoyage des colonnes IMDb")
        df_merged_v3.rename(columns={
            'tconst': 'ID imdb',
            'primaryTitle': 'Titre Original',
            'averageRating': 'Note imdb',
            'numVotes': 'Votes imdb'
        }, inplace=True)
        
        # Nettoyage des colonnes TMDB
        logging.info("Nettoyage des colonnes TMDB")
        df_tmdb.rename(columns={
            'id': 'ID tmdb',
            'backdrop_path': 'Image de Fond',
            'budget': 'Budget',
            'genres': 'Genres',
            'overview': 'Synopsis',
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

        # Nettoyage des listes dans les colonnes TMDB
        for col in ['Pays de Production', 'Compagnies de Production', 'Langues Parlées', 'Genres']:
            df_tmdb[col] = df_tmdb[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            ).str.strip('[]').str.replace("'", "")

        # Fusion finale des datasets
        logging.info("Fusion finale des datasets")
        df_final = pd.merge(df_merged_v3, df_tmdb, left_on='ID imdb', right_on='ID IMDb')

        # Application des critères de filtrage
        logging.info("Filtrage final des données")
        df_movie_cleaned_v1 = df_final[
            ((df_final['Votes imdb'] > 8000) & (df_final['Popularité'] > 5) & (df_final['Langue Originale'].str.contains('fr', case=False, na=False))) |
            ((df_final['Votes imdb'] > 15000) & (df_final['Popularité'] > 7.5) & (df_final['Langues Parlées'].str.contains('French', case=False, na=False))) |
            ((df_final['Votes imdb'] > 20000) & (df_final['Popularité'] > 10) & (df_final['Langue Originale'].str.contains('en', case=False, na=False))) |
            ((df_final['Votes imdb'] > 50000) & (df_final['Popularité'] > 25))
        ]

        # Filtres additionnels
        df_movie_cleaned_v2 = df_movie_cleaned_v1[
            ~((df_movie_cleaned_v1['Note imdb'] < 4) & (df_movie_cleaned_v1['Note tmdb'] < 4) & (df_movie_cleaned_v1['Date de Sortie'] < '2024-01-01'))
        ]
        
        df_movie_cleaned = df_movie_cleaned[
            ~((df_movie_cleaned['Note imdb'] < 8) & (df_movie_cleaned['Date de Sortie'] < '2000-01-01'))
        ]
        
        df_movie_cleaned = df_movie_cleaned.drop_duplicates(subset='Titre Original')
        df_movie_cleaned['Durée'] = pd.to_numeric(df_movie_cleaned['Durée'], errors='coerce')

        # Colonnes catégoriques
        logging.info("Création des colonnes catégoriques")
        df_movie_cleaned['Mots-Clés'] = df_movie_cleaned['ID tmdb'].apply(self.get_movie_keywords)
        df_movie_cleaned['Réputation'] = df_movie_cleaned['Votes imdb'].apply(self.categorize_votes)
        df_movie_cleaned['Métrage'] = df_movie_cleaned['Durée'].apply(self.categorize_times)
        df_movie_cleaned['Décennie'] = df_movie_cleaned['Date de Sortie'].apply(
            lambda x: self.categorize_years(int(str(x)[:4])) if isinstance(x, str) else None
        )
        df_movie_cleaned['Genre Principal'] = df_movie_cleaned['Genres'].apply(
            lambda x: x.split(',')[0] if isinstance(x, str) else x
        )
        
        # Filtres finaux
        df_movie_cleaned = df_movie_cleaned[
            df_movie_cleaned['Genre Principal'] != 'Documentary'
        ]

        # Sélection des colonnes finales
        df_movie_cleaned = df_movie_cleaned[[
            'ID imdb', 'ID tmdb', 'Titre Original', 'Titre Français', 
            'Réalisateur(s)', 'Acteurs', 'Budget', 'Genres', 'Mots-Clés', 
            'Genre Principal', 'Date de Sortie', 'Décennie', 
            'Langue Originale', 'Langues Parlées', 'Synopsis', 
            'Popularité', 'Réputation', 'Affiche', 'Image de Fond', 
            'Durée', 'Métrage', 'Note tmdb', 'Votes tmdb', 
            'Note imdb', 'Votes imdb', 'Compagnies de Production', 
            'Pays de Production', 'Box Office'
        ]]

        # Export du dataframe final
        logging.info(f"Export des données nettoyées vers {output_path}")
        df_movie_cleaned.to_csv(output_path, index=False)
        
        logging.info("Nettoyage des données terminé avec succès")
        return df_movie_cleaned

def main():
    try:
        cleaner = MovieDataCleaner()
        cleaner.clean_data()
    except Exception as e:
        logging.critical(f"Erreur critique lors du nettoyage des données : {e}")
        raise

if __name__ == "__main__":
    main()