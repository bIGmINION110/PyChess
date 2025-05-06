# -*- coding: utf-8 -*-
# Dateiname: PyChess/config.py
"""
Konfigurationsdatei für das PyChess-Spiel.
Enthält Konstanten für Fenstergröße, Farben, Schriftarten, Pfade,
Spiel-Logik, KI-Einstellungen und mehr.
Initialisiert auch Pygame-Module wie font und lädt Ressourcen.
"""
import pygame
import chess # Wird für chess.PieceType, chess.WHITE, chess.BLACK benötigt
import os
from typing import Optional # Importiere Optional und Tuple für Type Hinting
import logger, logging
import sys # Für kritische Fehler

# --- Logger Konfiguration (NUR Datei-Logging, mit __name__) ---
# Wichtig: Der Logger wird hier konfiguriert, aber das Logging beginnt erst
# nach der Initialisierung. Frühere Fehler (z.B. beim Import) werden nicht geloggt.
log = logger.setup_logger(
    name=__name__,            # Logger-Name ist der Modulname (z.B. 'config')
    log_file='logs/PyChess.txt', # Loggt in dieselbe Datei wie andere Module
    level=logging.DEBUG,      # Loggt alles ab DEBUG-Level
    console=False,            # KEIN Logging in die Konsole
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)


# --- Debugging ---
DEBUG_MODE = True # Zusätzliche Log-Ausgaben (DEBUG Level) aktivieren?
log.info("Debug Mode: %s", DEBUG_MODE)

TARGET_FPS = 120
log.info("Target FPS set to: %d", TARGET_FPS)

# -- Grundlegende Fenster- und Brett-Einstellungen --
WIDTH = 800      # Breite des Hauptfensters in Pixeln
HEIGHT = 600     # Höhe des Hauptfensters in Pixeln
BOARD_WIDTH = 480 # Breite des Schachbretts in Pixeln (Standard: 480 für 60x60 Felder)
BOARD_HEIGHT = 480# Höhe des Schachbretts in Pixeln
SQ_SIZE = BOARD_WIDTH // 8 # Größe eines einzelnen Feldes auf dem Brett (Standard: 60)
log.info("Window Dimensions: %dx%d", WIDTH, HEIGHT)
log.info("Board Dimensions: %dx%d (Square Size: %d)", BOARD_WIDTH, BOARD_HEIGHT, SQ_SIZE)


# Berechne den Offset, um das Brett im Fenster zu zentrieren
BOARD_OFFSET_X = (WIDTH - BOARD_WIDTH) // 2
BOARD_OFFSET_Y = (HEIGHT - BOARD_HEIGHT) // 2
log.info("Board Offset: X=%d, Y=%d", BOARD_OFFSET_X, BOARD_OFFSET_Y)

# --- Timer-Position ---
TIMER_POS_X = 15
TIMER_POS_Y = 15
log.info("Timer Position: X=%d, Y=%d", TIMER_POS_X, TIMER_POS_Y)

# --- Statusanzeige Position & Dauer ---
STATUS_POS_X = WIDTH // 2 # X-Koordinate des Mittelpunkts
STATUS_POS_Y = TIMER_POS_Y # Gleiche Höhe wie Timer
STATUS_MOVE_DURATION = 5.0 # Sekunden, wie lange der letzte Zug angezeigt wird
log.info("Status Display Position: X=%d, Y=%d, Move Duration: %.1f s", STATUS_POS_X, STATUS_POS_Y, STATUS_MOVE_DURATION)

# --- Verzeichnisse und Dateipfade ---
# Dynamische Ermittlung des Projekt-Basisverzeichnisses
try:
    # Annahme: config.py liegt im Hauptverzeichnis des Projekts
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback, wenn __file__ nicht definiert ist (z.B. in manchen Umgebungen)
    log.warning("__file__ not defined, using current working directory as BASE_DIR.")
    BASE_DIR = os.path.abspath(".")
