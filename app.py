import streamlit as st

st.set_page_config(
    page_title="Gestion Fournisseurs GA",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ Outil de Gestion des Données Fournisseurs")

st.markdown("""
Bienvenue sur l'outil de gestion des données fournisseurs de Genève Aéroport.

[cite_start]Cet outil a pour but de centraliser les informations non financières des fournisseurs et prospects afin d'améliorer l'efficacité du suivi[cite: 14, 25].

**👈 Utilisez le menu de navigation sur la gauche pour accéder aux différentes sections:**

- **Entrée des données:** Pour créer ou mettre à jour une fiche fournisseur/prospect.
- **Visualisation et Recherche:** Pour consulter, filtrer et analyser la base de données fournisseurs.

*Cette application est une version de démonstration basée sur le cahier des charges et les cas d'usage fournis.*
""")
