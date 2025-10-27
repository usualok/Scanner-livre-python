"""
Configuration centralisée - Scanner Livre App
Toutes les constantes et paramètres de l'application
"""

import os
from pathlib import Path

# ========================================================================
# PATHS & FILES
# ========================================================================

# Détection automatique du dossier de travail
# Si sur clé USB (D:, E:, F:...) → utilise ce dossier
# Sinon → utilise dossier courant
CURRENT_DIR = Path(__file__).parent

# Base de données
DB_FILENAME = "scans.db"
DB_PATH = CURRENT_DIR / DB_FILENAME

# Backup
BACKUP_DIR = CURRENT_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# ========================================================================
# APIS
# ========================================================================

# Google Books API
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_BOOKS_TIMEOUT = 10
GOOGLE_BOOKS_RATE_LIMIT = 1.0  # secondes entre requêtes

# OpenLibrary API
OPENLIBRARY_API = "https://openlibrary.org/api/books"
OPENLIBRARY_TIMEOUT = 10
OPENLIBRARY_RATE_LIMIT = 1.0

# Retry logic
API_MAX_RETRIES = 3
API_RETRY_DELAY = 2  # secondes

# ========================================================================
# EBAY CONFIGURATION
# ========================================================================

# Localisation
EBAY_SITE_ID = "Canada"
EBAY_COUNTRY = "CA"
EBAY_CURRENCY = "CAD"
EBAY_VERSION = "1193"
EBAY_LOCATION = "VALCOURT,QC"
EBAY_POSTAL_CODE = "J0E2L0"

# Catégories
EBAY_CATEGORY_BOOKS = "267"

# Format listing
EBAY_FORMAT = "FixedPrice"
EBAY_DURATION = "GTC"  # Good Till Cancelled

# Headers CSV (51 colonnes exactes)
EBAY_CSV_HEADERS = [
    f'*Action(SiteID={EBAY_SITE_ID}|Country={EBAY_COUNTRY}|Currency={EBAY_CURRENCY}|Version={EBAY_VERSION})',
    'Custom label (SKU)',
    'Category ID',
    'Category name',
    'Title',
    'Relationship',
    'Relationship details',
    'Schedule Time',
    'P:EPID',
    'Start price',
    'Quantity',
    'Item photo URL',
    'VideoID',
    'Condition ID',
    'Description',
    'Format',
    'Duration',
    'Buy It Now price',
    'Best Offer Enabled',
    'Best Offer Auto Accept Price',
    'Minimum Best Offer Price',
    'Immediate pay required',
    'Location',
    'Shipping service 1 option',
    'Shipping service 1 cost',
    'Shipping service 1 priority',
    'Shipping service 2 option',
    'Shipping service 2 cost',
    'Shipping service 2 priority',
    'Max dispatch time',
    'Returns accepted option',
    'Returns within option',
    'Refund option',
    'Return shipping cost paid by',
    'Shipping profile name',
    'Return profile name',
    'Payment profile name',
    'ProductCompliancePolicyID',
    'Regional ProductCompliancePolicies',
    'C:Author',
    'C:Book Title',
    'C:Language',
    'C:Format',
    'C:Publication Year',
    'WeightMajor',
    'WeightMinor',
    'WeightUnit',
    'PackageLength',
    'PackageDepth',
    'PackageWidth',
    'PostalCode'
]

# ========================================================================
# CONDITIONS
# ========================================================================

CONDITIONS = {
    'NEW': {
        'id': '1000',
        'name': 'Brand New',
        'price_factor': 0.70,
        'description': 'Livre neuf, jamais ouvert'
    },
    'GOOD': {
        'id': '2750',
        'name': 'Very Good',
        'price_factor': 0.50,
        'description': 'Livre en très bon état, quelques signes d\'usage mineurs'
    },
    'USED': {
        'id': '5000',
        'name': 'Acceptable',
        'price_factor': 0.35,
        'description': 'Livre usagé, tous les pages intactes'
    },
    'DONATION': {
        'id': '',
        'name': 'Donation',
        'price_factor': 0,
        'description': 'Pour donation (pas eBay)'
    }
}

# Prix minimum (si MSRP × factor < MIN_PRICE)
MIN_PRICE = 3.99

# ========================================================================
# VALIDATION
# ========================================================================