log.info("Base Directory: %s", BASE_DIR)

ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMAGE_DIR = os.path.join(ASSETS_DIR, 'images')   # Verzeichnis für Figurenbilder
SOUND_DIR = os.path.join(ASSETS_DIR, 'sounds')   # Verzeichnis für Soundeffekte
FONT_DIR = os.path.join(ASSETS_DIR, 'fonts')     # Verzeichnis für benutzerdefinierte Schriftarten
BOOK_DIR = os.path.join(ASSETS_DIR, 'books')     # Verzeichnis für Eröffnungsbücher
SYZYGY_DIR = os.path.join(ASSETS_DIR, 'syzygy')  # Verzeichnis für Endspieldatenbanken (optional)
SAVE_DIR = os.path.join(BASE_DIR, 'saves')       # Verzeichnis für Speicherstände
log.info("Assets Directory: %s", ASSETS_DIR)
log.info("Save Directory: %s", SAVE_DIR)


# Pfad zum Standard-Eröffnungsbuch (Polyglot-Format)
POLYGLOT_BOOK_PATH = os.path.join(BOOK_DIR, 'human.bin')
# POLYGLOT_BOOK_PATH = "" # Deaktivieren, wenn kein Buch verwendet wird
log.info("Polyglot Book Path: %s", POLYGLOT_BOOK_PATH if POLYGLOT_BOOK_PATH else "Disabled")

# Pfad zu den Syzygy-Endspieldatenbanken (optional)
SYZYGY_PATH = "" # Standardmäßig deaktiviert
SYZYGY_MAX_PIECES = 7 # Maximale Anzahl Figuren für Syzygy-Nutzung
log.info("Syzygy Path: %s", SYZYGY_PATH if SYZYGY_PATH else "Disabled")
if SYZYGY_PATH: log.info("Syzygy Max Pieces: %d", SYZYGY_MAX_PIECES)

# --- Speicherformat Version ---
# Wird in die Speicherdatei geschrieben, um Kompatibilität zu prüfen
SAVE_FORMAT_VERSION = "1.0"
log.info("Save Format Version: %s", SAVE_FORMAT_VERSION)

# --- Farben (RGB-Tupel oder RGBA für Transparenz) ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0) # Goldfarbe für Titel

# Brettfarben
LIGHT_SQUARE_COLOR = (245, 245, 220) # Beige
DARK_SQUARE_COLOR = (160, 82, 45)   # Braun (SaddleBrown ähnlich)

# Hervorhebungsfarben (mit Alpha für Transparenz, 0=transparent, 255=opak)
HIGHLIGHT_COLOR_LEGAL_MOVE = (0, 255, 0, 80)      # Grün, leicht transparent
HIGHLIGHT_COLOR_LEGAL_CAPTURE = (255, 0, 0, 80)   # Rot, leicht transparent
SELECTED_SQUARE_COLOR = (82, 121, 147, 100)  # Bläulich, Cursor
PICKUP_HIGHLIGHT_COLOR = (255, 165, 0, 120) # Orange, halbtransparent
PREMOVE_SQUARE_COLOR = (210, 180, 140, 150) # Beige/Braun, halbtransparent (optional)
LAST_MOVE_HIGHLIGHT_COLOR = (170, 162, 58, 100) # Gelblich
CHECK_HIGHLIGHT_COLOR = (255, 0, 0, 120)      # Rot, halbtransparent

# Blink-Einstellungen für legale Züge
LEGAL_MOVE_BLINK_CYCLE_MS = 800  # Gesamtdauer eines Blink-Zyklus in Millisekunden
LEGAL_MOVE_BLINK_ON_MS = 400   # Dauer, für die das Feld während eines Zyklus sichtbar ist

# GUI-Element Farben
WINDOW_BACKGROUND_COLOR = (30, 30, 30) # Dunkelgrau (RGB)
MAIN_MENU_BACKGROUND_COLOR_RGBA = (30, 30, 30, 200) # Dunkelgrau mit Alpha
INGAME_MENU_BACKGROUND_COLOR_RGBA = MAIN_MENU_BACKGROUND_COLOR_RGBA # Gleich wie Hauptmenü

