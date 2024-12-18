import sqlite3
import streamlit as st
import hashlib
import os
from datetime import datetime

class AuthManager:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), ".streamlit", "film_recommender.db")
        self.init_database()

    def init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            print(f"Connexion à la DB : {self.db_path}")  # Debug log

            # Table utilisateurs
            c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Table favoris
            c.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                movie_id TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                PRIMARY KEY (user_id, movie_id)
            )
            ''')

            conn.commit()

        except Exception as e:
            st.error(f"Erreur d'initialisation DB : {e}")

        finally:
            if conn:
                conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            password_hash = self.hash_password(password)
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                     (username, password_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            if conn:
                conn.close()

    def verify_user(self, username, password):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            password_hash = self.hash_password(password)
            c.execute('SELECT user_id FROM users WHERE username = ? AND password_hash = ?',
                     (username, password_hash))
            result = c.fetchone()
            return result[0] if result else None
        finally:
            if conn:
                conn.close()

    def get_favorites(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT movie_id FROM favorites WHERE user_id = ?', (user_id,))
            results = c.fetchall()
            favorites = [r[0] for r in results]
            print(f"Debug - Favoris user {user_id}: {favorites}")  # Debug log
            return favorites
        except Exception as e:
            st.error(f"Erreur get_favorites: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def add_favorite(self, user_id, movie_id):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('INSERT INTO favorites (user_id, movie_id) VALUES (?, ?)',
                     (user_id, movie_id))
            conn.commit()
            print(f"Debug - Ajout favori: user={user_id}, film={movie_id}")  # Debug log
            return True
        except Exception as e:
            st.error(f"Erreur add_favorite: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def remove_favorite(self, user_id, movie_id):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('DELETE FROM favorites WHERE user_id = ? AND movie_id = ?',
                     (user_id, movie_id))
            conn.commit()
            print(f"Debug - Suppression favori: user={user_id}, film={movie_id}")  # Debug log
        except Exception as e:
            st.error(f"Erreur remove_favorite: {e}")
        finally:
            if conn:
                conn.close()

def auth_component():
    auth = AuthManager()
    
    # Initialisation des variables de session
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    # Affichage état session (debug)
    print("Debug - Session state:", dict(st.session_state))  # Debug log
    
    if st.session_state.user_id is None:
        st.sidebar.markdown("### 👤 Connexion")
        tab1, tab2 = st.sidebar.tabs(["Connexion", "Inscription"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Nom d'utilisateur")
                password = st.text_input("Mot de passe", type="password")
                submit = st.form_submit_button("Se connecter")
                
                if submit:
                    user_id = auth.verify_user(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.favorites = auth.get_favorites(user_id)
                        st.success("Connexion réussie!")
                        st.rerun()
                    else:
                        st.error("Identifiants invalides")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Choisir un nom d'utilisateur")
                new_password = st.text_input("Choisir un mot de passe", type="password")
                confirm_password = st.text_input("Confirmer le mot de passe", type="password")
                submit = st.form_submit_button("S'inscrire")
                
                if submit:
                    if new_password != confirm_password:
                        st.error("Les mots de passe ne correspondent pas")
                    elif len(new_password) < 6:
                        st.error("Le mot de passe doit contenir au moins 6 caractères")
                    else:
                        if auth.register_user(new_username, new_password):
                            st.success("Inscription réussie! Vous pouvez maintenant vous connecter.")
                        else:
                            st.error("Ce nom d'utilisateur existe déjà")
    
    else:
        st.sidebar.markdown(f"### 👤 Connecté en tant que {st.session_state.username}")
        if st.sidebar.button("Se déconnecter"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    return st.session_state.get('user_id')

def favorite_button(movie_id, movie_title, unique_key=""):
    auth = AuthManager()
    user_id = st.session_state.get('user_id')
    
    if user_id:
        favorites = auth.get_favorites(user_id)
        is_favorite = str(movie_id) in [str(f) for f in favorites]
        
        button_key = f"fav_{movie_id}_{unique_key}"
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if is_favorite:
                if st.button("❤️", key=button_key):
                    auth.remove_favorite(user_id, str(movie_id))
                    st.session_state.favorites = auth.get_favorites(user_id)
                    st.rerun()
            else:
                if st.button("🤍", key=button_key):
                    auth.add_favorite(user_id, str(movie_id))
                    st.session_state.favorites = auth.get_favorites(user_id)
                    st.rerun()

def sidebar_favorites(movies_df):
    user_id = st.session_state.get('user_id')
    if user_id:
        auth = AuthManager()
        favorites = auth.get_favorites(user_id)
        
        if favorites:
            st.sidebar.markdown("### ❤️ Vos Favoris")
            fav_movies = movies_df[movies_df['ID tmdb'].astype(str).isin([str(f) for f in favorites])]
            
            for _, movie in fav_movies.iterrows():
                # Créer un lien cliquable vers la page du film
                st.sidebar.markdown(f"- [{movie['Titre Original']}](Film?id={movie['ID tmdb']})")