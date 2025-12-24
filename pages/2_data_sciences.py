import streamlit as st
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from utils.config import apply_compact_layout
from utils.sidebar import render_sidebar

apply_compact_layout()

# Menu de navigation
render_sidebar()

st.title("📈 Data Science")

# Protection de la suite de la page par login
if not st.session_state.get("logged_in", False):
    st.warning("Veuillez vous connecter")
    st.stop()
    

iris = load_iris(as_frame=True)
df = iris.frame

st.dataframe(df.head())

X = df.drop(columns="target")
y = df["target"]

model = RandomForestClassifier()
model.fit(X, y)

st.write("Importance des variables")
st.bar_chart(model.feature_importances_)



