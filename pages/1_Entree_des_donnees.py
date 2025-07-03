import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="Entrée des données", layout="wide")

# --- File Paths ---
DATA_FILE = 'data/suppliers.csv'
UPLOAD_DIR = 'data/uploads'

# --- Utility Functions ---
def init_data_file():
    """Creates the CSV file with headers if it doesn't exist."""
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        df = pd.DataFrame(columns=[
            'id_unique', 'raison_sociale', 'id_oracle', 'est_prospect',
            'adresse', 'pays_canton', 'contacts', 'tags',
            'statut_audit', 'commentaires', 'documents_lies', 'date_creation',
            'derniere_modif'
        ])
        df.to_csv(DATA_FILE, index=False)

def save_uploaded_files(uploaded_files, supplier_id):
    """Saves uploaded files to a supplier-specific folder."""
    if not uploaded_files:
        return []

    supplier_upload_dir = os.path.join(UPLOAD_DIR, str(supplier_id))
    os.makedirs(supplier_upload_dir, exist_ok=True)
    saved_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(supplier_upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_paths.append(file_path)
    return saved_paths

# --- Initialization ---
init_data_file()
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Streamlit Interface ---
st.title("📝 Entrée des données Fournisseurs")
st.markdown("Remplissez le formulaire ci-dessous pour ajouter un nouveau fournisseur ou prospect.")

with st.form("supplier_form", clear_on_submit=True):
    st.subheader("Informations Générales")
    raison_sociale = st.text_input("**Raison Sociale**", help="Nom officiel de l'entreprise.", key="raison_sociale")
    id_oracle = st.text_input("ID Oracle (si connu)", help="L'identifiant du fournisseur dans l'ERP Oracle.")
    est_prospect = st.checkbox("Ceci est un prospect (non présent dans Oracle)")

    st.subheader("Coordonnées")
    adresse = st.text_area("Adresse complète")
    pays_canton = st.selectbox("Pays / Canton",
                               ["Genève", "Vaud", "Valais", "France", "Allemagne", "Italie", "Autre"],
                               help="Permet de générer des statistiques géographiques.")

    st.subheader("Détails et Suivi")
    contacts = st.text_area("Contacts", help="Listez les personnes de contact (Nom, email, téléphone). Un par ligne.")
    tags = st.multiselect("Catégorisation / Tags",
                          ["Fournisseur critique", "Conforme", "Non conforme", "Audit à planifier", "RSE+", "Innovation"],
                          help="Permet un filtrage et une classification rapide.")
    statut_audit = st.selectbox("Statut d'audit",
                                ["Non concerné", "En attente", "Planifié", "Réalisé", "Non-conformité majeure"],
                                help="Suivi de la conformité des fournisseurs.")
    commentaires = st.text_area("Commentaires / Historique des échanges",
                                help="Retours d'expériences, notes de réunions, conditions de paiement négociées, etc.")

    st.subheader("Documents")
    uploaded_files = st.file_uploader("Joindre des documents (audits, offres, contrats...)",
                                        accept_multiple_files=True,
                                        help="Les documents seront stockés et liés à cette fiche fournisseur.")

    submitted = st.form_submit_button("Enregistrer le fournisseur")

if submitted:
    if not raison_sociale:
        st.error("La raison sociale est un champ obligatoire.")
    else:
        try:
            df = pd.read_csv(DATA_FILE)
            
            # Generate a unique ID based on the timestamp
            new_id = f"GA-{int(datetime.now().timestamp())}"

            # Save uploaded files
            document_paths = save_uploaded_files(uploaded_files, new_id)

            new_data = {
                'id_unique': new_id,
                'raison_sociale': raison_sociale,
                'id_oracle': id_oracle if id_oracle else 'N/A',
                'est_prospect': est_prospect,
                'adresse': adresse,
                'pays_canton': pays_canton,
                'contacts': contacts,
                'tags': ', '.join(tags), # Convert list to string
                'statut_audit': statut_audit,
                'commentaires': commentaires,
                'documents_lies': ', '.join(document_paths), # Store paths
                'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'derniere_modif': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Add new data to DataFrame
            new_df = pd.DataFrame([new_data])
            updated_df = pd.concat([df, new_df], ignore_index=True)
            
            # Save the CSV file
            updated_df.to_csv(DATA_FILE, index=False)
            
            st.success(f"Le fournisseur '{raison_sociale}' a été enregistré avec succès avec l'ID: {new_id}")
            st.balloons()
        except Exception as e:
            st.error(f"Une erreur est survenue lors de l'enregistrement : {e}")
