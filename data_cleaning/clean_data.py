import os
import logging
import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path
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

env_path = Path('../.env')
load_dotenv(dotenv_path=env_path, encoding='utf-8-sig')


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

    def get_movie_details_from_tmdb(self, movie_id, language='fr'):
        """Récupère les détails du film depuis TMDb dans la langue spécifiée"""
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={self.tmdb_api_key}&language={language}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Erreur lors de la récupération des détails du film : {response.status_code}")
            return None

    def get_cast_with_roles(self, tmdb_id):
        """Récupère le casting avec les rôles"""
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={self.tmdb_api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            cast = data.get('cast', [])
            actor_roles = [
                f"{actor['name']} ({actor['character']})"
                for actor in cast[:10]
            ]
            return ", ".join(actor_roles)
        else:
            return None

    def remplacer_synopsis_par_overview_fr(self, df):
        """Remplace la colonne 'Synopsis' par le synopsis en français"""
        required_columns = ['ID tmdb', 'Synopsis']
        for col in required_columns:
            if col not in df.columns:
                logging.warning(f"La colonne '{col}' n'existe pas dans le DataFrame.")
                return df

        for index, row in df.iterrows():
            movie_id = row['ID tmdb']
            movie_details = self.get_movie_details_from_tmdb(movie_id, language='fr')
            if movie_details:
                df.at[index, 'Synopsis'] = movie_details.get('overview', '')

        return df

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

    def _prepare_imdb_data(self) -> pd.DataFrame:
        """Prépare les données IMDb."""
        logging.info("Chargement et préparation des données IMDb")
        
        # Chargement des bases
        title_basics = self._safe_read_csv(
            'https://datasets.imdbws.com/title.basics.tsv.gz', 
            sep='\t', compression='gzip'
        )
        title_ratings = self._safe_read_csv(
            'https://datasets.imdbws.com/title.ratings.tsv.gz', 
            sep='\t', compression='gzip'
        )
        title_akas = self._safe_read_csv(
            'https://datasets.imdbws.com/title.akas.tsv.gz', 
            sep='\t', compression='gzip'
        )
        
        logging.info("Nettoyage des données IMDb de base")
        df = (title_basics[title_basics['titleType'] == 'movie']
            .dropna(subset=['startYear', 'genres'])
            .assign(startYear=lambda x: x['startYear'].astype(int))
            .query('1970 <= startYear <= 2025')
            .merge(title_ratings[title_ratings['numVotes'] > 1000], on='tconst')
            .merge(
                title_akas[title_akas['region'] == 'FR'][['titleId', 'title']]
                .rename(columns={'titleId': 'tconst', 'title': 'Titre Français'}),
                on='tconst', how='left'
            ))
        
        logging.info("Préparation des données de casting IMDb")
        name_basics = self._safe_read_csv(
            'https://datasets.imdbws.com/name.basics.tsv.gz', 
            sep='\t', compression='gzip'
        )
        crew = self._safe_read_csv(
            'https://datasets.imdbws.com/title.crew.tsv.gz', 
            sep='\t', compression='gzip'
        )
        principals = self._safe_read_csv(
            'https://datasets.imdbws.com/title.principals.tsv.gz', 
            sep='\t', compression='gzip'
        )
        
        # Ajout réalisateurs
        directors = (crew.fillna({'directors': 'Unknown'})
                    .assign(directors=lambda x: x['directors'].str.split(','))
                    .explode('directors')
                    .merge(name_basics[['nconst', 'primaryName']], 
                        left_on='directors', right_on='nconst', how='left')
                    .groupby('tconst')['primaryName']
                    .agg(list)
                    .reset_index()
                    .rename(columns={'primaryName': 'Réalisateur(s)'}))
        
        df = df.merge(directors, on='tconst', how='left')
        
        # Renommage final
        df = df.rename(columns={
            'tconst': 'ID imdb',
            'primaryTitle': 'Titre Original',
            'averageRating': 'Note imdb',
            'numVotes': 'Votes imdb'
        })
        
        df["Titre Français"] = df["Titre Français"].fillna(df["Titre Original"])
        
        return df

    def _prepare_tmdb_data(self) -> pd.DataFrame:
        """Prépare les données TMDB."""
        logging.info("Chargement et préparation des données TMDB")
        cols_needed = [
            'id', 'backdrop_path', 'budget', 'genres', 'imdb_id', 
            'original_language', 'overview', 'popularity', 'poster_path', 
            'production_countries', 'release_date', 'revenue', 'runtime',
            'spoken_languages', 'vote_average', 'vote_count', 'production_companies'
        ]
        
        df = (self._safe_read_csv('../data/raw/tmdb_full.csv')
            [cols_needed]
            .rename(columns={
                'id': 'ID tmdb', 'backdrop_path': 'Image de Fond',
                'budget': 'Budget', 'genres': 'Genres',
                'overview': 'Synopsis', 'original_language': 'Langue Originale',
                'popularity': 'Popularité', 'poster_path': 'Affiche',
                'production_countries': 'Pays de Production',
                'release_date': 'Date de Sortie', 'revenue': 'Box Office',
                'runtime': 'Durée', 'spoken_languages': 'Langues Parlées',
                'vote_average': 'Note tmdb', 'vote_count': 'Votes tmdb',
                'production_companies': 'Compagnies de Production'
            }))
        
        # Nettoyage des colonnes de type liste
        for col in ['Pays de Production', 'Compagnies de Production', 'Langues Parlées', 'Genres']:
            df[col] = (df[col]
                    .apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
                    .str.strip('[]')
                    .str.replace("'", ""))
        
        return df

    def _enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrichit les données avec les API calls."""
        logging.info("Enrichissement des données avec les API calls (peut prendre du temps)")
        
        logging.info("- Ajout des acteurs et leurs rôles")
        df['Acteurs'] = df['ID tmdb'].apply(self.get_cast_with_roles)
        
        logging.info("- Mise à jour des synopsis en français")
        df = self.remplacer_synopsis_par_overview_fr(df)
        
        logging.info("- Ajout des mots-clés")
        df['Mots-Clés'] = df['ID tmdb'].apply(self.get_movie_keywords)
        
        return df

    def _categorize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute les catégorisations aux données."""
        logging.info("Ajout des catégorisations")
        return df.assign(
            Réputation=lambda x: x['Votes imdb'].apply(self.categorize_votes),
            Métrage=lambda x: x['Durée'].apply(self.categorize_times),
            Décennie=lambda x: x['Date de Sortie'].apply(
                lambda d: self.categorize_years(int(str(d)[:4])) if isinstance(d, str) else None
            ),
            Genre_Principal=lambda x: x['Genres'].str.split(',').str[0]
        )

    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applique tous les filtres de qualité."""
        logging.info("Application des filtres de qualité")
        
        # Critères de popularité et langue
        mask_popularity = (
            ((df['Votes imdb'] > 8000) & (df['Popularité'] > 5) & 
            (df['Langue Originale'].str.contains('fr', case=False, na=False))) |
            ((df['Votes imdb'] > 15000) & (df['Popularité'] > 7.5) & 
            (df['Langues Parlées'].str.contains('French', case=False, na=False))) |
            ((df['Votes imdb'] > 20000) & (df['Popularité'] > 10) & 
            (df['Langue Originale'].str.contains('en', case=False, na=False))) |
            ((df['Votes imdb'] > 50000) & (df['Popularité'] > 25))
        )
        
        df = df[mask_popularity].copy()
        
        # Filtres de notes et dates
        df = df[
            ~((df['Note imdb'] < 4) & (df['Note tmdb'] < 4) & 
            (df['Date de Sortie'] < '2025-01-01'))
        ]
        
        df = df[
            ~((df['Note imdb'] < 8) & (df['Date de Sortie'] < '2000-01-01'))
        ]
        
        # Filtres finaux
        df = df[df['Genre Principal'] != 'Documentary']
        
        return df.drop_duplicates(subset='Titre Original')

    def clean_data(self, output_path: str = '../data/cleaned/df_movie_cleaned.csv'):
        """Processus complet de nettoyage des données."""
        logging.info("Début du nettoyage des données")
        
        # Préparation des données
        df_imdb = self._prepare_imdb_data()
        df_tmdb = self._prepare_tmdb_data()
        
        # Fusion des données
        logging.info("Fusion des données IMDb et TMDB")
        df = pd.merge(df_imdb, df_tmdb, left_on='ID imdb', right_on='imdb_id')
        
        # Enrichissement et catégorisation
        df = self._enrich_data(df)
        df = self._categorize_data(df)
        
        # Application des filtres
        df = self._apply_filters(df)
        
        # Sélection des colonnes finales
        cols_order = [
            'ID imdb', 'ID tmdb', 'Titre Original', 'Titre Français', 
            'Réalisateur(s)', 'Acteurs', 'Budget', 'Genres', 'Mots-Clés', 
            'Genre Principal', 'Date de Sortie', 'Décennie', 'Langue Originale',
            'Langues Parlées', 'Synopsis', 'Popularité', 'Réputation', 'Affiche',
            'Image de Fond', 'Durée', 'Métrage', 'Note tmdb', 'Votes tmdb',
            'Note imdb', 'Votes imdb', 'Compagnies de Production',
            'Pays de Production', 'Box Office'
        ]
        
        df = df[cols_order]
        
        # Export
        logging.info(f"Export des données nettoyées vers {output_path}")
        df.to_csv(output_path, index=False)
        
        logging.info("Nettoyage des données terminé avec succès")
        return df

def main():
    try:
        cleaner = MovieDataCleaner()
        cleaner.clean_data()
    except Exception as e:
        logging.critical(f"Erreur critique lors du nettoyage des données : {e}")
        raise

if __name__ == "__main__":
    main()