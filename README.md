# Application de Gestion de Comptes

Application Streamlit pour gérer les comptes personnels et communs.

## 🚀 Fonctionnalités

- **Authentification requise** : Toutes les pages nécessitent une connexion
- **Page d'accueil** : Tableau de bord avec récapitulatif des dépenses mensuelles
- **Compte Lucile** : Gestion des transactions personnelles de Lucile
- **Compte Julien** : Gestion des transactions personnelles de Julien
- **Compte Commun** : Gestion des dépenses communes
- **Page de connexion** : Authentification des utilisateurs

## 📋 Pages

1. **Accueil (app.py)** : Vue d'ensemble avec statistiques globales et récapitulatif mensuel
2. **Compte Lucile** : Tableau de transactions pour Lucile
3. **Compte Julien** : Tableau de transactions pour Julien
4. **Compte Commun** : Tableau de transactions communes
5. **Connexion** : Page de connexion

## 🔐 Authentification

Les utilisateurs doivent être connectés pour accéder aux pages. La connexion peut se faire via :
- La barre latérale (sidebar)
- La page de connexion dédiée

## 🛠️ Installation

```bash
pip install -r requirements.txt
```

## ▶️ Lancement

```bash
streamlit run app.py
```

## 👥 Utilisateurs

Les utilisateurs sont définis dans le fichier `users.json`.

## 📊 Fonctionnalités des pages de comptes

Chaque page de compte (Lucile, Julien, Commun) permet de :
- Ajouter des transactions avec date, description, montant et catégorie
- Visualiser le solde, les revenus et les dépenses
- Consulter l'historique des transactions
- Effacer toutes les transactions

## 🏠 Page d'accueil

La page d'accueil affiche :
- Vue d'ensemble par compte (solde, revenus, dépenses)
- Total global de tous les comptes
- Récapitulatif mensuel des transactions
- Liste des 10 dernières transactions
