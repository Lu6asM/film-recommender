import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import colorama
from colorama import Fore, Style
import time
import random

# Initialisation de colorama pour les couleurs dans le terminal
colorama.init()

def print_header(text):
    """Affiche un header formaté"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{text.center(80)}")
    print(f"{'='*80}{Style.RESET_ALL}\n")

def print_section(text):
    """Affiche une section formatée"""
    print(f"\n{Fore.GREEN}▶ {text}{Style.RESET_ALL}")

def print_movie(title, year, genres, overview, similarity=None):
    """Affiche les informations d'un film de manière formatée"""
    print(f"\n{Fore.YELLOW}📽 {title} ({year}){Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLUE_EX}Genres:{Style.RESET_ALL} {', '.join(genres)}")
    if similarity is not None:
        print(f"{Fore.MAGENTA}Score de similarité:{Style.RESET_ALL} {similarity:.2f}")
    print(f"{Fore.WHITE}{overview}{Style.RESET_ALL}\n")
    print("-" * 80)

def charger_donnees_films(chemin_fichier):
    """Charge et prépare les données des films"""
    df = pd.read_csv(chemin_fichier)
    
    # Traitement des colonnes
    colonnes_list = ['Genres', 'Mots-Clés', 'Acteurs']
    for col in colonnes_list:
        df[col] = df[col].str.split(', ')
    
    # Renommage des colonnes pour plus de clarté
    df['genres'] = df['Genres']
    df['keywords'] = df['Mots-Clés']
    df['title'] = df['Titre Original']
    df['overview'] = df['Synopsis']
    df['release_date'] = df['Date de Sortie']
    df['director'] = df['Réalisateur(s)']
    df['cast'] = df['Acteurs']
    
    return df

def recommander_films(movie_title, movies_df, k=5):
    """Système de recommandation de films"""
    feature_mapping = {
        'genres': 0.4,
        'keywords': 0.2,
        'director': 0.15,
        'cast': 0.15,
        'overview': 0.1
    }

    if movie_title not in movies_df['title'].values:
        raise ValueError(f"Le film '{movie_title}' n'a pas été trouvé dans la base de données.")

    ref_movie = movies_df[movies_df['title'] == movie_title].iloc[0]
    combined_similarity = np.zeros(len(movies_df))
    
    for feature, weight in feature_mapping.items():
        vectorizer = TfidfVectorizer(token_pattern=r'\b\w+\b')
        
        def process_feature(data):
            if isinstance(data, list):
                return ' '.join(map(str, data))
            return str(data)

        feature_data = movies_df[feature].apply(process_feature).fillna('')
        feature_matrix = vectorizer.fit_transform(feature_data)
        ref_vector = vectorizer.transform([process_feature(ref_movie[feature])])
        similarity = cosine_similarity(ref_vector, feature_matrix)[0]
        
        combined_similarity += similarity * weight

    # Score basé sur l'année
    year_diff = abs(pd.to_datetime(movies_df['release_date']).dt.year - 
                   pd.to_datetime(ref_movie['release_date']).year)
    year_score = 1 / (1 + year_diff)
    combined_similarity += year_score * 0.1

    movie_indices = combined_similarity.argsort()[::-1][1:k+1]
    recommended_films = movies_df.iloc[movie_indices].copy()
    recommended_films['similarity_score'] = combined_similarity[movie_indices]
    
    return recommended_films.sort_values('similarity_score', ascending=False)

def demonstration():
    """Fonction principale de démonstration"""
    print_header("Système de Recommandation de Films")
    print("Chargement des données...")
    
    # Chargement des données
    try:
        movies_df = charger_donnees_films('https://raw.githubusercontent.com/Lu6asM/film-recommender/refs/heads/main/data/processed/df_movie_cleaned.csv')
        print(f"{Fore.GREEN}✓ Base de données chargée avec succès : {len(movies_df)} films{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Erreur lors du chargement des données : {str(e)}{Style.RESET_ALL}")
        return

    # Films pour la démonstration
    films_demo = [
        "The Dark Knight",
        "Inception",
        "Pulp Fiction",
        "The Matrix",
        "Forrest Gump"
    ]

    print_section("Démonstration du système de recommandation")
    print(f"Films disponibles pour la démonstration : {', '.join(films_demo)}")

    while True:
        try:
            choice = input(f"\n{Fore.YELLOW}Choisissez un film (ou 'q' pour quitter) : {Style.RESET_ALL}")
            if choice.lower() == 'q':
                break

            if choice.strip() == "":
                choice = random.choice(films_demo)
                print(f"{Fore.GREEN}Film choisi aléatoirement : {choice}{Style.RESET_ALL}")

            film = movies_df[movies_df['title'] == choice].iloc[0]
            print_movie(
                film['title'],
                pd.to_datetime(film['release_date']).year,
                film['genres'],
                film['overview']
            )

            print(f"{Fore.CYAN}Recherche des recommandations...{Style.RESET_ALL}")
            time.sleep(1)  # Effet de "calcul"

            recommendations = recommander_films(choice, movies_df, k=5)
            print_section(f"Top 5 des films recommandés basés sur '{choice}'")
            
            for _, rec in recommendations.iterrows():
                print_movie(
                    rec['title'],
                    pd.to_datetime(rec['release_date']).year,
                    rec['genres'],
                    rec['overview'],
                    rec['similarity_score']
                )
                time.sleep(0.5)  # Pause entre chaque recommandation

        except KeyboardInterrupt:
            print("\nArrêt de la démonstration...")
            break
        except Exception as e:
            print(f"{Fore.RED}Erreur : {str(e)}{Style.RESET_ALL}")
            continue

    print_header("Fin de la démonstration")

if __name__ == "__main__":
    demonstration()