# Hauptmenü Textfarben
MAIN_MENU_TITLE_COLOR = GOLD
MAIN_MENU_TEXT_COLOR = (220, 220, 220)
MAIN_MENU_BUTTON_TEXT_COLOR = (200, 200, 200)
MAIN_MENU_BUTTON_COLOR = (0, 0, 0, 0) # Transparent
MAIN_MENU_BUTTON_HOVER_BORDER_COLOR = GOLD # Goldener Rahmen bei Hover
MAIN_MENU_BUTTON_HOVER_TEXT_COLOR = WHITE # Text wird weiß bei Hover

# In-Game Menü Farben
INGAME_MENU_TEXT_COLOR = (220, 220, 220)
INGAME_MENU_HIGHLIGHT_COLOR = (100, 100, 100) # Hintergrund für ausgewählte Menüpunkte
INGAME_BUTTON_COLOR = (70, 70, 70) # Nicht verwendet aktuell?
INGAME_BUTTON_TEXT_COLOR = (200, 200, 200) # Nicht verwendet aktuell?
INGAME_BUTTON_HOVER_COLOR = (90, 90, 90) # Nicht verwendet aktuell?

# Koordinatenfarben
COORDINATE_TEXT_COLOR_LIGHT = DARK_SQUARE_COLOR # Dunkler Text auf hellem Feld
COORDINATE_TEXT_COLOR_DARK = LIGHT_SQUARE_COLOR # Heller Text auf dunklem Feld

# Timer Farbe
TIMER_TEXT_COLOR = GOLD

# Statusanzeige Farben
STATUS_TEXT_COLOR = WHITE
STATUS_ERROR_COLOR = RED

# --- Schriftarten ---
# Initialisiere pygame.font, falls noch nicht geschehen
try:
    if not pygame.font.get_init():
        log.info("Initializing Pygame font module...")
        pygame.font.init()
        log.info("Pygame font module initialized.")
    else:
        log.debug("Pygame font module already initialized.")
except Exception as e:
    # Kritischer Fehler, wenn Font nicht initialisiert werden kann
    log.critical("CRITICAL: Pygame font module could not be initialized: %s", e, exc_info=True)
    print(f"!!! KRITISCHER FEHLER: Pygame Font-Modul konnte nicht initialisiert werden: {e} !!!", file=sys.stderr)
    # Beenden? Oder versuchen weiterzumachen? Beenden ist sicherer.
    pygame.quit()
    sys.exit("Font module initialization failed.")

# Versuche, spezifische Schriftarten zu laden, mit System-Fallbacks
DEFAULT_FONT_NAME = "Arial" # Standardschriftart, falls spezifische nicht gefunden wird
DEFAULT_FONT_SIZE = 18
DEFAULT_FONT_LARGE_SIZE = 28
DEFAULT_FONT_SMALL_SIZE = 14

# Name der "gekringelten" Schriftart für den Titel
MAIN_MENU_TITLE_FONT_NAME = 'cursive' # Beispiel: 'cursive' oder spezifischer Name wie 'DancingScript-Regular.ttf'
MAIN_MENU_TITLE_FONT_SIZE = 48 # Größe für den Titel

