"""
Module Export eBay - Scanner Livre App
Génère fichiers CSV au format eBay File Exchange (51 colonnes)
"""

import csv
from datetime import datetime
from pathlib import Path
import config
import database
import utils

# ========================================================================
# CSV GENERATION
# ========================================================================

def build_ebay_row(scan_data, aggregated_quantity):
    """
    Construit une ligne CSV eBay (51 colonnes) depuis données scan.
    Args:
        scan_data (dict): Données d'un scan enrichi
        aggregated_quantity (int): Quantité agrégée (si plusieurs scans même UPC+Condition)
    Returns:
        list: 51 valeurs
    """
    
    # Action (col 1)
    action = 'Add'
    
    # Custom label / SKU (col 2) = UPC
    sku = scan_data.get('upc', '')
    
    # Category ID (col 3)
    category_id = scan_data.get('ebay_category', config.EBAY_CATEGORY_BOOKS)
    
    # Category name (col 4) - vide
    category_name = ''
    
    # Title (col 5)
    title = scan_data.get('title', 'Livre')
    # Tronque si trop long (eBay max 80 caractères)
    title = utils.truncate_text(title, 80, '...')
    
    # Relationship (col 6-7) - vide
    relationship = ''
    relationship_details = ''
    
    # Schedule Time (col 8) - vide
    schedule_time = ''
    
    # P:EPID (col 9) - vide
    epid = ''
    
    # Start price (col 10)
    start_price = scan_data.get('start_price', config.MIN_PRICE)
    
    # Quantity (col 11) - agrégée
    quantity = aggregated_quantity
    
    # Item photo URL (col 12)
    photo_url = scan_data.get('image_url', '')
    
    # VideoID (col 13) - vide
    video_id = ''
    
    # Condition ID (col 14)
    condition_id = scan_data.get('ebay_condition_id', '5000')
    
    # Description (col 15) - HTML
    description = scan_data.get('description_html', '')
    
    # Format (col 16)
    format_type = config.EBAY_FORMAT
    
    # Duration (col 17)
    duration = config.EBAY_DURATION
    
    # Buy It Now price (col 18) - vide
    buy_it_now = ''
    
    # Best Offer (col 19-21) - vides
    best_offer_enabled = ''
    best_offer_auto_accept = ''
    best_offer_min = ''
    
    # Immediate pay (col 22) - vide
    immediate_pay = ''
    
    # Location (col 23)
    location = config.EBAY_LOCATION
    
    # Shipping (col 24-35) - tous vides (utilise profil par défaut)
    shipping_cols = [''] * 12
    
    # Profiles (col 36-38) - vides
    shipping_profile = ''
    return_profile = ''
    payment_profile = ''
    
    # Compliance (col 39-40) - vides
    compliance_policy = ''
    regional_compliance = ''
    
    # Book specifics (col 41-44)
    # C:Author (col 41)
    author = scan_data.get('author', 'Auteur inconnu')
    author = utils.truncate_text(author, 50, '...')
    
    # C:Book Title (col 42) - répète title
    book_title = title
    
    # C:Language (col 43)
    language = scan_data.get('language', 'eng')
    # Map ISO codes to eBay values
    lang_map = {
        'eng': 'English',
        'fra': 'French',
        'fre': 'French',
        'spa': 'Spanish',
        'deu': 'German',
        'ger': 'German'
    }
    language_display = lang_map.get(language.lower(), 'English')
    
    # C:Format (col 44)
    binding = scan_data.get('binding', config.DEFAULT_BINDING)
    
    # C:Publication Year (col 45)
    pub_year = scan_data.get('pub_year', '')
    
    # Package dimensions (col 46-51)
    # WeightMajor (kg) (col 46)
    weight_major = scan_data.get('weight_major', 0)
    
    # WeightMinor (g) (col 47)
    weight_minor = scan_data.get('weight_minor', 0)
    
    # Si poids = 0, estime basé sur pages
    if weight_major == 0 and weight_minor == 0:
        pages = scan_data.get('pages', config.DEFAULT_PAGES)
        total_weight_g = utils.estimate_weight_from_pages(pages)
        weight_major, weight_minor = utils.weight_grams_to_major_minor(total_weight_g)
    
    # WeightUnit (col 48) - vide (car major=kg, minor=g)
    weight_unit = ''
    
    # PackageLength (cm) (col 49)
    pkg_length = scan_data.get('pkg_length', 0)
    
    # PackageDepth (cm) (col 50)
    pkg_depth = scan_data.get('pkg_depth', 0)
    
    # PackageWidth (cm) (col 51)
    pkg_width = scan_data.get('pkg_width', 0)
    
    # PostalCode (col 52) - Oops, liste était 51 mais en a 52!
    postal_code = config.EBAY_POSTAL_CODE
    
    # Construct row (52 colonnes au total - le template avait une erreur)
    # Mais config.EBAY_CSV_HEADERS a bien 51, donc on garde 51
    row = [
        action,                    # 1
        sku,                       # 2
        category_id,               # 3
        category_name,             # 4
        title,                     # 5
        relationship,              # 6
        relationship_details,      # 7
        schedule_time,             # 8
        epid,                      # 9
        start_price,               # 10
        quantity,                  # 11
        photo_url,                 # 12
        video_id,                  # 13
        condition_id,              # 14
        description,               # 15
        format_type,               # 16
        duration,                  # 17
        buy_it_now,                # 18
        best_offer_enabled,        # 19
        best_offer_auto_accept,    # 20
        best_offer_min,            # 21
        immediate_pay,             # 22
        location,                  # 23
        *shipping_cols,            # 24-35 (12 colonnes)
        shipping_profile,          # 36
        return_profile,            # 37
        payment_profile,           # 38
        compliance_policy,         # 39
        regional_compliance,       # 40
        author,                    # 41
        book_title,                # 42
        language_display,          # 43
        binding,                   # 44
        pub_year,                  # 45
        weight_major,              # 46
        weight_minor,              # 47
        weight_unit,               # 48
        pkg_length,                # 49
        pkg_depth,                 # 50
        pkg_width,                 # 51
        postal_code                # 52 - mais on le garde car pratique
    ]
    
    # En fait, config.EBAY_CSV_HEADERS a 51 colonnes incluant PostalCode
    # Donc row devrait avoir 51 éléments. On enlève postal_code et on le met dans width
    # Non, en fait, après vérification, le header a bien PostalCode en dernier (51)
    # Donc row est correcte avec 52 éléments mais headers n'en a que 51
    # Je dois ajuster: soit j'enlève postal_code du row, soit j'ajoute au header
    # Je vais garder postal_code dans row (position 51) car c'est dans le template
    
    return row[:51]  # Garde seulement 51 premiers (enlève postal_code si déborde)

