"""
Fonctions utilitaires - Scanner Livre App
Helpers, validations, conversions, etc.
"""

import re
from datetime import datetime
import config

# ========================================================================
# VALIDATION
# ========================================================================

def validate_bin(bin_code):
    """
    Valide format BIN: Lettre + 3-4 chiffres (ex: C001, I004, Z9999).
    Returns: True si valide, False sinon
    """
    if not bin_code:
        return False
    
    return re.match(config.BIN_REGEX, bin_code.upper()) is not None

def validate_upc(upc):
    """
    Valide format UPC: 10-14 chiffres.
    Returns: True si valide, False sinon
    """
    if not upc:
        return False
    
    # Doit être que des chiffres
    if not upc.isdigit():
        return False
    
    # Longueur 10-14
    length = len(upc)
    return config.UPC_MIN_LENGTH <= length <= config.UPC_MAX_LENGTH

def validate_condition(condition):
    """
    Valide condition: NEW, GOOD, USED, DONATION.
    Returns: True si valide, False sinon
    """
    if not condition:
        return False
    
    return condition.upper() in config.VALID_CONDITIONS

def validate_scan_input(bin_code, upc, condition):
    """
    Valide une entrée de scan complète.
    Returns: (bool, str) - (is_valid, error_message)
    """
    if not bin_code:
        return False, "BIN manquant"
    
    if not validate_bin(bin_code):
        return False, f"BIN invalide: {bin_code}\nFormat attendu: Lettre + 3-4 chiffres (ex: C001)"
    
    if not upc:
        return False, "UPC manquant"
    
    if not validate_upc(upc):
        return False, f"UPC invalide: {upc}\nDoit contenir {config.UPC_MIN_LENGTH}-{config.UPC_MAX_LENGTH} chiffres"
    
    if not condition:
        return False, "Condition manquante"
    
    if not validate_condition(condition):
        return False, f"Condition invalide: {condition}\nValides: {', '.join(config.VALID_CONDITIONS)}"
    
    return True, ""

# ========================================================================
# CONVERSION & FORMATTING
# ========================================================================

def format_date(date_obj=None):
    """
    Formate une date en YYYY-MM-DD.
    Args: datetime object ou None (défaut: aujourd'hui)
    Returns: str
    """
    if date_obj is None:
        date_obj = datetime.now()
    
    return date_obj.strftime('%Y-%m-%d')

def format_timestamp(dt=None):
    """
    Formate datetime en ISO8601.
    Args: datetime object ou None (défaut: maintenant)
    Returns: str
    """
    if dt is None:
        dt = datetime.now()
    
    return dt.isoformat()

def format_price(price):
    """
    Formate prix en $X.XX.
    Args: float
    Returns: str
    """
    if price is None:
        return "$0.00"
    
    return f"${price:.2f}"

def format_percentage(value, total):
    """
    Calcule et formate pourcentage.
    Args: value, total (numbers)
    Returns: str "XX.X%"
    """
    if total == 0:
        return "0.0%"
    
    percent = (value / total) * 100
    return f"{percent:.1f}%"

# ========================================================================
# ISBN CONVERSION
# ========================================================================

def isbn13_to_isbn10(isbn13):
    """
    Convertit ISBN-13 en ISBN-10.
    Args: ISBN-13 (str, 13 chiffres)
    Returns: ISBN-10 (str, 10 caractères) ou None si invalide
    
    Note: ISBN-13 commençant par 978 ou 979 peuvent être convertis
    """
    if not isbn13 or len(isbn13) != 13:
        return None
    
    # Enlève le préfixe 978 ou 979
    if not isbn13.startswith('978') and not isbn13.startswith('979'):
        return None
    
    # Prend les 9 premiers chiffres après le préfixe
    isbn10_base = isbn13[3:12]
    
    # Calcule checksum ISBN-10
    checksum = 0
    for i, digit in enumerate(isbn10_base):
        checksum += int(digit) * (10 - i)
    
    checksum = (11 - (checksum % 11)) % 11
    
    # Checksum = X si 10
    check_char = 'X' if checksum == 10 else str(checksum)
    
    return isbn10_base + check_char

def isbn10_to_isbn13(isbn10):
    """
    Convertit ISBN-10 en ISBN-13.
    Args: ISBN-10 (str, 10 caractères)
    Returns: ISBN-13 (str, 13 chiffres) ou None si invalide
    """
    if not isbn10 or len(isbn10) != 10:
        return None
    
    # Enlève le checksum et ajoute préfixe 978
    isbn13_base = '978' + isbn10[:-1]
    
    # Calcule checksum ISBN-13
    checksum = 0
    for i, digit in enumerate(isbn13_base):
        weight = 1 if i % 2 == 0 else 3
        checksum += int(digit) * weight
    
    checksum = (10 - (checksum % 10)) % 10
    
    return isbn13_base + str(checksum)

# ========================================================================
# TEXT PROCESSING
# ========================================================================