def get_font(size: int, bold: bool = False, font_name: Optional[str] = None) -> pygame.font.Font:
    """Lädt eine Schriftart oder gibt eine Fallback-Schriftart zurück."""
    target_font_name = font_name or DEFAULT_FONT_NAME
    log.debug("Attempting to load font: Name='%s', Size=%d, Bold=%s", target_font_name, size, bold)

    # 1. Versuch: Spezifische Schriftart aus FONT_DIR (falls font_name angegeben)
    if font_name:
        specific_font_path = os.path.join(FONT_DIR, font_name)
        if os.path.exists(specific_font_path):
            log.debug("Found specific font file: %s", specific_font_path)
            try:
                font = pygame.font.Font(specific_font_path, size)
                # SysFont kann 'bold' direkt setzen, Font nicht. Man könnte simulieren, ist aber aufwändig.
                # Hier ignorieren wir 'bold' für Font-Dateien vorerst.
                log.info("Successfully loaded font from file: %s (Size: %d)", specific_font_path, size)
                return font
            except pygame.error as e:
                log.warning("Could not load specific font file '%s': %s", specific_font_path, e)
        else:
            log.debug("Specific font file not found: %s", specific_font_path)

    # 2. Versuch: Systemschriftart (Standard oder spezifiziert)
    try:
        log.debug("Attempting to load system font: %s (Size: %d, Bold: %s)", target_font_name, size, bold)
        font = pygame.font.SysFont(target_font_name, size, bold=bold)
        log.info("Successfully loaded system font: %s (Size: %d, Bold: %s)", target_font_name, size, bold)
        return font
    except Exception as e:
        log.warning("Could not load system font '%s': %s. Trying Pygame default.", target_font_name, e)
        # 3. Fallback: Pygame Standardschriftart
        try:
            log.debug("Attempting to load Pygame default font (Size: %d)", size)
            # pygame.font.Font(None, size) ist die sicherste Fallback-Option
            font = pygame.font.Font(None, size)
            log.info("Successfully loaded Pygame default font (Size: %d)", size)
            return font
        except Exception as final_e:
            # Wenn selbst das fehlschlägt, ist etwas grundlegend falsch
            log.critical("CRITICAL: Could not load any font! Error: %s", final_e, exc_info=True)
            print(f"!!! KRITISCHER FEHLER: Konnte keine Schriftart laden! {final_e} !!!", file=sys.stderr)
            pygame.quit()
            sys.exit("Font loading failed.")

# Definiere die zu verwendenden Schriftarten
log.debug("Loading standard fonts...")
DEFAULT_FONT = get_font(DEFAULT_FONT_SIZE)
DEFAULT_FONT_BOLD = get_font(DEFAULT_FONT_SIZE, bold=True)
DEFAULT_FONT_LARGE = get_font(DEFAULT_FONT_LARGE_SIZE, bold=True)
DEFAULT_FONT_SMALL = get_font(DEFAULT_FONT_SMALL_SIZE)
COORDINATE_FONT = get_font(DEFAULT_FONT_SMALL_SIZE)
TIMER_FONT = get_font(DEFAULT_FONT_SIZE, bold=True)
STATUS_FONT = get_font(DEFAULT_FONT_SIZE)

log.debug("Loading menu fonts...")
MAIN_MENU_TITLE_FONT = get_font(MAIN_MENU_TITLE_FONT_SIZE, bold=True, font_name=MAIN_MENU_TITLE_FONT_NAME)
MAIN_MENU_BUTTON_FONT = get_font(DEFAULT_FONT_SIZE, bold=True)
log.debug("All fonts loaded.")

# --- Bilder ---
IMAGES = {} # Dictionary zum Speichern der geladenen Figurenbilder (Schlüssel: z.B. 'wP', 'bK')
IMAGE_FILE_TYPE = '.png' # Bevorzugter Dateityp (unterstützt Transparenz)
FALLBACK_IMAGE_FILE_TYPE = '.svg' # Fallback (benötigt pygame.image.load_extended)

