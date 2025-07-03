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
    
    # Tri
    order = "ASC" if ascending else "DESC"
    query += f" ORDER BY {sort_by} {order}"
    
    # Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    df = pd.read_sql_query(query, conn, params=params)
    total_records = conn.execute(count_query, params[:-2]).fetchone()[0] # Exclude limit/offset for count

    conn.close()
    return df, total_records

def delete_supplier(supplier_id):
    """Supprime un fournisseur."""
    conn = get_db_connection()
    conn.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
    conn.commit()
    conn.close()

def get_suppliers_map():
    """Récupère un dictionnaire {raison_sociale: id_oracle}."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT raison_sociale, id_oracle FROM suppliers", conn)
    conn.close()
    # Filtre les fournisseurs qui ont un Numéro de fournisseur
    df = df.dropna(subset=['id_oracle'])
    return pd.Series(df.id_oracle.values, index=df.raison_sociale).to_dict()

def upsert_suppliers_from_df(df):
    """
    Met à jour ou insère des fournisseurs depuis un DataFrame.
    Le DataFrame doit contenir les colonnes 'Raison Sociale' et 'Numéro de fournisseur'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    inserted_count = 0

    for _, row in df.iterrows():
        raison_sociale = row['Raison Sociale']
        # Assurer que l'Numéro de fournisseur est traité comme une chaîne de caractères
        id_oracle = str(row['Numéro de fournisseur']) if pd.notna(row['Numéro de fournisseur']) else None


        # Vérifie si le fournisseur existe déjà
        cursor.execute("SELECT id FROM suppliers WHERE raison_sociale = ?", (raison_sociale,))
        result = cursor.fetchone()

        if result:
            # Met à jour l'Numéro de fournisseur s'il existe déjà
            supplier_id = result[0]
            cursor.execute("UPDATE suppliers SET id_oracle = ?, derniere_modif = CURRENT_TIMESTAMP WHERE id = ?", (id_oracle, supplier_id))
            updated_count += 1
        else:
            # Insère le nouveau fournisseur s'il n'existe pas
            cursor.execute("""
                INSERT INTO suppliers (raison_sociale, id_oracle, est_prospect)
                VALUES (?, ?, ?)
            """, (raison_sociale, id_oracle, False))
            inserted_count += 1
            
    conn.commit()
    conn.close()
    return inserted_count, updated_count
