import json
import os
from pathlib import Path

# Chemin du dossier data et du fichier de données
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "transactions.json")

def initialize_data_file():
    """Initialise le fichier de données s'il n'existe pas."""
    # Créer le dossier data s'il n'existe pas
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(DATA_FILE):
        default_data = {
            "lucile_transactions": [],
            "julien_transactions": [],
            "commun_transactions": []
        }
        save_data(default_data)

def load_data():
    """Charge toutes les données depuis le fichier JSON."""
    initialize_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        return {
            "lucile_transactions": [],
            "julien_transactions": [],
            "commun_transactions": []
        }

def save_data(data):
    """Sauvegarde toutes les données dans le fichier JSON."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données: {e}")

def load_transactions(account_name):
    """Charge les transactions d'un compte spécifique."""
    data = load_data()
    return data.get(f"{account_name}_transactions", [])

def save_transactions(account_name, transactions):
    """Sauvegarde les transactions d'un compte spécifique."""
    data = load_data()
    data[f"{account_name}_transactions"] = transactions
    save_data(data)

def add_transaction(account_name, transaction):
    """Ajoute une transaction à un compte et la sauvegarde."""
    transactions = load_transactions(account_name)
    transactions.append(transaction)
    save_transactions(account_name, transactions)
    return transactions

def delete_transaction(account_name, index):
    """Supprime une transaction à un index donné."""
    transactions = load_transactions(account_name)
    if 0 <= index < len(transactions):
        transactions.pop(index)
        save_transactions(account_name, transactions)
    return transactions

def clear_transactions(account_name):
    """Efface toutes les transactions d'un compte."""
    save_transactions(account_name, [])