def load_images():
    """Lädt die Figurenbilder in das IMAGES Dictionary und skaliert sie."""
    log.info("Loading piece images from: %s", IMAGE_DIR)
    pieces = ['wP', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bP', 'bR', 'bN', 'bB', 'bK', 'bQ']
    loaded_count = 0
    for piece in pieces:
        image = None
        image_path = os.path.join(IMAGE_DIR, f'{piece}{IMAGE_FILE_TYPE}')
        fallback_path = os.path.join(IMAGE_DIR, f'{piece}{FALLBACK_IMAGE_FILE_TYPE}')
        log.debug("Attempting to load image for %s...", piece)

        # Prioritize PNG if it exists
        if os.path.exists(image_path):
            log.debug("Trying PNG: %s", image_path)
            try:
                image = pygame.image.load(image_path)
                log.debug(" -> PNG loaded successfully.")
            except Exception as e:
                log.warning(" -> Failed to load PNG for %s: %s", piece, e)
        else:
            log.debug(" -> PNG file not found: %s", image_path)

        # Try SVG as fallback
        if image is None and os.path.exists(fallback_path):
            log.debug("Trying SVG fallback: %s", fallback_path)
            try:
                # load_extended wird für SVG benötigt, falls pygame > 2.0.0.dev8
                # Prüfe, ob die Funktion existiert
                if hasattr(pygame.image, 'load_extended'):
                     image = pygame.image.load_extended(fallback_path)
                     log.debug(" -> SVG loaded successfully using load_extended.")
                else:
                     # Fallback für ältere Pygame-Versionen (könnte fehlschlagen)
                     log.warning("pygame.image.load_extended not available. Trying standard load for SVG (might fail).")
                     image = pygame.image.load(fallback_path)
                     log.debug(" -> SVG loaded successfully using standard load.")
            except Exception as e:
                log.warning(" -> Failed to load SVG for %s: %s", piece, e)
        elif image is None:
            log.debug(" -> SVG file also not found: %s", fallback_path)

        # Process the loaded image (scale and convert)
        if image:
            log.debug("Processing image for %s...", piece)
            try:
                # convert_alpha() ist wichtig für Transparenz
                scaled_image = pygame.transform.smoothscale(image, (SQ_SIZE, SQ_SIZE)).convert_alpha()
                IMAGES[piece] = scaled_image
                loaded_count += 1
                log.debug(" -> Scaled and converted image stored for %s.", piece)
            except Exception as e:
                log.error(" -> Error processing image for %s: %s", piece, e, exc_info=True)
        else:
            log.warning(" -> Could not load any image file for piece %s.", piece)

    log.info("Finished loading images. Loaded %d/%d pieces.", loaded_count, len(pieces))
    if loaded_count != len(pieces):
        missing_pieces = [p for p in pieces if p not in IMAGES]
        log.warning("Not all piece images could be loaded! Missing: %s", missing_pieces)


# --- Sound-Effekte ---
SOUNDS = {} # Dictionary zum Speichern der geladenen Sounds
ENABLE_SOUNDS = True # Sollen Soundeffekte standardmäßig abgespielt werden?
mixer_initialized = False # Wird von main.py gesetzt
log.info("Sound Effects Enabled: %s", ENABLE_SOUNDS)

# Sound-Dateinamen (Basisname, bevorzugte Endung)
SOUND_FILES = {
    'BoardSlide': ('BrettFliegtRein', '.mp3'),
    'PiecePlace': ('Aufsetzen', '.wav'),
    'PieceCapture': ('Schlagen', '.ogg'),
    'game_start': ('game-start', '.wav'),
    'BackgroundMusic': ('background-music', '.mp3'), # Wird separat geladen
    'undo': ('undo', '.wav'),
    'redo': ('redo', '.wav'),
    'Check': ('check', '.wav'), # Geändert von 'check' zu 'Check' für Konsistenz
    'Checkmate': ('checkmate', '.wav'), # Geändert von 'checkmate' zu 'Checkmate'
    'SaveGame' : ('save-game', '.wav'),
    'LoadGame' : ('load-game', '.wav'),
    'game_over': ('game-end', '.wav'),
    'Castle': ('castle', '.wav') # Rochade-Sound hinzugefügt
}

def play_sound(name: str):
    """ Spielt einen Sound ab, wenn Sounds aktiviert und Mixer initialisiert sind. """
    if not ENABLE_SOUNDS:
        # log.debug("Sound '%s' not played (Sounds disabled).", name) # Zu viel Spam?
        return
    if not mixer_initialized:
        log.warning("Attempted to play sound '%s' but mixer is not initialized.", name)
        return
    if name in SOUNDS:
        try:
            SOUNDS[name].play()
            log.debug("Playing sound: %s", name) # Loggt das erfolgreiche Abspielen
        except pygame.error as e:
            log.error("Error playing sound '%s': %s", name, e, exc_info=True)
    else:
        log.warning("Attempted to play sound '%s', but it is not loaded.", name)

def load_sounds():
    """ Lädt die Sounddateien. Der Mixer muss bereits initialisiert sein! """
    if not ENABLE_SOUNDS:
        log.info("Skipping sound loading (Sounds disabled).")
        return

    if not mixer_initialized: # Prüfen, ob der Mixer läuft
        log.warning("Cannot load sounds because Pygame mixer is not initialized.")
        return

    log.info("Loading sound effects from: %s", SOUND_DIR)
    loaded_count = 0
    for name, (filename_base, file_ext) in SOUND_FILES.items():
         # Ignoriere Hintergrundmusik hier, sie wird separat geladen
         if name == 'BackgroundMusic':
             continue

         # Versuche, die Datei mit der bevorzugten Endung zu finden
         filename = f"{filename_base}{file_ext}"
         path = os.path.join(SOUND_DIR, filename)

         # Fallback: Versuche andere gängige Endungen, wenn die bevorzugte nicht existiert
         if not os.path.exists(path):
             log.debug("Sound file %s not found. Trying other extensions...", path)
             found_fallback = False
             for ext in ['.wav', '.ogg', '.mp3']: # Reihenfolge der Fallback-Versuche
                 fallback_filename = f"{filename_base}{ext}"
                 fallback_path = os.path.join(SOUND_DIR, fallback_filename)
                 if os.path.exists(fallback_path):
                     path = fallback_path
                     log.debug("Found fallback sound file: %s", path)
                     found_fallback = True
                     break
             if not found_fallback:
                 log.warning("Could not find any sound file for '%s' (Base: %s) in %s", name, filename_base, SOUND_DIR)
                 continue # Nächsten Sound versuchen

         # Lade den gefundenen Sound
         try:
             SOUNDS[name] = pygame.mixer.Sound(path)
             loaded_count += 1
             log.debug("Sound '%s' loaded from %s", name, path)
         except pygame.error as e:
             log.error("Error loading sound '%s' from %s: %s", name, path, e, exc_info=True)

    # Zähle BackgroundMusic nicht mit bei der Gesamtanzahl
    total_sounds_to_load = len(SOUND_FILES) - 1 if 'BackgroundMusic' in SOUND_FILES else len(SOUND_FILES)
    log.info("Finished loading sound effects. Loaded %d/%d sounds.", loaded_count, total_sounds_to_load)
    if loaded_count == 0 and total_sounds_to_load > 0:
        log.warning("No sound effect files could be loaded.")


# --- Spiel-Logik Einstellungen ---
HIGHLIGHT_LEGAL_MOVES = True # Sollen legale Züge visuell hervorgehoben werden?
FLIP_BOARD_AUTOMATICALLY = True # Soll das Brett automatisch gedreht werden? (Nicht implementiert)
log.info("Highlight Legal Moves: %s", HIGHLIGHT_LEGAL_MOVES)
log.info("Flip Board Automatically: %s", FLIP_BOARD_AUTOMATICALLY)

# --- KI-Einstellungen ---
AI_ENABLED = True           # Ist die KI standardmäßig aktiviert? (wird im Menü gesetzt)
AI_PLAYER = chess.BLACK     # Welche Farbe spielt die KI standardmäßig? (wird im Menü gesetzt)
AI_DEPTH = 2                # Suchtiefe für die Minimax-KI
# Einstellungen für Hintergrund-KI (Neu)
BACKGROUND_AI_DEPTH = 1     # Geringe Tiefe oder Zufallszüge für Hintergrundspiel
BACKGROUND_AI_MOVE_DELAY = 2000 # Millisekunden zwischen Zügen im Hintergrundspiel
log.info("Default AI Settings: Enabled=%s, Player=%s, Depth=%d", AI_ENABLED, "Black" if AI_PLAYER == chess.BLACK else "White", AI_DEPTH)
log.info("Background AI Settings: Depth=%d, Delay=%d ms", BACKGROUND_AI_DEPTH, BACKGROUND_AI_MOVE_DELAY)


# Werte für die Materialbewertung
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}
CHECKMATE = 100000 # Sehr hoher Wert für Schachmatt
STALEMATE = 0      # Wert für Patt
log.info("Piece Values: %s", PIECE_VALUES)
log.info("Checkmate Score: %d, Stalemate Score: %d", CHECKMATE, STALEMATE)

