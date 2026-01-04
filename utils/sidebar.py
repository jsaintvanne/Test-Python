import streamlit as st
from utils.auth import check_login


def render_sidebar():
    """Affiche le menu de navigation et le formulaire de connexion dans la barre latérale"""
    with st.sidebar:
        st.header("Navigation")
        st.page_link("app.py", label="🏠 Accueil")
        st.page_link("pages/1_lucile.py", label="💰 Compte Lucile")
        st.page_link("pages/2_julien.py", label="💰 Compte Julien")
        st.page_link("pages/3_commun.py", label="💑 Compte Commun")
        
        st.markdown("---")
        
        # Section authentification
        st.subheader("🔐 Authentification")
        
        logged_in = st.session_state.get("logged_in", False)
        
        if logged_in:
            username = st.session_state.get("username", "Utilisateur")
            st.success(f"✅ Connecté ({username})")
            if st.button("🚪 Déconnexion", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()
        else:
            st.info("Non connecté")
            username = st.text_input("Utilisateur", key="sidebar_username")
            password = st.text_input("Mot de passe", type="password", key="sidebar_password")
            
            if st.button("Se connecter", use_container_width=True):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Connexion réussie")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
