# Test Application Python

## Installation

### Sous Windows 11

🔍 Étape 1 – Vérifier si Python est installé

Dans PowerShell ou Invite de commandes, tape :

python --version


ou

py --version

Résultats possibles

✅ Python 3.x.x → Python est installé

❌ commande inconnue → Python n’est pas installé ou mal configuré

✅ Cas 1 : python ou py fonctionne

Sous Windows, pip s’utilise souvent comme ceci :

Essaie :
python -m pip install streamlit


ou

py -m pip install streamlit


👉 Dans 90 % des cas, ça résout le problème.

❌ Cas 2 : Python n’est pas installé
Installer Python correctement (important ⚠️)

Va sur
👉 https://www.python.org/downloads/windows/

Télécharge Python 3.11 ou 3.12

⚠️ COCHE ABSOLUMENT :

☑ Add Python to PATH


Clique sur Install Now

Ensuite, ferme et rouvre PowerShell, puis :

python --version
python -m pip install streamlit

🧪 Vérifier que Streamlit est installé
python -m streamlit --version


Si tu vois une version → tout est OK 🎉

🚀 Lancer ton app

Place-toi dans ton dossier projet :

cd chemin\vers\ton_projet


Puis :

python -m streamlit run menu.py



### Lancement utilisateur

🧪 2️⃣ Installation automatique (côté utilisateur)

Quelqu’un qui clone ton projet fait simplement :

python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py