# --- Text-to-Speech (TTS) Einstellungen ---
ENABLE_TTS = False          # Generelle Aktivierung von TTS
TTS_ENGINE = 'Tolk'         # Optionen: 'Tolk' (Windows Screenreader), 'pyttsx3' (plattformunabhängig)
log.info("TTS Enabled: %s, Engine: %s", ENABLE_TTS, TTS_ENGINE)

# --- Hauptmenü Texte ---
MAIN_MENU_TITLE = "Schach"
MAIN_MENU_ITEM_NEW = "NEUES SPIEL"
MAIN_MENU_ITEM_LOAD = "SPIEL LADEN"
MAIN_MENU_ITEM_QUIT = "SPIEL BEENDEN"

# --- Untermenü Texte ---
SUBMENU_TITLE = "MODI WÄHLEN"
SUBMENU_ITEM_LOCAL = "LOKALES SPIEL"
SUBMENU_ITEM_AI = "GEGEN KI"
SUBMENU_ITEM_ONLINE = "ONLINE" # (Noch nicht implementiert)
SUBMENU_ITEM_BACK = "ZURÜCK"

# --- In-Game Menü Titel & Items ---
INGAME_MENU_TITLE = "PAUSE"
INGAME_MENU_ITEM_NEW = "Neues Spiel"
INGAME_MENU_ITEM_SAVE = "Spiel speichern"
INGAME_MENU_ITEM_LOAD = "Spiel laden"
INGAME_MENU_ITEM_MAIN = "Hauptmenü"
INGAME_MENU_ITEM_QUIT = "Spiel beenden"
INGAME_MENU_ITEM_RESUME = "Fortsetzen"


