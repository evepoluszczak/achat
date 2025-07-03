import sqlite3
import pandas as pd

DB_FILE = "suppliers.db"

def get_db_connection():
    """Crée et retourne une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données et crée la table si elle n'existe pas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raison_sociale TEXT NOT NULL,
        id_oracle TEXT,
        est_prospect BOOLEAN,
        adresse TEXT,
        pays_canton TEXT,
        contacts TEXT,
        tags TEXT,
        statut_audit TEXT,
        commentaires TEXT,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        derniere_modif TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def add_supplier(data):
    """Ajoute un nouveau fournisseur à la base de données."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO suppliers (raison_sociale, id_oracle, est_prospect, adresse, pays_canton, contacts, tags, statut_audit, commentaires, derniere_modif)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (data['raison_sociale'], data['id_oracle'], data['est_prospect'], data['adresse'], data['pays_canton'], data['contacts'], ','.join(data['tags']), data['statut_audit'], data['commentaires']))
    conn.commit()
    conn.close()

def update_supplier(supplier_id, data):
    """Met à jour un fournisseur existant."""
    conn = get_db_connection()
    conn.execute("""
        UPDATE suppliers
        SET raison_sociale = ?, id_oracle = ?, est_prospect = ?, adresse = ?, pays_canton = ?, contacts = ?, tags = ?, statut_audit = ?, commentaires = ?, derniere_modif = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (data['raison_sociale'], data['id_oracle'], data['est_prospect'], data['adresse'], data['pays_canton'], data['contacts'], ','.join(data['tags']), data['statut_audit'], data['commentaires'], supplier_id))
    conn.commit()
    conn.close()

def get_supplier_by_id(supplier_id):
    """Récupère un fournisseur par son ID."""
    conn = get_db_connection()
    supplier = conn.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,)).fetchone()
    conn.close()
    return dict(supplier) if supplier else None

def get_suppliers(limit, offset, search_term=None, sort_by='raison_sociale', ascending=True):
    """Récupère une liste paginée et triée de fournisseurs."""
    conn = get_db_connection()
    query = "SELECT * FROM suppliers"
    count_query = "SELECT COUNT(id) FROM suppliers"
    params = []

    if search_term:
        query += " WHERE raison_sociale LIKE ?"
        count_query += " WHERE raison_sociale LIKE ?"
        params.append(f'%{search_term}%')
    
    order = "ASC" if ascending else "DESC"
    query += f" ORDER BY {sort_by} {order}"
    
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    df = pd.read_sql_query(query, conn, params=params)
    total_records = conn.execute(count_query, params[:-2]).fetchone()[0]

    conn.close()
    return df, total_records

def delete_supplier(supplier_id):
    """Supprime un fournisseur."""
    conn = get_db_connection()
    conn.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
    conn.commit()
    conn.close()

def get_suppliers_prefill_data():
    """Récupère un dictionnaire de données pour le pré-remplissage du formulaire."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT raison_sociale, id_oracle, adresse FROM suppliers", conn)
    conn.close()
    
    prefill_data = {}
    for _, row in df.iterrows():
        prefill_data[row['raison_sociale']] = {
            'id_oracle': row['id_oracle'],
            'adresse': row['adresse']
        }
    return prefill_data

# Remplacez la fonction upsert_suppliers_from_df par les deux fonctions suivantes
# dans votre fichier database.py.

def analyze_import_data(df):
    """
    Analyse un DataFrame importé et le compare à la base de données.
    Retourne des listes de nouveaux fournisseurs, de fournisseurs à mettre à jour,
    et de conflits potentiels.
    """
    conn = get_db_connection()
    existing_suppliers_df = pd.read_sql_query("SELECT id, raison_sociale, id_oracle, adresse FROM suppliers", conn)
    conn.close()

    new_suppliers = []
    conflicts = []

    # Convertir le DataFrame existant en dictionnaire pour un accès rapide
    existing_map = existing_suppliers_df.set_index('raison_sociale').to_dict('index')

    for _, row in df.iterrows():
        name = row['Raison Sociale']
        new_data = {
            'raison_sociale': name,
            'id_oracle': str(row['Numéro de fournisseur']) if pd.notna(row['Numéro de fournisseur']) else '',
            'adresse': str(row['Adresse']) if pd.notna(row['Adresse']) else ''
        }

        if name in existing_map:
            # Le fournisseur existe, on vérifie les conflits
            old_data = existing_map[name]
            id_changed = new_data['id_oracle'] != str(old_data['id_oracle'])
            address_changed = new_data['adresse'] != str(old_data['adresse'])

            if id_changed or address_changed:
                conflict_details = {
                    'raison_sociale': name,
                    'old_id': old_data['id_oracle'],
                    'new_id': new_data['id_oracle'],
                    'old_adresse': old_data['adresse'],
                    'new_adresse': new_data['adresse'],
                }
                conflicts.append(conflict_details)
        else:
            # Nouveau fournisseur
            new_suppliers.append(new_data)
            
    return new_suppliers, conflicts

def execute_import(new_suppliers, approved_conflicts):
    """Exécute les insertions et les mises à jour validées par l'utilisateur."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insérer les nouveaux fournisseurs
    for supplier in new_suppliers:
        cursor.execute(
            "INSERT INTO suppliers (raison_sociale, id_oracle, adresse, est_prospect) VALUES (?, ?, ?, ?)",
            (supplier['raison_sociale'], supplier['id_oracle'], supplier['adresse'], False)
        )

    # Mettre à jour les fournisseurs avec conflits approuvés
    for conflict in approved_conflicts:
        cursor.execute(
            "UPDATE suppliers SET id_oracle = ?, adresse = ?, derniere_modif = CURRENT_TIMESTAMP WHERE raison_sociale = ?",
            (conflict['new_id'], conflict['new_adresse'], conflict['raison_sociale'])
        )
    
    conn.commit()
    conn.close()
    return len(new_suppliers), len(approved_conflicts)
            
    conn.commit()
    conn.close()
    return inserted_count, updated_count