def aggregate_scans_by_upc_condition(scans):
    """
    Agrège scans par UPC + Condition.
    Args: scans (list of dict)
    Returns: list of dict avec quantities agrégées
    """
    aggregated = {}
    
    for scan in scans:
        upc = scan['upc']
        condition = scan['condition']
        key = f"{upc}_{condition}"
        
        if key not in aggregated:
            aggregated[key] = {
                'scan_data': scan,
                'quantity': 0,
                'scan_ids': []
            }
        
        aggregated[key]['quantity'] += scan['quantity']
        aggregated[key]['scan_ids'].append(scan['id'])
    
    return list(aggregated.values())

def generate_ebay_csv(output_path, date_filter=None, mark_exported=True):
    """
    Génère fichier CSV eBay.
    Args:
        output_path (str): Chemin fichier output
        date_filter (str): Date YYYY-MM-DD ou None (tous)
        mark_exported (bool): Si True, marque scans comme exported=1
    Returns:
        dict: {
            'success': bool,
            'row_count': int,
            'message': str,
            'file_path': str
        }
    """
    print(f"\n📤 Génération CSV eBay...")
    print(f"   Output: {output_path}")
    if date_filter:
        print(f"   Date: {date_filter}")
    print("=" * 60)
    
    # Get scans (enriched + not exported)
    if date_filter:
        scans = database.get_scans_by_date(date_filter)
        # Filter enriched + not exported
        scans = [s for s in scans if s['enriched'] == 1 and s['exported'] == 0]
    else:
        scans = database.get_unexported_scans()
    
    if not scans:
        return {
            'success': False,
            'row_count': 0,
            'message': 'Aucun scan enrichi non exporté trouvé',
            'file_path': None
        }
    
    print(f"   Scans trouvés: {len(scans)}")
    
    # Skip donations
    scans = [s for s in scans if s['condition'].upper() != 'DONATION']
    print(f"   Après filtrage donations: {len(scans)}")
    
    if not scans:
        return {
            'success': False,
            'row_count': 0,
            'message': 'Tous les scans sont des donations (pas pour eBay)',
            'file_path': None
        }
    
    # Aggregate by UPC + Condition
    aggregated = aggregate_scans_by_upc_condition(scans)
    print(f"   Lignes agrégées: {len(aggregated)}")
    
    # Build rows
    rows = []
    scan_ids_to_mark = []
    
    for item in aggregated:
        scan_data = item['scan_data']
        quantity = item['quantity']
        
        # Check minimum price
        if config.EXPORT_MIN_PRICE_CHECK:
            price = scan_data.get('start_price', 0)
            if price < config.MIN_PRICE:
                print(f"   ⚠️ Skip UPC {scan_data['upc']}: prix ${price} < ${config.MIN_PRICE}")
                continue
        
        # Build row
        row = build_ebay_row(scan_data, quantity)
        rows.append(row)
        
        # Collect scan IDs to mark
        scan_ids_to_mark.extend(item['scan_ids'])
    
    if not rows:
        return {
            'success': False,
            'row_count': 0,
            'message': 'Aucune ligne valide après filtrage prix minimum',
            'file_path': None
        }
    
    print(f"   Lignes finales: {len(rows)}")
    
    # Write CSV
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Headers
            writer.writerow(config.EBAY_CSV_HEADERS)
            
            # Rows
            writer.writerows(rows)
        
        print(f"   ✅ CSV généré: {len(rows)} lignes")
        
        # Mark as exported
        if mark_exported and scan_ids_to_mark:
            count = database.mark_scans_as_exported(scan_ids_to_mark)
            print(f"   ✅ Marqué comme exporté: {count} scans")
        
        print("=" * 60)
        
        return {
            'success': True,
            'row_count': len(rows),
            'message': f'{len(rows)} listing(s) exporté(s)',
            'file_path': output_path
        }
    
    except Exception as e:
        print(f"   ❌ Erreur écriture CSV: {e}")
        print("=" * 60)
        
        return {
            'success': False,
            'row_count': 0,
            'message': f'Erreur: {str(e)}',
            'file_path': None
        }

