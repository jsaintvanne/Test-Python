import json
import os
import streamlit as st

def check_login(username, password):
    users_file = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
        return users.get(username) == password
    return False


def require_login():
    """
    Vérifie si l'utilisateur est connecté. Si non, affiche un message et arrête l'exécution de la page.
    À utiliser au début de chaque page nécessitant une authentification.
    """
    if not st.session_state.get("logged_in", False):
        st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
        st.info("Veuillez vous connecter via la barre latérale ou la page de connexion.")
        st.stop()
    return st.session_state.get("username", "")