def clean_text(text):
    """
    Nettoie texte: strip, enlève HTML basique.
    Args: str
    Returns: str
    """
    if not text:
        return ""
    
    # Strip
    text = text.strip()
    
    # Enlève tags HTML simples
    text = re.sub(r'<[^>]+>', '', text)
    
    # Enlève espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    return text

def truncate_text(text, max_length=100, suffix='...'):
    """
    Tronque texte à max_length.
    Args: text (str), max_length (int), suffix (str)
    Returns: str
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def sanitize_filename(filename):
    """
    Nettoie nom de fichier (enlève caractères invalides).
    Args: filename (str)
    Returns: str
    """
    # Garde seulement: lettres, chiffres, -, _, .
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Enlève underscores multiples
    filename = re.sub(r'_+', '_', filename)
    
    return filename

# ========================================================================
# PRICING
# ========================================================================

def calculate_price(msrp, condition):
    """
    Calcule prix basé sur MSRP et condition.
    Args: msrp (float), condition (str)
    Returns: float (avec minimum config.MIN_PRICE)
    """
    if not msrp or msrp <= 0:
        return config.MIN_PRICE
    
    factor = config.get_price_factor(condition.upper())
    
    price = msrp * factor
    
    # Applique minimum
    if price < config.MIN_PRICE:
        price = config.MIN_PRICE
    
    # Arrondit à 2 décimales
    return round(price, 2)

def estimate_weight_from_pages(pages):
    """
    Estime poids en grammes basé sur nombre de pages.
    Args: pages (int)
    Returns: int (grammes)
    """
    if not pages or pages <= 0:
        pages = config.DEFAULT_PAGES
    
    # ~8g par page (estimation)
    weight_g = pages * config.WEIGHT_PER_PAGE
    
    return int(weight_g)

def weight_grams_to_major_minor(weight_g):
    """
    Convertit poids en grammes vers (kg, g).
    Args: weight_g (int) - poids en grammes
    Returns: tuple (major_kg, minor_g)
    
    Example: 1250g → (1, 250)
    """
    major_kg = weight_g // 1000
    minor_g = weight_g % 1000
    
    return (major_kg, minor_g)

def major_minor_to_grams(major_kg, minor_g):
    """
    Convertit (kg, g) vers grammes.
    Args: major_kg (int), minor_g (int)
    Returns: int (grammes)
    """
    return (major_kg * 1000) + minor_g

# ========================================================================
# PARSING
# ========================================================================

def parse_scan_input(input_str):
    """
    Parse une entrée de scan: "BIN UPC CONDITION".
    Args: input_str (str)
    Returns: dict {'bin': str, 'upc': str, 'condition': str} ou None
    
    Examples:
      "C001 9781234567890 USED" → {'bin': 'C001', 'upc': '9781234567890', 'condition': 'USED'}
      "I004,9780123456789,NEW" → {'bin': 'I004', 'upc': '9780123456789', 'condition': 'NEW'}
    """
    if not input_str:
        return None
    
    # Split par espaces ou virgules
    parts = re.split(r'[\s,]+', input_str.strip().upper())
    parts = [p for p in parts if p]  # Enlève vides
    
    if len(parts) < 3:
        return None
    
    result = {
        'bin': None,
        'upc': None,
        'condition': None
    }
    
    # Parse chaque part
    for part in parts:
        # BIN: Lettre + chiffres
        if validate_bin(part) and not result['bin']:
            result['bin'] = part
        
        # UPC: 10-14 chiffres
        elif validate_upc(part) and not result['upc']:
            result['upc'] = part
        
        # Condition
        elif validate_condition(part) and not result['condition']:
            result['condition'] = part
    
    # Valide que tous remplis
    if all(result.values()):
        return result
    
    return None

def parse_dimensions_input(input_str):
    """
    Parse dimensions: "kg;g;length;depth;width".
    Args: input_str (str)
    Returns: dict ou None
    
    Example: "0;750;23;2;15" → {'weight_major': 0, 'weight_minor': 750, ...}
    """
    if not input_str:
        return None
    
    parts = input_str.split(';')
    
    if len(parts) != 5:
        return None
    
    try:
        return {
            'weight_major': float(parts[0]),
            'weight_minor': float(parts[1]),
            'pkg_length': float(parts[2]),
            'pkg_depth': float(parts[3]),
            'pkg_width': float(parts[4])
        }
    except ValueError:
        return None

# ========================================================================
# DESCRIPTION GENERATION
# ========================================================================

def generate_ebay_description(book_data):
    """
    Génère description HTML pour eBay.
    Args: book_data (dict) - données livre
    Returns: str (HTML)
    """
    title = book_data.get('title', 'Titre non disponible')
    author = book_data.get('author', 'Auteur inconnu')
    publisher = book_data.get('publisher', '')
    pub_year = book_data.get('pub_year', '')
    isbn = book_data.get('upc', '')
    binding = book_data.get('binding', '')
    pages = book_data.get('pages', '')
    language = book_data.get('language', 'eng')
    description = book_data.get('description', 'Description non disponible.')
    condition = book_data.get('condition', 'USED')
    
    # Map language code
    lang_map = {
        'eng': 'Anglais',
        'fra': 'Français',
        'fre': 'Français',
        'spa': 'Espagnol',
        'deu': 'Allemand',
        'ger': 'Allemand'
    }
    lang_display = lang_map.get(language.lower(), language)
    
    # Condition description
    condition_desc = config.CONDITIONS.get(condition.upper(), {}).get('description', '')
    
    html = f"""
