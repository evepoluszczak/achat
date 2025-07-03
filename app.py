import streamlit as st
import pandas as pd
import math
import database as db

# --- Configuration de la Page ---
st.set_page_config(layout="wide", page_title="Gestion Fournisseurs GA")

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
""", unsafe_allow_html=True)

# --- Constantes pour les options ---
TAG_OPTIONS = ["Fournisseur critique", "Fournisseur non critique", "Conforme", "Non conforme", "Audit à planifier", "RSE+", "Innovation"]
AUDIT_STATUS_OPTIONS = ["Non concerné", "En attente", "Planifié", "Réalisé", "Non-conformité majeure"]

# --- État de Session ---
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1
if 'import_analysis' not in st.session_state:
    st.session_state.import_analysis = None
if 'user_message' not in st.session_state:
    st.session_state.user_message = None
if 'show_delete_all_confirmation' not in st.session_state:
    st.session_state.show_delete_all_confirmation = False

RECORDS_PER_PAGE = 10

# --- Fonctions de l'UI ---
@st.dialog("Ajouter / Modifier un Fournisseur")
def supplier_form(supplier_id=None):
    if supplier_id:
        supplier_data = db.get_supplier_by_id(supplier_id)
    else:
        supplier_data = {}

    prefill_data = db.get_suppliers_prefill_data()
    supplier_names = [""] + list(prefill_data.keys())

    with st.form("supplier_form"):
        st.write("Pour pré-remplir, choisissez un fournisseur connu :")
        selected_name = st.selectbox("Choisir un fournisseur", options=supplier_names, index=0, label_visibility="collapsed")
        st.markdown("---")
        default_name = selected_name if selected_name else supplier_data.get('raison_sociale', '')
        selected_data = prefill_data.get(selected_name, {})
        default_id_oracle = selected_data.get('id_oracle', supplier_data.get('id_oracle', ''))
        default_adresse = selected_data.get('adresse', supplier_data.get('adresse', ''))

        tab1, tab2 = st.tabs(["Informations Générales", "Contacts & Suivi"])
        with tab1:
            raison_sociale = st.text_input("Raison Sociale", value=default_name)
            id_oracle = st.text_input("Numéro de fournisseur", value=default_id_oracle)
            adresse = st.text_area("Adresse", value=default_adresse)
            pays_canton = st.selectbox("Pays/Canton", ["Genève", "Vaud", "France", "Autre"], index=0)
            est_prospect = st.checkbox("Prospect", value=supplier_data.get('est_prospect', False))
        with tab2:
            contacts = st.text_area("Contacts", value=supplier_data.get('contacts', ''))
            tags = st.multiselect("Tags", options=TAG_OPTIONS, default=supplier_data.get('tags', '').split(',') if supplier_data.get('tags') else [])
            statut_audit = st.selectbox("Statut Audit", options=AUDIT_STATUS_OPTIONS, index=0)
            commentaires = st.text_area("Commentaires", value=supplier_data.get('commentaires', ''))

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            form_data = {"raison_sociale": raison_sociale, "id_oracle": id_oracle, "adresse": adresse, "pays_canton": pays_canton, "est_prospect": est_prospect, "contacts": contacts, "tags": tags, "statut_audit": statut_audit, "commentaires": commentaires}
            if supplier_id:
                db.update_supplier(supplier_id, form_data)
                st.session_state.user_message = {"text": f"Fournisseur '{raison_sociale}' mis à jour.", "icon": "✅"}
            else:
                db.add_supplier(form_data)
                st.session_state.user_message = {"text": f"Fournisseur '{raison_sociale}' ajouté.", "icon": "🎉"}
            st.rerun()

# --- BARRE LATERALE (SIDEBAR) ---
with st.sidebar:
    st.header("Actions")
    st.subheader("Importer une liste")
    uploaded_file = st.file_uploader("Importer un fichier (CSV ou Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file:
        if st.button("Analyser le fichier d'import"):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file).drop_duplicates(subset=['Raison Sociale'])
                else:
                    df = pd.read_excel(uploaded_file).drop_duplicates(subset=['Raison Sociale'])
                
                required_cols = ['Raison Sociale', 'Numéro de fournisseur', 'Adresse']
                if all(col in df.columns for col in required_cols):
                    with st.spinner("Analyse en cours..."):
                        new, conflicts = db.analyze_import_data(df)
                        st.session_state.import_analysis = {'new': new, 'conflicts': conflicts}
                else:
                    st.error(f"Le fichier doit contenir les colonnes : {', '.join(required_cols)}.")
                    st.session_state.import_analysis = None
            except Exception as e:
                st.error(f"Une erreur est survenue lors de l'analyse : {e}")
                st.session_state.import_analysis = None
    
    if st.session_state.import_analysis:
        st.markdown("---")
        st.subheader("Résultat de l'analyse")
        
        analysis = st.session_state.import_analysis
        new_suppliers = analysis['new']
        conflicts = analysis['conflicts']

        st.info(f"**{len(new_suppliers)}** nouveaux fournisseurs seront ajoutés.")
        
        if conflicts:
            st.warning(f"**{len(conflicts)}** fournisseurs existants ont des données différentes.")
            with st.form("conflict_form"):
                col1, col2 = st.columns(2)
                with col1:
                    approve_selected_submitted = st.form_submit_button("Appliquer la sélection")
                with col2:
                    approve_all_submitted = st.form_submit_button("Approuver TOUT", type="primary")

                st.markdown("---")
                approved_conflicts = []
                for i, conflict in enumerate(conflicts):
                    with st.expander(f"{conflict['raison_sociale']} - Données modifiées"):
                        if conflict['id_changed']:
                            st.write(f"**Numéro de fournisseur :** `{conflict['old_id']}` ➡️ `{conflict['new_id']}`")
                        if conflict['address_changed']:
                            st.write(f"**Adresse :** `{conflict['old_adresse']}` ➡️ `{conflict['new_adresse']}`")
                        
                        approve = st.checkbox("Approuver ce changement", key=f"approve_{i}")
                        if approve:
                            approved_conflicts.append(conflict)
                
                if approve_selected_submitted:
                    inserted, updated = db.execute_import(new_suppliers, approved_conflicts)
                    st.session_state.user_message = {"text": f"Importation terminée : {inserted} fournisseurs ajoutés, {updated} mis à jour.", "icon": "✅"}
                    st.session_state.import_analysis = None
                    st.rerun()
                
                if approve_all_submitted:
                    inserted, updated = db.execute_import(new_suppliers, conflicts)
                    st.session_state.user_message = {"text": f"Importation terminée : {inserted} fournisseurs ajoutés, {updated} mis à jour.", "icon": "✅"}
                    st.session_state.import_analysis = None
                    st.rerun()
        else:
            if st.button("Confirmer l'ajout des nouveaux fournisseurs"):
                inserted, _ = db.execute_import(new_suppliers, [])
                st.session_state.user_message = {"text": f"Importation terminée : {inserted} nouveaux fournisseurs ajoutés.", "icon": "✅"}
                st.session_state.import_analysis = None
                st.rerun()

    # --- NOUVEAU : Section pour la suppression de toutes les données ---
    st.markdown("---")
    st.subheader("Actions dangereuses")
    if st.button("Supprimer tous les fournisseurs", type="primary"):
        st.session_state.show_delete_all_confirmation = True

# --- Boîte de dialogue de confirmation de suppression totale ---
if st.session_state.show_delete_all_confirmation:
    @st.dialog("Confirmation de suppression")
    def confirm_delete_all():
        st.warning("Êtes-vous absolument certain de vouloir supprimer TOUS les fournisseurs ?")
        st.write("**Cette action est irréversible.**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Annuler"):
                st.session_state.show_delete_all_confirmation = False
                st.rerun()
        with col2:
            if st.button("Oui, supprimer tout", type="primary"):
                db.delete_all_suppliers()
                st.session_state.user_message = {"text": "Tous les fournisseurs ont été supprimés.", "icon": "🗑️"}
                st.session_state.show_delete_all_confirmation = False
                st.rerun()
    
    confirm_delete_all()

# --- AFFICHAGE PRINCIPAL ---
st.markdown("<h3><i class='bi bi-airplane-fill'></i> Outil de Gestion des Données Fournisseurs</h3>", unsafe_allow_html=True)

if st.session_state.user_message:
    msg = st.session_state.user_message
    st.success(msg['text'], icon=msg['icon'])
    st.session_state.user_message = None

col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input("Rechercher par raison sociale", placeholder="Rechercher...")
with col2:
    st.write("")
    st.write("")
    if st.button("Ajouter un nouveau fournisseur", use_container_width=True):
        supplier_form()
offset = (st.session_state.page_number - 1) * RECORDS_PER_PAGE
suppliers_df, total_records = db.get_suppliers(RECORDS_PER_PAGE, offset, search_term)
total_pages = math.ceil(total_records / RECORDS_PER_PAGE) if total_records > 0 else 1
st.header("Liste des Fournisseurs")
st.write(f"Affichage de {len(suppliers_df)} sur {total_records} fournisseurs.")

if not suppliers_df.empty:
    for index, row in suppliers_df.iterrows():
        expander = st.expander(f"{row['raison_sociale']} (ID: {row['id']})")
        with expander:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Statut Audit:** {row['statut_audit']}")
                st.write(f"**Pays/Canton:** {row['pays_canton']}")
                st.write(f"**Tags:** {row['tags']}")
            with col2:
                st.write(f"**Numéro de fournisseur:** {row['id_oracle']}")
                st.write(f"**Adresse:** {row['adresse']}")
                st.write(f"**Prospect:** {'Oui' if row['est_prospect'] else 'Non'}")
            with col3:
                if st.button("Modifier", key=f"edit_{row['id']}", use_container_width=True):
                    supplier_form(row['id'])
                if st.button("Supprimer", key=f"del_{row['id']}", type="primary", use_container_width=True):
                    db.delete_supplier(row['id'])
                    st.toast(f"Fournisseur '{row['raison_sociale']}' supprimé.", icon="🗑️")
                    st.rerun()
    st.write("")
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    with col_nav1:
        if st.session_state.page_number > 1:
            if st.button("Précédent"):
                st.session_state.page_number -= 1
                st.rerun()
    with col_nav2:
        st.write(f"Page **{st.session_state.page_number}** sur **{total_pages}**")
    with col_nav3:
        if st.session_state.page_number < total_pages:
            if st.button("Suivant", use_container_width=True):
                st.session_state.page_number += 1
                st.rerun()
else:
    st.info("Aucun fournisseur trouvé. Importez une liste ou cliquez sur 'Ajouter un nouveau fournisseur' pour commencer.")
