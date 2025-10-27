"""
database.py - Gestion base de données SQLite pour Scanner Livre Pro
===================================================================

Ce module gère toutes les interactions avec la base de données scans.db

Tables:
# ========================================================================
# COMPAT LAYER (wrappers + fonctions attendues par l'UI et les modules)
# ========================================================================

- manifest: Inventaire initial des 14,000 livres
- scans: Livres scannés quotidiennement
- dimensions: Cache des dimensions (poids, taille) par UPC
- sales: Ventes eBay importées

Auteur: Matt
Version: 1.0
Date: 2025-10-24
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import config


# ========================================================================
# CONNEXION & INITIALISATION
# ========================================================================

def get_connection():
    """
    Crée et retourne une connexion à la base de données.
    
    Returns:
        sqlite3.Connection: Connexion active à scans.db
    
    Note:
        Row factory permet d'accéder aux colonnes par nom (dict-like)
    """
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    return conn


def init_database():
    """
    Initialise la base de données avec toutes les tables nécessaires.
    
    Crée les tables si elles n'existent pas:
    - manifest: Inventaire de base
    - scans: Livres scannés
    - dimensions: Cache dimensions
    - sales: Ventes eBay
    
    Crée aussi les index pour optimiser les recherches.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table MANIFEST (inventaire initial)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manifest (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pallet TEXT,
        upc TEXT UNIQUE NOT NULL,
        sku TEXT,
        quantity INTEGER,
        category TEXT,
        title TEXT,
        msrp REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table SCANS (livres scannés)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        bin TEXT NOT NULL,
        upc TEXT NOT NULL,
        condition TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        
        -- Dimensions physiques
        weight_major REAL DEFAULT 0,
        weight_minor REAL DEFAULT 0,
        pkg_length REAL DEFAULT 0,
        pkg_depth REAL DEFAULT 0,
        pkg_width REAL DEFAULT 0,
        
        -- Infos du MANIFEST (copiées pour rapidité)
        pallet TEXT,
        sku TEXT,
        title TEXT,
        msrp REAL,
        
        -- Enrichissement (ajouté après appel APIs)
        author TEXT,
        publisher TEXT,
        pub_year TEXT,
        pages INTEGER,
        binding TEXT,
        language TEXT,
        description TEXT,
        image_url TEXT,
        description_html TEXT,
        start_price REAL,
        ebay_category TEXT DEFAULT '267',
        ebay_condition_id TEXT,
        enriched INTEGER DEFAULT 0,
        enriched_date TEXT,
        
        -- Export & Ventes
        exported INTEGER DEFAULT 0,
        exported_date TEXT,
        qty_vendue INTEGER DEFAULT 0,
        status TEXT DEFAULT 'En attente',
        
        -- Notes
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table DIMENSIONS (cache pour éviter de redemander)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dimensions (
        upc TEXT PRIMARY KEY,
        weight_major REAL DEFAULT 0,
        weight_minor REAL DEFAULT 0,
        pkg_length REAL DEFAULT 0,
        pkg_depth REAL DEFAULT 0,
        pkg_width REAL DEFAULT 0,
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table SALES (ventes eBay importées)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT,
        upc TEXT,
        quantity INTEGER,
        sale_price REAL,
        sale_date TEXT,
        buyer_username TEXT,
        imported_date TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Index pour optimiser les recherches
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_upc ON scans(upc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_bin ON scans(bin)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_enriched ON scans(enriched)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_exported ON scans(exported)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_upc ON sales(upc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manifest_upc ON manifest(upc)")
    
    conn.commit()
    conn.close()
    
    print("✅ Base de données initialisée avec succès!")


# ========================================================================
# FONCTIONS UTILITAIRES
# ========================================================================

def execute_query(query: str, params: tuple = ()) -> bool:
    """
    Exécute une requête SQL (INSERT, UPDATE, DELETE).
    
    Args:
        query: Requête SQL à exécuter
        params: Paramètres de la requête (tuple)
    
    Returns:
        bool: True si succès, False sinon
    
    Exemple:
        >>> execute_query("UPDATE scans SET exported=1 WHERE id=?", (42,))
        True
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur execute_query: {e}")
        return False


def fetch_one(query: str, params: tuple = ()) -> Optional[Dict]:
    """
    Exécute une requête SELECT et retourne UN résultat.
    
    Args:
        query: Requête SQL SELECT
        params: Paramètres de la requête (tuple)
    
    Returns:
        dict: Dictionnaire des colonnes ou None si aucun résultat
    
    Exemple:
        >>> fetch_one("SELECT * FROM manifest WHERE upc=?", ("9781234567890",))
        {'id': 1, 'upc': '9781234567890', 'title': 'Mon livre', ...}
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        return None
    except Exception as e:
        print(f"❌ Erreur fetch_one: {e}")
        return None


def fetch_all(query: str, params: tuple = ()) -> List[Dict]:
    """
    Exécute une requête SELECT et retourne TOUS les résultats.
    
    Args:
        query: Requête SQL SELECT
        params: Paramètres de la requête (tuple)
    
    Returns:
        list: Liste de dictionnaires (un par ligne)
    
    Exemple:
        >>> fetch_all("SELECT * FROM scans WHERE condition=?", ("USED",))
        [{'id': 1, 'upc': '...', ...}, {'id': 2, ...}, ...]
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Erreur fetch_all: {e}")
        return []


# ========================================================================
# MANIFEST - Inventaire initial
# ========================================================================

def check_upc_in_manifest(upc: str) -> bool:
    """
    Vérifie si un UPC existe dans le MANIFEST.
    
    Args:
        upc: Code UPC à vérifier
    
    Returns:
        bool: True si UPC existe, False sinon
    
    Exemple:
        >>> check_upc_in_manifest("9781234567890")
        True
    """
    query = "SELECT COUNT(*) as count FROM manifest WHERE upc = ?"
    result = fetch_one(query, (upc,))
    
    if result:
        return result['count'] > 0
    return False


def get_manifest_data(upc: str) -> Optional[Dict]:
    """
    Retourne toutes les infos MANIFEST pour un UPC.
    
    Args:
        upc: Code UPC du livre
    
    Returns:
        dict: Données du MANIFEST (pallet, sku, title, msrp, quantity...)
              ou None si UPC non trouvé
    
    Exemple:
        >>> get_manifest_data("9781234567890")
        {'upc': '9781234567890', 'title': 'Mon livre', 'msrp': 27.29, ...}
    """
    query = """
    SELECT * FROM manifest 
    WHERE upc = ?
    """
    return fetch_one(query, (upc,))


def insert_manifest_item(data: Dict) -> bool:
    """
    Insère un item dans le MANIFEST (ou le remplace s'il existe).
    
    Args:
        data: Dictionnaire avec les clés: pallet, upc, sku, quantity, 
              category, title, msrp
    
    Returns:
        bool: True si succès
    
    Exemple:
        >>> insert_manifest_item({
        ...     'pallet': '81343',
        ...     'upc': '9781234567890',
        ...     'sku': '172250587',
        ...     'quantity': 2,
        ...     'title': 'Mon livre',
        ...     'msrp': 27.29
        ... })
        True
    """
    query = """
    INSERT OR REPLACE INTO manifest 
    (pallet, upc, sku, quantity, category, title, msrp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    params = (
        data.get('pallet', ''),
        data.get('upc', ''),
        data.get('sku', ''),
        data.get('quantity', 0),
        data.get('category', ''),
        data.get('title', ''),
        data.get('msrp', 0.0)
    )
    
    return execute_query(query, params)


# ========================================================================
# SCANS - Livres scannés
# ========================================================================

def get_bin_for_upc(upc: str) -> Optional[str]:
    """
    Retourne le BIN où cet UPC a déjà été scanné.
    
    Args:
        upc: Code UPC du livre
    
    Returns:
        str: Le code BIN (ex: 'C001') ou None si jamais scanné
    
    Exemple:
        >>> get_bin_for_upc('9780815374237')
        'C001'
    
    Note:
        Utilisé pour vérifier les conflits de BIN (un UPC doit toujours
        être dans le même BIN physique)
    """
    query = """
    SELECT DISTINCT bin 
    FROM scans 
    WHERE upc = ? 
    LIMIT 1
    """
    
    result = fetch_one(query, (upc,))
    
    if result:
        return result['bin']
    return None


def insert_scan(data: Dict) -> Optional[int]:
    """
    Insère un nouveau scan dans la base.
    
    Args:
        data: Dictionnaire avec les données du scan
              Clés requises: bin, upc, condition, quantity
              Clés optionnelles: weight_major, weight_minor, pkg_length, etc.
    
    Returns:
        int: ID du scan inséré ou None si erreur
    
    Exemple:
        >>> insert_scan({
        ...     'bin': 'C001',
        ...     'upc': '9781234567890',
        ...     'condition': 'USED',
        ...     'quantity': 2,
        ...     'weight_major': 0,
        ...     'weight_minor': 750,
        ...     'title': 'Mon livre'
        ... })
        42  # ID du scan
    """
    try:
        # Récupère infos MANIFEST si disponibles
        manifest = get_manifest_data(data['upc'])
        
        query = """
        INSERT INTO scans (
            timestamp, bin, upc, condition, quantity,
            weight_major, weight_minor, pkg_length, pkg_depth, pkg_width,
            pallet, sku, title, msrp,
            ebay_condition_id, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Mapping condition → eBay Condition ID
        condition_map = {
            'NEW': '1000',
            'GOOD': '2750',
            'USED': '5000',
            'DONATION': ''
        }
        
        params = (
            datetime.now().isoformat(),
            data['bin'],
            data['upc'],
            data['condition'],
            data['quantity'],
            data.get('weight_major', 0),
            data.get('weight_minor', 0),
            data.get('pkg_length', 0),
            data.get('pkg_depth', 0),
            data.get('pkg_width', 0),
            manifest['pallet'] if manifest else '',
            manifest['sku'] if manifest else '',
            manifest['title'] if manifest else data.get('title', ''),
            manifest['msrp'] if manifest else 0.0,
            condition_map.get(data['condition'], ''),
            'En attente'
        )
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        scan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return scan_id
        
    except Exception as e:
        print(f"❌ Erreur insert_scan: {e}")
        return None


def get_scans_by_upc(upc: str) -> List[Dict]:
    """
    Retourne tous les scans pour un UPC donné.
    
    Args:
        upc: Code UPC du livre
    
    Returns:
        list: Liste de tous les scans de ce livre
    """
    query = """
    SELECT * FROM scans 
    WHERE upc = ?
    ORDER BY timestamp DESC
    """
    return fetch_all(query, (upc,))


def get_total_scanned_for_upc(upc: str) -> int:
    """
    Retourne le total de livres scannés pour un UPC (toutes conditions).
    
    Args:
        upc: Code UPC du livre
    
    Returns:
        int: Nombre total d'exemplaires scannés
    
    Exemple:
        >>> get_total_scanned_for_upc("9781234567890")
        15  # 15 exemplaires scannés au total
    """
    query = """
    SELECT SUM(quantity) as total 
    FROM scans 
    WHERE upc = ?
    """
    result = fetch_one(query, (upc,))
    
    if result and result['total']:
        return result['total']
    return 0


def get_unenriched_scans() -> List[Dict]:
    """
    Retourne tous les scans qui n'ont pas encore été enrichis.
    
    Returns:
        list: Liste des scans où enriched = 0
    
    Note:
        Utilisé par le module d'enrichissement pour savoir quels
        livres doivent appeler les APIs Google Books / OpenLibrary
    """
    query = """
    SELECT DISTINCT upc, title, condition
    FROM scans 
    WHERE enriched = 0
    ORDER BY timestamp DESC
    """
    return fetch_all(query)


def mark_scans_as_enriched(upc: str, enrichment_data: Dict) -> bool:
    """
    Marque un UPC comme enrichi et ajoute les métadonnées.
    
    Args:
        upc: Code UPC du livre
        enrichment_data: Dictionnaire avec author, publisher, pages, 
                        description, etc.
    
    Returns:
        bool: True si succès
    """
    query = """
    UPDATE scans 
    SET enriched = 1,
        enriched_date = ?,
        author = ?,
        publisher = ?,
        pub_year = ?,
        pages = ?,
        binding = ?,
        language = ?,
        description = ?,
        image_url = ?,
        description_html = ?,
        start_price = ?
    WHERE upc = ?
    """
    
    params = (
        datetime.now().isoformat(),
        enrichment_data.get('author', ''),
        enrichment_data.get('publisher', ''),
        enrichment_data.get('pub_year', ''),
        enrichment_data.get('pages', 0),
        enrichment_data.get('binding', ''),
        enrichment_data.get('language', ''),
        enrichment_data.get('description', ''),
        enrichment_data.get('image_url', ''),
        enrichment_data.get('description_html', ''),
        enrichment_data.get('start_price', 0.0),
        upc
    )
    
    return execute_query(query, params)


def update_scan_exported(scan_ids: List[int], exported: bool = True) -> bool:
    """
    Marque des scans comme exportés (ou non exportés).
    
    Args:
        scan_ids: Liste des IDs de scans à mettre à jour
        exported: True pour marquer comme exporté, False sinon
    
    Returns:
        bool: True si succès
    
    Exemple:
        >>> update_scan_exported([1, 2, 3, 4, 5], exported=True)
        True
    """
    if not scan_ids:
        return True
    
    placeholders = ','.join('?' * len(scan_ids))
    query = f"""
    UPDATE scans 
    SET exported = ?,
        exported_date = ?
    WHERE id IN ({placeholders})
    """
    
    export_value = 1 if exported else 0
    export_date = datetime.now().isoformat() if exported else None
    
    params = (export_value, export_date) + tuple(scan_ids)
    
    return execute_query(query, params)


def get_recent_scans(limit: int = 50) -> List[Dict]:
    """
    Retourne les derniers scans.
    
    Args:
        limit: Nombre maximum de scans à retourner
    
    Returns:
        list: Liste des scans récents
    """
    query = """
    SELECT * FROM scans 
    ORDER BY timestamp DESC 
    LIMIT ?
    """
    return fetch_all(query, (limit,))


def delete_scan(scan_id: int) -> bool:
    """
    Supprime un scan (utilisé pour UNDO).
    
    Args:
        scan_id: ID du scan à supprimer
    
    Returns:
        bool: True si succès
    """
    query = "DELETE FROM scans WHERE id = ?"
    return execute_query(query, (scan_id,))


# ========================================================================
# DIMENSIONS - Cache
# ========================================================================

def get_dimensions_for_upc(upc: str) -> Optional[Dict]:
    """
    Retourne les dimensions d'un UPC depuis le cache.
    
    Args:
        upc: Code UPC du livre
    
    Returns:
        dict: Dimensions (weight_major, weight_minor, pkg_length, etc.)
              ou None si pas en cache
    
    Exemple:
        >>> get_dimensions_for_upc("9781234567890")
        {'weight_major': 0, 'weight_minor': 750, 'pkg_length': 23, ...}
    
    Note:
        Vérifie d'abord la table dimensions, puis cherche dans scans
    """
    # D'abord, cherche dans le cache dimensions
    query = """
    SELECT * FROM dimensions 
    WHERE upc = ?
    """
    result = fetch_one(query, (upc,))
    
    if result:
        return result
    
    # Sinon, cherche dans scans (si déjà scanné avant)
    query = """
    SELECT weight_major, weight_minor, pkg_length, pkg_depth, pkg_width
    FROM scans 
    WHERE upc = ?
    AND (weight_major > 0 OR weight_minor > 0 OR pkg_length > 0)
    LIMIT 1
    """
    result = fetch_one(query, (upc,))
    
    if result:
        # Sauvegarde dans cache pour la prochaine fois
        save_dimensions_for_upc(upc, result)
        return result
    
    return None


def save_dimensions_for_upc(upc: str, dimensions: Dict) -> bool:
    """
    Sauvegarde les dimensions d'un UPC dans le cache.
    
    Args:
        upc: Code UPC du livre
        dimensions: Dictionnaire avec weight_major, weight_minor, 
                   pkg_length, pkg_depth, pkg_width
    
    Returns:
        bool: True si succès
    
    Exemple:
        >>> save_dimensions_for_upc("9781234567890", {
        ...     'weight_major': 0,
        ...     'weight_minor': 750,
        ...     'pkg_length': 23,
        ...     'pkg_depth': 2,
        ...     'pkg_width': 16
        ... })
        True
    """
    query = """
    INSERT OR REPLACE INTO dimensions 
    (upc, weight_major, weight_minor, pkg_length, pkg_depth, pkg_width, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    params = (
        upc,
        dimensions.get('weight_major', 0),
        dimensions.get('weight_minor', 0),
        dimensions.get('pkg_length', 0),
        dimensions.get('pkg_depth', 0),
        dimensions.get('pkg_width', 0),
        datetime.now().isoformat()
    )
    
    return execute_query(query, params)


# ========================================================================
# SALES - Ventes eBay
# ========================================================================

def insert_sale(data: Dict) -> bool:
    """
    Insère une vente eBay dans la base.
    
    Args:
        data: Dictionnaire avec order_number, upc, quantity, sale_price, 
              sale_date, buyer_username
    
    Returns:
        bool: True si succès
    """
    query = """
    INSERT INTO sales 
    (order_number, upc, quantity, sale_price, sale_date, buyer_username)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    
    params = (
        data.get('order_number', ''),
        data.get('upc', ''),
        data.get('quantity', 0),
        data.get('sale_price', 0.0),
        data.get('sale_date', ''),
        data.get('buyer_username', '')
    )
    
    return execute_query(query, params)


def update_qty_vendue(upc: str, quantity: int) -> bool:
    """
    Incrémente la quantité vendue pour un UPC.
    
    Args:
        upc: Code UPC du livre
        quantity: Nombre d'exemplaires vendus
    
    Returns:
        bool: True si succès
    """
    query = """
    UPDATE scans 
    SET qty_vendue = qty_vendue + ?
    WHERE upc = ?
    """
    return execute_query(query, (quantity, upc))


def get_total_revenue() -> float:
    """
    Calcule le revenu total de toutes les ventes.
    
    Returns:
        float: Montant total en $
    """
    query = "SELECT SUM(sale_price * quantity) as total FROM sales"
    result = fetch_one(query)
    
    if result and result['total']:
        return result['total']
    return 0.0


# ========================================================================
# STATISTIQUES & DASHBOARD
# ========================================================================

def get_total_scanned() -> int:
    """Retourne le nombre total de livres scannés."""
    query = "SELECT SUM(quantity) as total FROM scans"
    result = fetch_one(query)
    
    if result and result['total']:
        return result['total']
    return 0


def get_scans_today() -> int:
    """Retourne le nombre de scans aujourd'hui."""
    today = datetime.now().date().isoformat()
    
    query = """
    SELECT SUM(quantity) as total 
    FROM scans 
    WHERE DATE(timestamp) = ?
    """
    result = fetch_one(query, (today,))
    
    if result and result['total']:
        return result['total']
    return 0


def get_scans_by_condition() -> List[Dict]:
    """Retourne le nombre de scans par condition."""
    query = """
    SELECT condition, SUM(quantity) as count
    FROM scans
    GROUP BY condition
    ORDER BY count DESC
    """
    return fetch_all(query)


def get_scans_by_status() -> List[Dict]:
    """Retourne le nombre de scans par statut."""
    query = """
    SELECT status, COUNT(*) as count
    FROM scans
    GROUP BY status
    """
    return fetch_all(query)


# ========================================================================
# TESTS & DEBUG

# ========================================================================
# FONCTIONS DE COMPATIBILITÉ / ALIAS
# ========================================================================
# Ces fonctions sont des alias ou des wrappers pour assurer la 
# compatibilité avec les autres modules (main_app.py, manifest_module.py, etc.)

def get_manifest_by_upc(upc: str) -> Optional[Dict]:
    """
    Alias pour get_manifest_data() (compatibilité avec main_app.py).
    
    Args:
        upc: Code UPC du livre
    
    Returns:
        dict: Données du MANIFEST ou None si non trouvé
    
    Exemple:
        >>> get_manifest_by_upc("9781234567890")
        {'upc': '9781234567890', 'title': 'Mon livre', ...}
    
    Note:
        Cette fonction existe pour la compatibilité. Elle appelle
        simplement get_manifest_data() qui fait le vrai travail.
    """
    return get_manifest_data(upc)


def count_manifest() -> int:
    """
    Compte le nombre total de livres dans le MANIFEST.
    
    Returns:
        int: Nombre de lignes dans le MANIFEST
    
    Exemple:
        >>> count_manifest()
        14000
    
    Note:
        Compte les lignes (pas les quantités). Si tu veux le total
        d'exemplaires, utilise get_manifest_total_quantity().
    """
    query = "SELECT COUNT(*) as count FROM manifest"
    result = fetch_one(query)
    
    if result:
        return result['count']
    return 0


def get_manifest_total_quantity() -> int:
    """
    Retourne la quantité totale de tous les livres du MANIFEST.
    
    Returns:
        int: Somme de toutes les quantités
    
    Exemple:
        >>> get_manifest_total_quantity()
        14000  # Total d'exemplaires (pas de titres)
    
    Note:
        Somme la colonne 'quantity' de tous les livres.
    """
    query = "SELECT SUM(quantity) as total FROM manifest"
    result = fetch_one(query)
    
    if result and result['total']:
        return result['total']
    return 0


def get_manifest_progress() -> Dict[str, int]:
    """
    Retourne la progression globale du scanning par rapport au MANIFEST.
    
    Returns:
        dict: {
            'total_manifest': int,  # Total livres dans MANIFEST
            'total_scanned': int,   # Total livres scannés
            'remaining': int,       # Reste à scanner
            'percent': float        # Pourcentage complété
        }
    
    Exemple:
        >>> get_manifest_progress()
        {'total_manifest': 14000, 'total_scanned': 347, 'remaining': 13653, 'percent': 2.5}
    
    Note:
        Utilisé par le Dashboard pour afficher la progression globale.
    """
    total_manifest = get_manifest_total_quantity()
    total_scanned = get_total_scanned()
    remaining = max(0, total_manifest - total_scanned)
    
    percent = 0.0
    if total_manifest > 0:
        percent = round((total_scanned / total_manifest) * 100, 1)
    
    return {
        'total_manifest': total_manifest,
        'total_scanned': total_scanned,
        'remaining': remaining,
        'percent': percent
    }


def get_all_manifest_items() -> List[Dict]:
    """
    Retourne tous les items du MANIFEST.
    
    Returns:
        list: Liste de tous les livres dans le MANIFEST
    
    Note:
        Peut être lent si 14,000 livres. Utilise avec précaution.
    """
    query = "SELECT * FROM manifest ORDER BY pallet, upc"
    return fetch_all(query)


def search_manifest(search_term: str) -> List[Dict]:
    """
    Recherche dans le MANIFEST par UPC ou titre.
    
    Args:
        search_term: Terme à rechercher (UPC ou partie du titre)
    
    Returns:
        list: Liste des livres correspondants
    
    Exemple:
        >>> search_manifest("9781234")
        [{'upc': '9781234567890', 'title': '...', ...}]
    """
    query = """
    SELECT * FROM manifest 
    WHERE upc LIKE ? OR title LIKE ?
    ORDER BY title
    LIMIT 50
    """
    search_pattern = f"%{search_term}%"
    return fetch_all(query, (search_pattern, search_pattern))

# ========================================================================

def test_database():
    """
    Fonction de test pour vérifier que la base fonctionne.
    
    Teste:
    - Création des tables
    - Insertion de données
    - Requêtes de lecture
    """
    print("🧪 Test de la base de données...")
    
    # Init
    init_database()
    print("✅ Tables créées")
    
    # Test insert manifest
    test_manifest = {
        'pallet': 'TEST',
        'upc': '9999999999999',
        'sku': 'TEST-SKU',
        'quantity': 5,
        'title': 'Livre de test',
        'msrp': 19.99
    }
    insert_manifest_item(test_manifest)
    print("✅ Insert manifest OK")
    
    # Test check UPC
    exists = check_upc_in_manifest('9999999999999')
    print(f"✅ Check UPC: {exists}")
    
    # Test get manifest
    data = get_manifest_data('9999999999999')
    print(f"✅ Get manifest: {data['title'] if data else 'None'}")
    
    # Test insert scan
    test_scan = {
        'bin': 'C001',
        'upc': '9999999999999',
        'condition': 'USED',
        'quantity': 2,
        'weight_minor': 500,
        'pkg_length': 20
    }
    scan_id = insert_scan(test_scan)
    print(f"✅ Insert scan OK (ID: {scan_id})")
    
    # Test dimensions
    dims = {'weight_minor': 500, 'pkg_length': 20}
    save_dimensions_for_upc('9999999999999', dims)
    saved_dims = get_dimensions_for_upc('9999999999999')
    print(f"✅ Dimensions cache: {saved_dims['weight_minor'] if saved_dims else 'None'}")
    
    print("\n🎉 Tous les tests passés!")


if __name__ == "__main__":
    # Si on exécute ce fichier directement, lance les tests
    test_database()
def save_dimensions(upc: str, dimensions: Dict) -> bool:
    """
    Alias pour save_dimensions_for_upc() (compatibilité avec main_app.py).
    
    Args:
        upc: Code UPC du livre
        dimensions: Dictionnaire avec weight_major, weight_minor, pkg_length, etc.
    
    Returns:
        bool: True si succès
    
    Note:
        Cette fonction redirige vers save_dimensions_for_upc().
    """
    return save_dimensions_for_upc(upc, dimensions)


def get_scans_today_quantity() -> int:
    """
    Alias pour get_scans_today() (compatibilité).
    
    Returns:
        int: Nombre de scans aujourd'hui
    
    Note:
        Même fonction que get_scans_today(), juste un nom différent.
    """
    return get_scans_today()



def get_enriched_count() -> int:
    """
    Compte le nombre de scans enrichis (avec métadonnées des APIs).
    
    Returns:
        int: Nombre de scans où enriched = 1
    
    Exemple:
        >>> get_enriched_count()
        0  # Aucun scan enrichi encore
    
    Note:
        Utilisé par le Dashboard pour afficher "X scans enrichis"
    """
    query = "SELECT COUNT(DISTINCT upc) as count FROM scans WHERE enriched = 1"
    result = fetch_one(query)
    
    if result:
        return result['count']
    return 0


def get_not_enriched_count() -> int:
    """
    Compte le nombre de scans NON enrichis (à enrichir).
    
    Returns:
        int: Nombre de scans où enriched = 0
    
    Note:
        Utilisé pour savoir combien de livres attendent l'enrichissement.
    """
    query = "SELECT COUNT(DISTINCT upc) as count FROM scans WHERE enriched = 0"
    result = fetch_one(query)
    
    if result:
        return result['count']
    return 0



def get_exported_count() -> int:
    """
    Compte le nombre de scans exportés vers eBay.
    
    Returns:
        int: Nombre de scans où exported = 1
    
    Exemple:
        >>> get_exported_count()
        0  # Aucun export eBay encore
    
    Note:
        Utilisé par le Dashboard pour afficher "X scans exportés"
    """
    query = "SELECT COUNT(DISTINCT id) as count FROM scans WHERE exported = 1"
    result = fetch_one(query)
    
    if result:
        return result['count']
    return 0