<div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background: #ffffff;">
    
    <!-- Header -->
    <div style="background: #2c3e50; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">{title}</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">par {author}</p>
    </div>
    
    <!-- Details Box -->
    <div style="background: #ecf0f1; padding: 20px; border-left: 4px solid #3498db;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px 0; font-weight: bold; width: 150px;">📚 Auteur:</td>
                <td style="padding: 8px 0;">{author}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">🏢 Éditeur:</td>
                <td style="padding: 8px 0;">{publisher} {pub_year}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">🔢 ISBN:</td>
                <td style="padding: 8px 0;">{isbn}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">📖 Format:</td>
                <td style="padding: 8px 0;">{binding}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">📄 Pages:</td>
                <td style="padding: 8px 0;">{pages}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">🌍 Langue:</td>
                <td style="padding: 8px 0;">{lang_display}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">⭐ Condition:</td>
                <td style="padding: 8px 0;">{condition_desc}</td>
            </tr>
        </table>
    </div>
    
    <!-- Description -->
    <div style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 4px;">
        <h2 style="color: #2c3e50; font-size: 18px; margin-top: 0;">📝 À propos de ce livre</h2>
        <p style="line-height: 1.6; color: #555;">{description}</p>
    </div>
    
    <!-- Footer -->
    <div style="margin-top: 30px; padding: 20px; background: #e8f5e9; border-radius: 4px; border-left: 4px solid #4caf50;">
        <h3 style="color: #2e7d32; margin-top: 0; font-size: 16px;">✅ Pourquoi acheter chez nous?</h3>
        <ul style="margin: 10px 0; padding-left: 20px; color: #555;">
            <li style="margin-bottom: 8px;">📦 <strong>Expédition rapide</strong> depuis Valcourt, Québec</li>
            <li style="margin-bottom: 8px;">⭐ <strong>Vendeur professionnel</strong> avec excellentes évaluations</li>
            <li style="margin-bottom: 8px;">🇨🇦 <strong>Entreprise québécoise</strong> - Service en français</li>
            <li style="margin-bottom: 8px;">💯 <strong>Satisfaction garantie</strong> ou remboursement</li>
        </ul>
    </div>
    
    <!-- Contact -->
    <div style="margin-top: 20px; padding: 15px; text-align: center; font-size: 12px; color: #777; border-top: 1px solid #ddd;">
        <p style="margin: 5px 0;">Des questions? N'hésitez pas à nous contacter!</p>
        <p style="margin: 5px 0;">Merci de votre confiance 🙏</p>
    </div>
    
</div>
"""
    
    return html.strip()

# ========================================================================
# HELPERS
# ========================================================================

def safe_float(value, default=0.0):
    """
    Convertit value en float, retourne default si échec.
    Args: value (any), default (float)
    Returns: float
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """
    Convertit value en int, retourne default si échec.
    Args: value (any), default (int)
    Returns: int
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def get_file_size_mb(filepath):
    """
    Retourne taille fichier en MB.
    Args: filepath (str or Path)
    Returns: float
    """
    from pathlib import Path
    try:
        size_bytes = Path(filepath).stat().st_size
        return size_bytes / (1024 * 1024)
    except:
        return 0.0

# ========================================================================
# DEBUG
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("UTILS - TESTS")
    print("=" * 60)
    
    # Test validation
    print("\nValidation:")
    print(f"  BIN 'C001': {validate_bin('C001')}")
    print(f"  BIN 'X99': {validate_bin('X99')}")
    print(f"  UPC '9781234567890': {validate_upc('9781234567890')}")
    print(f"  UPC '12345': {validate_upc('12345')}")
    print(f"  Condition 'NEW': {validate_condition('NEW')}")
    print(f"  Condition 'BROKEN': {validate_condition('BROKEN')}")
    
    # Test parsing
    print("\nParsing:")
    scan = parse_scan_input("C001 9781234567890 USED")
    print(f"  Parse scan: {scan}")
    
    dims = parse_dimensions_input("0;750;23;2;15")
    print(f"  Parse dims: {dims}")
    
    # Test ISBN
    print("\nISBN:")
    isbn10 = isbn13_to_isbn10("9781234567890")
    print(f"  ISBN-13 → ISBN-10: {isbn10}")
    
    # Test pricing
    print("\nPricing:")
    price = calculate_price(29.99, 'GOOD')
    print(f"  MSRP $29.99, GOOD: {format_price(price)}")
    
    # Test weight
    print("\nWeight:")
    weight = estimate_weight_from_pages(300)
    print(f"  300 pages → {weight}g")
    major, minor = weight_grams_to_major_minor(weight)
    print(f"  {weight}g → {major}kg {minor}g")
    
    print("=" * 60)