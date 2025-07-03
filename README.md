# Outil de Gestion des Données Fournisseurs - Genève Aéroport (GA)

Cette application Streamlit est un prototype fonctionnel pour la gestion des données fournisseurs. Cette version est optimisée pour la performance et l'expérience utilisateur.

## Fonctionnalités Clés ✨

* **Base de Données Robuste**: Utilise **SQLite** pour un stockage de données fiable et performant, adapté à un usage multi-utilisateurs.
* **Interface Unifiée**: Une seule page intuitive pour visualiser, rechercher, ajouter, modifier et supprimer des fournisseurs.
* **Formulaire d'Édition Modal**: L'ajout et la modification se font via une fenêtre modale (`st.dialog`) organisée en onglets pour ne pas surcharger l'utilisateur.
* **Pagination**: Affiche les fournisseurs par pages pour garantir de bonnes performances même avec un grand volume de données.
* **Recherche Instantanée**: Une barre de recherche permet de filtrer rapidement la liste des fournisseurs.
* **Notifications**: Des notifications `toast` confirment les actions de l'utilisateur (création, mise à jour, suppression).

## Architecture Technique 🛠️

* **Framework**: Streamlit
* **Base de données**: SQLite
* **Manipulation de données**: Pandas

## Comment lancer l'application

1.  **Prérequis**: Assurez-vous d'avoir Python 3.8+ installé.

2.  **Fichiers**: Enregistrez `app.py` et `database.py` dans le même dossier.

3.  **Installer les dépendances**:
    ```bash
    pip install streamlit pandas
    ```

4.  **Lancer l'application**:
    ```bash
    streamlit run app.py
    ```
L'application créera automatiquement le fichier de base de données `suppliers.db` au premier lancement.
