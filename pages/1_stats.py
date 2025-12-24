import streamlit as st
import numpy as np
import pandas as pd
from utils.config import apply_compact_layout
from utils.sidebar import render_sidebar

apply_compact_layout()

# Menu de navigation
render_sidebar()

st.title("📊 Statistiques")

n = st.slider("Taille de l'échantillon", 10, 1000, 100)

data = np.random.normal(loc=0, scale=1, size=n)

df = pd.DataFrame(data, columns=["X"])

st.write("Résumé statistique")
st.dataframe(df.describe())

st.line_chart(df)