# --- Animationseinstellungen ---
ANIMATION_SPEED = 15 # Frames für die Zuganimation (niedriger = schneller)
MENU_SLIDE_FRAMES = 20 # Frames für die Menü-Schiebe-Animation
BOARD_SLIDE_IN_FRAMES = 30 # Frames für das Einschieben des Bretts
PIECE_SETUP_DELAY_MS = 25  # Millisekunden zwischen dem Platzieren jeder Figur
log.info("Animation Settings: Move=%d frames, Menu Slide=%d frames, Board Slide=%d frames, Piece Delay=%d ms",
         ANIMATION_SPEED, MENU_SLIDE_FRAMES, BOARD_SLIDE_IN_FRAMES, PIECE_SETUP_DELAY_MS)

# Stelle sicher, dass das Save-Verzeichnis existiert
if not os.path.exists(SAVE_DIR):
    log.info("Save directory does not exist. Attempting to create: %s", SAVE_DIR)
    try:
        os.makedirs(SAVE_DIR)
        log.info("Save directory created successfully.")
    except OSError as e:
        log.error("Failed to create save directory '%s': %s", SAVE_DIR, e, exc_info=True)
        # Optional: Programm beenden oder ohne Speichern fortfahren?
        # print(f"FEHLER: Konnte Speicherverzeichnis nicht erstellen: {SAVE_DIR}", file=sys.stderr)

log.info("%s loading complete.", __name__)