# BIN: Lettre + 3-4 chiffres (ex: C001, I004, Z9999)
BIN_REGEX = r'^[A-Z]\d{3,4}$'

# UPC: 10-14 chiffres
UPC_MIN_LENGTH = 10
UPC_MAX_LENGTH = 14

# Conditions valides
VALID_CONDITIONS = ['NEW', 'GOOD', 'USED', 'DONATION']

# ========================================================================
# UI CONFIGURATION
# ========================================================================

# Fenêtre principale
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = "📚 Scanner Livre Pro"

# Theme
UI_THEME = "clam"

# Couleurs
COLOR_SUCCESS = "#2ecc71"
COLOR_ERROR = "#e74c3c"
COLOR_WARNING = "#f39c12"
COLOR_INFO = "#3498db"
COLOR_BACKGROUND = "#ecf0f1"

# Fonts
FONT_TITLE = ("Arial", 14, "bold")
FONT_NORMAL = ("Arial", 10)
FONT_SMALL = ("Arial", 9)
FONT_MONO = ("Courier", 10)

# Sizes
PADDING = 10
BUTTON_WIDTH = 20
ENTRY_WIDTH = 50

# ========================================================================
# DATABASE
# ========================================================================

# Table names
TABLE_MANIFEST = "manifest"
TABLE_SCANS = "scans"
TABLE_DIMENSIONS = "dimensions"
TABLE_SALES = "sales"

# Status
STATUS_PENDING = "En attente"
STATUS_LISTED = "En vente eBay"
STATUS_SOLD = "Vendu"

STATUS_OPTIONS = [STATUS_PENDING, STATUS_LISTED, STATUS_SOLD]

# ========================================================================
# ENRICHMENT
# ========================================================================

# Calcul poids estimé (si pas de dimensions)
WEIGHT_PER_PAGE = 8  # grammes par page (estimation)
DEFAULT_PAGES = 200  # si pages inconnues

# Langue par défaut
DEFAULT_LANGUAGE = "eng"

# Binding par défaut
DEFAULT_BINDING = "Paperback"

# ========================================================================
# EXPORT
# ========================================================================

# Filtres export
EXPORT_MIN_ENRICHED = True  # Exporte seulement si enriched=1
EXPORT_MIN_PRICE_CHECK = True  # Skip si price < MIN_PRICE

# ========================================================================
# LOGGING
# ========================================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = False  # Si True, écrit dans scanner.log

# ========================================================================
# MISC
# ========================================================================

# Manifest
MANIFEST_TOTAL_BOOKS = 14000  # Pour calculs progression

# Toast duration
TOAST_DURATION = 3  # secondes

# Progress refresh
PROGRESS_REFRESH_MS = 100  # millisecondes

# ========================================================================
# HELPERS
# ========================================================================

def get_db_path():
    """Retourne le chemin absolu de la DB."""
    return str(DB_PATH.absolute())

def get_backup_dir():
    """Retourne le chemin du dossier backup."""
    return str(BACKUP_DIR.absolute())

def is_on_usb_drive():
    """Détecte si l'app est sur clé USB (Windows: D:, E:, F:...)."""
    drive = Path(CURRENT_DIR).drive
    return drive and drive.upper() in ['D:', 'E:', 'F:', 'G:', 'H:']

def get_condition_info(condition):
    """Retourne info condition."""
    return CONDITIONS.get(condition.upper(), CONDITIONS['USED'])

# ========================================================================
# VALIDATION HELPERS
# ========================================================================

def validate_condition(condition):
    """Valide que la condition est valide."""
    return condition.upper() in VALID_CONDITIONS

def get_price_factor(condition):
    """Retourne le facteur de prix pour une condition."""
    return CONDITIONS.get(condition.upper(), {}).get('price_factor', 0.35)

# ========================================================================
# DEBUG INFO
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SCANNER LIVRE - CONFIGURATION")
    print("=" * 60)
    print(f"Database: {get_db_path()}")
    print(f"Backup dir: {get_backup_dir()}")
    print(f"On USB drive: {is_on_usb_drive()}")
    print(f"Conditions: {list(CONDITIONS.keys())}")
    print(f"eBay headers: {len(EBAY_CSV_HEADERS)} colonnes")
    print("=" * 60)