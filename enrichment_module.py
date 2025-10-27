"""
Module Enrichissement - Scanner Livre App
Enrichit les livres scannés avec Google Books API et OpenLibrary API
"""

import requests
import time
from datetime import datetime
import config
import utils
import database

# ========================================================================
# GOOGLE BOOKS API
# ========================================================================

def fetch_google_books(upc):
    """
    Appelle Google Books API pour un ISBN/UPC.
    Args: upc (str)
    Returns: dict ou None
    """
    url = f"{config.GOOGLE_BOOKS_API}?q=isbn:{upc}"
    
    try:
        response = requests.get(url, timeout=config.GOOGLE_BOOKS_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('totalItems', 0) > 0:
                return parse_google_books_response(data)
        
        return None
    
    except requests.exceptions.Timeout:
        print(f"⚠️ Google Books timeout pour UPC {upc}")
        return None
    
    except Exception as e:
        print(f"❌ Erreur Google Books pour UPC {upc}: {e}")
        return None

def parse_google_books_response(data):
    """
    Parse réponse Google Books API.
    Args: data (dict) - réponse JSON API
    Returns: dict
    """
    try:
        item = data['items'][0]
        volume_info = item.get('volumeInfo', {})
        
        # Authors (peut être liste)
        authors = volume_info.get('authors', [])
        author = ', '.join(authors) if authors else None
        
        # Publisher
        publisher = volume_info.get('publisher')
        
        # Publication date (peut être YYYY ou YYYY-MM-DD)
        pub_date = volume_info.get('publishedDate', '')
        pub_year = pub_date[:4] if pub_date else None
        
        # Pages
        pages = volume_info.get('pageCount')
        
        # Description
        description = volume_info.get('description')
        if description:
            description = utils.clean_text(description)
            description = utils.truncate_text(description, 1000)
        
        # Image
        image_links = volume_info.get('imageLinks', {})
        image_url = (image_links.get('thumbnail') or 
                     image_links.get('smallThumbnail'))
        
        # Language
        language = volume_info.get('language', config.DEFAULT_LANGUAGE)
        
        # Title (fallback)
        title = volume_info.get('title')
        
        return {
            'author': author,
            'publisher': publisher,
            'pub_year': pub_year,
            'pages': pages,
            'description': description,
            'image_url': image_url,
            'language': language,
            'title': title,
            'source': 'google_books'
        }
    
    except (KeyError, IndexError, TypeError) as e:
        print(f"⚠️ Erreur parsing Google Books: {e}")
        return None

# ========================================================================
# OPENLIBRARY API
# ========================================================================

def fetch_openlibrary(upc):
    """
    Appelle OpenLibrary API pour un ISBN.
    Essaie ISBN-13 ET ISBN-10 (conversion automatique).
    Args: upc (str)
    Returns: dict ou None
    """
    # Essaie ISBN-13
    bibkeys = [f"ISBN:{upc}"]
    
    # Essaie aussi ISBN-10 (conversion)
    isbn10 = utils.isbn13_to_isbn10(upc)
    if isbn10:
        bibkeys.append(f"ISBN:{isbn10}")
    
    url = f"{config.OPENLIBRARY_API}?bibkeys={','.join(bibkeys)}&format=json&jscmd=data"
    
    try:
        response = requests.get(url, timeout=config.OPENLIBRARY_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Trouve première clé valide
            for bibkey in bibkeys:
                if bibkey in data:
                    return parse_openlibrary_response(data[bibkey], upc)
        
        return None
    
    except requests.exceptions.Timeout:
        print(f"⚠️ OpenLibrary timeout pour UPC {upc}")
        return None
    
    except Exception as e:
        print(f"❌ Erreur OpenLibrary pour UPC {upc}: {e}")
        return None

def parse_openlibrary_response(data, upc):
    """
    Parse réponse OpenLibrary API.
    Args: data (dict), upc (str)
    Returns: dict
    """
    try:
        # Authors
        authors_list = data.get('authors', [])
        author = ', '.join([a.get('name', '') for a in authors_list]) if authors_list else None
        
        # Publishers
        publishers_list = data.get('publishers', [])
        publisher = publishers_list[0].get('name') if publishers_list else None
        
        # Publish date
        pub_date = data.get('publish_date', '')
        pub_year = pub_date[-4:] if len(pub_date) >= 4 else None
        
        # Pages
        pages = data.get('number_of_pages')
        
        # Description (parfois dans 'notes')
        description = None
        if 'notes' in data:
            notes = data['notes']
            if isinstance(notes, dict):
                description = notes.get('value')
            elif isinstance(notes, str):
                description = notes
        
        if description:
            description = utils.clean_text(description)
            description = utils.truncate_text(description, 1000)
        
        # Cover image
        cover = data.get('cover', {})
        image_url = cover.get('medium') or cover.get('small') or cover.get('large')
        
        # Title
        title = data.get('title')
        
        return {
            'author': author,
            'publisher': publisher,
            'pub_year': pub_year,
            'pages': pages,
            'description': description,
            'image_url': image_url,
            'title': title,
            'source': 'openlibrary'
        }
    
    except (KeyError, IndexError, TypeError) as e:
        print(f"⚠️ Erreur parsing OpenLibrary: {e}")
        return None

# ========================================================================
# MERGE & ENRICH
# ========================================================================

def merge_book_data(gb_data, ol_data, manifest_data, scan_data):
    """
    Fusionne données de Google Books, OpenLibrary, MANIFEST et scan.
    Priorité: Google Books > OpenLibrary > MANIFEST > Defaults
    Args: gb_data (dict), ol_data (dict), manifest_data (dict), scan_data (dict)
    Returns: dict complet
    """
    merged = {}
    
    # UPC
    merged['upc'] = scan_data.get('upc')
    
    # Title (MANIFEST prioritaire car c'est la source officielle)
    merged['title'] = (manifest_data.get('title') or 
                       (gb_data.get('title') if gb_data else None) or
                       (ol_data.get('title') if ol_data else None) or
                       'Titre inconnu')
    
    # Author
    merged['author'] = ((gb_data.get('author') if gb_data else None) or
                        (ol_data.get('author') if ol_data else None) or
                        'Auteur inconnu')
    
    # Publisher
    merged['publisher'] = ((gb_data.get('publisher') if gb_data else None) or
                           (ol_data.get('publisher') if ol_data else None) or
                           '')
    
    # Publication year
    merged['pub_year'] = ((gb_data.get('pub_year') if gb_data else None) or
                          (ol_data.get('pub_year') if ol_data else None) or
                          '')
    
    # Pages
    merged['pages'] = ((gb_data.get('pages') if gb_data else None) or
                       (ol_data.get('pages') if ol_data else None) or
                       config.DEFAULT_PAGES)
    
    # Binding (Google Books plus fiable)
    merged['binding'] = config.DEFAULT_BINDING
    
    # Language
    merged['language'] = ((gb_data.get('language') if gb_data else None) or
                          config.DEFAULT_LANGUAGE)
    
    # Description (préfère GB car souvent plus complète)
    merged['description'] = ((gb_data.get('description') if gb_data else None) or
                             (ol_data.get('description') if ol_data else None) or
                             'Description non disponible.')
    
    # Image (préfère GB car meilleure qualité)
    merged['image_url'] = ((gb_data.get('image_url') if gb_data else None) or
                           (ol_data.get('image_url') if ol_data else None) or
                           '')
    
    # Condition (depuis scan)
    merged['condition'] = scan_data.get('condition')
    
    # MSRP (depuis MANIFEST)
    merged['msrp'] = manifest_data.get('msrp', 0)
    
    # Calculate price
    merged['start_price'] = utils.calculate_price(merged['msrp'], merged['condition'])
    
    # eBay specifics
    merged['ebay_category'] = config.EBAY_CATEGORY_BOOKS
    merged['ebay_condition_id'] = config.get_condition_info(merged['condition'])['id']
    
    # Generate HTML description
    merged['description_html'] = utils.generate_ebay_description(merged)
    
    # Source info (pour debug)
    sources = []
    if gb_data:
        sources.append('GoogleBooks')
    if ol_data:
        sources.append('OpenLibrary')
    merged['data_source'] = '+'.join(sources) if sources else 'None'
    
    return merged

def enrich_book(upc, progress_callback=None):
    """
    Enrichit un livre (UPC) avec APIs.
    Args: 
        upc (str)
        progress_callback (callable): fonction(message) pour feedback
    Returns: 
        dict: {'success': bool, 'data': dict, 'message': str}
    """
    if progress_callback:
        progress_callback(f"📖 Enrichissement {upc}...")
    
    # 1. Get scan data
    scans = database.get_scans_by_upc(upc)
    if not scans:
        return {
            'success': False,
            'data': None,
            'message': f'UPC {upc} non trouvé dans scans'
        }
    
    scan_data = scans[0]  # Prend premier scan (tous même UPC)
    
    # 2. Get MANIFEST data
    manifest_data = database.get_manifest_by_upc(upc)
    if not manifest_data:
        return {
            'success': False,
            'data': None,
            'message': f'UPC {upc} non trouvé dans MANIFEST'
        }
    
    # 3. Call Google Books API
    if progress_callback:
        progress_callback(f"  🔍 Google Books...")
    
    gb_data = None
    for attempt in range(config.API_MAX_RETRIES):
        gb_data = fetch_google_books(upc)
        if gb_data:
            break
        if attempt < config.API_MAX_RETRIES - 1:
            time.sleep(config.API_RETRY_DELAY)
    
    # Rate limiting
    time.sleep(config.GOOGLE_BOOKS_RATE_LIMIT)
    
    # 4. Call OpenLibrary API
    if progress_callback:
        progress_callback(f"  🔍 OpenLibrary...")
    
    ol_data = None
    for attempt in range(config.API_MAX_RETRIES):
        ol_data = fetch_openlibrary(upc)
        if ol_data:
            break
        if attempt < config.API_MAX_RETRIES - 1:
            time.sleep(config.API_RETRY_DELAY)
    
    # Rate limiting
    time.sleep(config.OPENLIBRARY_RATE_LIMIT)
    
    # 5. Merge data
    if not gb_data and not ol_data:
        # Aucune donnée API → use MANIFEST seulement
        merged = {
            'upc': upc,
            'title': manifest_data.get('title', 'Titre inconnu'),
            'author': 'Auteur inconnu',
            'publisher': '',
            'pub_year': '',
            'pages': config.DEFAULT_PAGES,
            'binding': config.DEFAULT_BINDING,
            'language': config.DEFAULT_LANGUAGE,
            'description': 'Description non disponible.',
            'description_html': '',
            'image_url': '',
            'condition': scan_data.get('condition'),
            'msrp': manifest_data.get('msrp', 0),
            'start_price': utils.calculate_price(manifest_data.get('msrp', 0), scan_data.get('condition')),
            'ebay_category': config.EBAY_CATEGORY_BOOKS,
            'ebay_condition_id': config.get_condition_info(scan_data.get('condition'))['id'],
            'data_source': 'MANIFEST_only'
        }
        
        # Generate basic description
        merged['description_html'] = utils.generate_ebay_description(merged)
    
    else:
        merged = merge_book_data(gb_data, ol_data, manifest_data, scan_data)
    
    # 6. Update database
    database.update_scan_enrichment(upc, merged)
    
    if progress_callback:
        progress_callback(f"  ✅ Enrichi! (source: {merged.get('data_source', 'unknown')})")
    
    return {
        'success': True,
        'data': merged,
        'message': f"Enrichi avec {merged.get('data_source', 'unknown')}"
    }

# ========================================================================
# BATCH ENRICHMENT
# ========================================================================

def enrich_books(upc_list, progress_callback=None):
    """
    Enrichit une liste d'UPCs.
    Args:
        upc_list (list of str)
        progress_callback (callable): fonction(current, total, message)
    Returns:
        dict: {
            'success': int,
            'failed': int,
            'results': [dict, ...]
        }
    """
    results = []
    total = len(upc_list)
    success_count = 0
    failed_count = 0
    
    print(f"\n🔍 Enrichissement de {total} livre(s)...")
    print("=" * 60)
    
    for i, upc in enumerate(upc_list):
        current = i + 1
        
        # Progress callback
        if progress_callback:
            progress_callback(current, total, f"Livre {current}/{total}: {upc}")
        
        # Log
        print(f"\n[{current}/{total}] UPC: {upc}")
        
        # Enrich
        def item_progress(message):
            print(f"  {message}")
        
        result = enrich_book(upc, progress_callback=item_progress)
        
        # Store result
        results.append({
            'upc': upc,
            'success': result['success'],
            'message': result['message'],
            'data': result['data']
        })
        
        # Count
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Enrichissement terminé!")
    print(f"  Succès: {success_count}")
    print(f"  Échecs: {failed_count}")
    print("=" * 60)
    
    return {
        'success': success_count,
        'failed': failed_count,
        'results': results
    }

def enrich_unenriched_scans(progress_callback=None):
    """
    Enrichit tous les scans non enrichis (enriched=0).
    Args: progress_callback (callable)
    Returns: dict
    """
    # Get unenriched scans
    scans = database.get_unenriched_scans()
    
    if not scans:
        return {
            'success': 0,
            'failed': 0,
            'results': []
        }
    
    # Extract unique UPCs
    upc_set = set()
    for scan in scans:
        upc_set.add(scan['upc'])
    
    upc_list = list(upc_set)
    
    # Enrich
    return enrich_books(upc_list, progress_callback)

# ========================================================================
# DEBUG
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ENRICHMENT MODULE - TEST")
    print("=" * 60)
    
    # Test UPC (exemple: The Alchemist by Paulo Coelho)
    test_upc = "9780062315007"
    
    print(f"\nTest enrichment pour UPC: {test_upc}")
    
    # Simulate scan + manifest data
    print("\nNote: Ce test requiert que l'UPC existe dans la DB.")
    print("Pour test complet, utilise l'app principale.")
    
    print("\n" + "=" * 60)