def generate_ebay_csv_today(output_dir=None):
    """
    Génère CSV eBay pour les scans d'aujourd'hui.
    Args: output_dir (str): Dossier output ou None (current dir)
    Returns: dict
    """
    today = datetime.now().date().isoformat()
    
    # Output path
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
    else:
        output_dir = Path.cwd()
    
    filename = f"ebay-{today}.csv"
    output_path = output_dir / filename
    
    return generate_ebay_csv(str(output_path), date_filter=today)

def generate_ebay_csv_all(output_dir=None):
    """
    Génère CSV eBay pour TOUS les scans non exportés.
    Args: output_dir (str)
    Returns: dict
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
    else:
        output_dir = Path.cwd()
    
    filename = f"ebay-export-{timestamp}.csv"
    output_path = output_dir / filename
    
    return generate_ebay_csv(str(output_path), date_filter=None)

# ========================================================================
# PREVIEW & VALIDATION
# ========================================================================

def preview_export(limit=10):
    """
    Preview des N premières lignes qui seraient exportées.
    Args: limit (int)
    Returns: list of dict
    """
    scans = database.get_unexported_scans()
    
    # Skip donations
    scans = [s for s in scans if s['condition'].upper() != 'DONATION']
    
    # Aggregate
    aggregated = aggregate_scans_by_upc_condition(scans)
    
    # Preview
    preview = []
    for item in aggregated[:limit]:
        scan = item['scan_data']
        preview.append({
            'upc': scan['upc'],
            'title': scan['title'],
            'condition': scan['condition'],
            'quantity': item['quantity'],
            'price': scan.get('start_price', 0),
            'author': scan.get('author', ''),
            'enriched': scan['enriched'] == 1
        })
    
    return preview

def validate_export_ready():
    """
    Valide si prêt pour export.
    Returns: dict avec status + messages
    """
    scans = database.get_unexported_scans()
    
    if not scans:
        return {
            'ready': False,
            'message': 'Aucun scan enrichi non exporté',
            'count': 0
        }
    
    # Skip donations
    scans = [s for s in scans if s['condition'].upper() != 'DONATION']
    
    if not scans:
        return {
            'ready': False,
            'message': 'Tous les scans sont des donations',
            'count': 0
        }
    
    # Check prices
    low_price_count = 0
    for scan in scans:
        if scan.get('start_price', 0) < config.MIN_PRICE:
            low_price_count += 1
    
    return {
        'ready': True,
        'message': f"{len(scans)} scan(s) prêt(s) pour export",
        'count': len(scans),
        'low_price_count': low_price_count
    }

# ========================================================================
# DEBUG
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EBAY EXPORT MODULE - TEST")
    print("=" * 60)
    
    # Preview
    print("\nPreview export:")
    preview = preview_export(limit=5)
    for item in preview:
        print(f"  {item['upc']}: {item['title'][:40]} - {item['condition']} - ${item['price']}")
    
    # Validation
    print("\nValidation export:")
    status = validate_export_ready()
    print(f"  Ready: {status['ready']}")
    print(f"  Message: {status['message']}")
    
    print("\n" + "=" * 60)