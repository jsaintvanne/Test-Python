@echo off

REM Verifier si l'environnement virtuel existe
if not exist ".venv" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
    echo Environnement virtuel cree avec succes!
    echo.
)

REM Lancer la fenetre de chargement en arriere-plan
start "" /MIN .venv\Scripts\pythonw.exe loading_window.py "Préparation de l'application..."

REM Activer l'environnement
call .venv\Scripts\activate.bat >nul 2>&1

REM Installer les dependances
pip install -r requirements.txt >nul 2>&1

REM Fermer la fenetre de chargement (tuer tous les pythonw.exe)
taskkill /F /IM pythonw.exe >nul 2>&1

REM Lancer Streamlit
streamlit run app.py
