# 🎥 Film Recommender System

## 📋 Description
Ce projet vise à créer un système de suggestion de films basé sur un dataset. Il comprend plusieurs étapes clés :
1. **Nettoyage des données :** Préparation des données brutes pour l'analyse.
2. **Visualisation des données :** Une application Streamlit permettant de générer automatiquement des graphiques pour explorer les données.
3. **Système de recommandation :** Utilisation de techniques de machine learning pour recommander des films.
4. **Interface utilisateur :** Une page d'accueil interactive via Streamlit pour présenter les fonctionnalités principales.

---

## ✨ Fonctionnalités
- **Nettoyage des données :**
  - Scripts pour analyser et nettoyer les données brutes.
  - Enregistrement des datasets nettoyés.
- **Visualisation des données :**
  - Application Streamlit pour explorer les statistiques du dataset (genres, notes, etc.).
- **Système de recommandation :**
  - Modèle de machine learning entraîné pour générer des recommandations personnalisées.
  - KPIs pour évaluer les performances du système.
- **Page d'accueil Streamlit :**
  - Accès à toutes les fonctionnalités via une interface centralisée.

---

## 🗂 Structure du projet
```plaintext
/data_cleaning/    # Scripts et données liés au nettoyage
/streamlit_viz/    # Application Streamlit pour la visualisation du dataset
/recommendation/   # Scripts pour le système de recommandation
/streamlit_home/   # Application Streamlit pour la page d'accueil
/data/             # Datasets (bruts et nettoyés)
/notebooks/        # Jupyter Notebooks pour la documentation des processus
README.md          # Documentation
requirements.txt   # Liste des dépendances Python
```

---

## 🚀 Installation
Pour exécuter ce projet localement, suivez ces étapes :

1. Clonez le dépôt :

    ```bash
    git clone [https://github.com/yourusername/film-recommender.git]
    cd film-recommender
    ```

2. Créez un environnement virtuel :

    ```bash
    python -m venv venv
    ```

3. Activez l'environnement virtuel :

    - Sur macOS/Linux :

        ```bash
        source venv/bin/activate
        ```

    - Sur Windows :

        ```bash
        venv\Scripts\activate
        ```

4. Installez les dépendances nécessaires :

    ```bash
    pip install -r requirements.txt
    ```
    
---

## 🛠 Usage
- **Nettoyage des données :** Lancez les scripts dans le dossier `/data_cleaning/` :
- 
    ```bash
    python data_cleaning/clean_data.py
    ```
- **Visualisation des données :** Démarrez l'application Streamlit :
- 
    ```bash
    streamlit run streamlit_viz/app.py
    ```
- **Système de recommandation :** Exécutez le script d'entraînement ou les prédictions :
- 
    ```bash
    python recommendation/train_model.py
    ```
- **Page d'accueil Streamlit :** Lancez l'interface de recommendation :
- 
    ```bash
    streamlit run streamlit_home/app.py
    ```
  
---

## 🛠 Technologies utilisées
- **Langage :** Python
- **Frameworks :** Pandas, Scikit-learn, Streamlit
- **Visualisation :** Matplotlib, Seaborn
- **Gestion des versions :** Git, GitHub

## 🚧 Améliorations futures
- Optimisation des algorithmes de recommandation.
- Intégration de fonctionnalités supplémentaires pour l'analyse utilisateur.
