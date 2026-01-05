# Configuration centralisée et petits utilitaires d'UI
import streamlit as st


__version__ = "0.1.0"
APP_NAME = "Application de suivi de comptes"
CONTACT_EMAIL = "j.saintvanne@gmail.com"


def apply_compact_layout(top_padding: str = "1rem") -> None:
    """Réduit l'espace vide en haut des pages Streamlit."""
    st.markdown(
        f"""
        <style>
            .block-container {{
                padding-top: {top_padding};
                padding-bottom: 2rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
