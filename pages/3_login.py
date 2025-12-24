import streamlit as st
from utils.auth import check_login
from utils.sidebar import render_sidebar, render_header

# Barre d'en-tête avec statut de connexion
render_header()

# Menu de navigation
render_sidebar()

st.title("🔐 Connexion")

username = st.text_input("Nom d'utilisateur")
password = st.text_input("Mot de passe", type="password")

if st.button("Se connecter"):
    if check_login(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.success("Connexion réussie")
        st.rerun()
    else:
        st.error("Identifiants incorrects")

