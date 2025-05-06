# -*- coding: utf-8 -*-
"""
Dieses Modul enthält die Hauptfunktionen zum Zeichnen des Spielzustands,
einschließlich des Bretts, der Figuren, Hervorhebungen, Spielende-Texten
und der Anzeige geschlagener Figuren.
Es koordiniert die Aufrufe an das BoardDisplay-Objekt.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import logger
import pygame
import chess

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in chess_gui.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)



# --- Importiere config (relativ mit Fallback) ---
config = None
try:
    from .. import config # Bevorzugter relativer Import
    config_import_method = "relative"
except ImportError as e_rel_config:
    log.warning("Relativer Import für 'config' fehlgeschlagen (%s). Versuche absoluten Import.", e_rel_config)
    # Verwende den bereits angepassten sys.path vom Logger-Import
    try:
        import config
        config_import_method = "absolute (fallback)"
        log.info("Absoluter Import für 'config' erfolgreich (Fallback).")
    except ImportError as e_abs_config:
        log.critical("Konnte 'config' weder relativ noch absolut importieren (%s)! Ist config.py im Hauptverzeichnis?", e_abs_config)
        sys.exit("Config Import fehlgeschlagen.")
    except Exception as e_other_config:
        log.critical("Unerwarteter Fehler beim Importieren von 'config': %s", e_other_config, exc_info=True)
        sys.exit("Unerwarteter Config-Importfehler.")

if config is None:
     log.critical("Config-Modul konnte nicht geladen werden.")
     sys.exit("Config konnte nicht initialisiert werden.")

log.debug("Config Modul importiert (Methode: %s)", config_import_method)

# Importiere chess_utils relativ
try:
    import chess_utils
except ImportError as e_cu:
    log.critical("Konnte chess_utils nicht relativ importieren! Fehler: %s", e_cu)
    sys.exit("chess_utils Import fehlgeschlagen.")


# Importiere BoardDisplay und GameState nur für Type Hinting
from typing import TYPE_CHECKING, Optional, Tuple, List, Dict, Any
if TYPE_CHECKING:
    # Verwende relative Pfade auch für Type Hinting innerhalb des Pakets
    try:
        from .board_display import BoardDisplay
        from ..game_state import GameState # GameState ist eine Ebene höher
    except ImportError:
         # Fallback für statische Analyse
         from board_display import BoardDisplay
         from game_state import GameState


# --- Globale Variable für skalierte Bilder (Cache) ---
_scaled_captured_images: Dict[str, pygame.Surface] = {}
_CAPTURED_PIECE_SIZE = 20 # Größe der Icons für geschlagene Figuren

def _get_scaled_capture_image(piece_key: str) -> Optional[pygame.Surface]:
    """ Holt oder erstellt ein skaliertes Bild für geschlagene Figuren. """
    global _scaled_captured_images
    if piece_key in _scaled_captured_images:
        return _scaled_captured_images[piece_key]

    original_image = config.IMAGES.get(piece_key)
    if original_image:
        try:
            scaled_image = pygame.transform.smoothscale(original_image, (_CAPTURED_PIECE_SIZE, _CAPTURED_PIECE_SIZE))
            _scaled_captured_images[piece_key] = scaled_image
            log.debug("Scaled image created for captured piece: %s", piece_key)
            return scaled_image
        except Exception as e:
            log.error("Error scaling image for captured piece %s: %s", piece_key, e)
            return None
    else:
        # log.warning("Original image not found for captured piece key: %s", piece_key) # Kann spammy sein
        return None

# --- Zeichenfunktion für geschlagene Figuren ---

def draw_captured_pieces(screen: pygame.Surface, gs: 'GameState', board_display: 'BoardDisplay'):
    """
    Zeichnet die geschlagenen Figuren links und rechts neben dem Brett.
    Zeigt optional den Materialvorteil an.
    """
    try:
        captured_by_white = gs.get_captured_by_white() # Schwarze Figuren
        captured_by_black = gs.get_captured_by_black() # Weiße Figuren

        # Sortiere nach Wert (absteigend) für konsistente Anzeige
        piece_order = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
        captured_by_white.sort(key=lambda p: piece_order.index(p.piece_type) if p.piece_type in piece_order else 99)
        captured_by_black.sort(key=lambda p: piece_order.index(p.piece_type) if p.piece_type in piece_order else 99)

        # Bereiche definieren (Beispiel: rechts und links vom Brett)
        margin = 10 # Abstand zum Brett/Fensterrand
        icon_spacing = 2 # Kleiner Abstand zwischen Icons
        max_icons_per_row = (board_display.board_offset_x - margin * 2) // (_CAPTURED_PIECE_SIZE + icon_spacing)
        if max_icons_per_row <= 0: max_icons_per_row = 1 # Mindestens Platz für 1 Icon

        # --- Geschlagene weiße Figuren (links vom Brett) ---
        start_x_black = margin
        start_y_black = board_display.board_offset_y
        current_x = start_x_black
        current_y = start_y_black
        col_count = 0
        material_black = 0
        for piece in captured_by_black:
            piece_key = chess_utils.get_piece_color_char(piece) + chess_utils.get_piece_symbol_upper(piece)
            img = _get_scaled_capture_image(piece_key)
            if img:
                screen.blit(img, (current_x, current_y))
                current_x += _CAPTURED_PIECE_SIZE + icon_spacing
                col_count += 1
                if col_count >= max_icons_per_row:
                    current_x = start_x_black
                    current_y += _CAPTURED_PIECE_SIZE + icon_spacing
                    col_count = 0
            material_black += config.PIECE_VALUES.get(piece.piece_type, 0)

        # --- Geschlagene schwarze Figuren (rechts vom Brett) ---
        start_x_white = board_display.board_offset_x + board_display.width + margin
        start_y_white = board_display.board_offset_y
        current_x = start_x_white
        current_y = start_y_white
        col_count = 0
        material_white = 0
        for piece in captured_by_white:
            piece_key = chess_utils.get_piece_color_char(piece) + chess_utils.get_piece_symbol_upper(piece)
            img = _get_scaled_capture_image(piece_key)
            if img:
                screen.blit(img, (current_x, current_y))
                current_x += _CAPTURED_PIECE_SIZE + icon_spacing
                col_count += 1
                if col_count >= max_icons_per_row:
                     current_x = start_x_white
                     current_y += _CAPTURED_PIECE_SIZE + icon_spacing
                     col_count = 0
            material_white += config.PIECE_VALUES.get(piece.piece_type, 0)

        # --- Materialvorteil anzeigen (optional) ---
        material_diff = material_white - material_black
        if material_diff != 0:
            advantage_text = f"+{material_diff // 100}" if material_diff > 0 else f"{material_diff // 100}"
            font = config.DEFAULT_FONT_SMALL # Kleinere Schrift
            color = config.WHITE if material_diff > 0 else config.GREY # Weiß für Weiß-Vorteil, Grau für Schwarz-Vorteil
            text_surf = font.render(advantage_text, True, color)

            # Positioniere rechts neben den schwarzen geschlagenen Figuren (oder wo Platz ist)
            advantage_x = start_x_white # Start der rechten Spalte
            advantage_y = board_display.board_offset_y + board_display.height - _CAPTURED_PIECE_SIZE - margin # Unten rechts
            text_rect = text_surf.get_rect(bottomleft=(advantage_x, advantage_y))

            # Kleiner Hintergrund für den Vorteil
            bg_rect = text_rect.inflate(4, 2)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 150))
            screen.blit(bg_surf, bg_rect.topleft)
            screen.blit(text_surf, text_rect)

    except Exception as e:
        log.error("Error drawing captured pieces: %s", e, exc_info=True)


# --- Haupt-Zeichenfunktion ---

def draw_game_state(
    screen: pygame.Surface,
    gs: 'GameState',
    board_display: 'BoardDisplay',
    selected_square_index: Optional[chess.Square] = None, # Der Cursor
    source_square_index: Optional[chess.Square] = None,  # Die aufgenommene Figur
    last_move: Optional[chess.Move] = None,
    board_flipped: bool = False
    ):
    """
    Zeichnet den kompletten aktuellen Spielzustand auf den Bildschirm.
    Hebt Cursor und aufgenommene Figur unterschiedlich hervor.

    Args:
        screen (pygame.Surface): Die Hauptzeichenfläche.
        gs (GameState): Der aktuelle Spielzustand.
        board_display (BoardDisplay): Das Objekt, das für das Zeichnen des Bretts zuständig ist.
        selected_square_index (chess.Square, optional): Index des Cursors (0-63).
        source_square_index (chess.Square, optional): Index der aufgenommenen Figur (0-63).
        last_move (chess.Move, optional): Der letzte ausgeführte Zug zur Hervorhebung.
        board_flipped (bool): Gibt an, ob das Brett gedreht angezeigt wird.
    """
    # log.debug("Drawing game state...") # Sehr spammy

    try:
        # 1. Zeichne das Brett (Felder)
        board_display.draw_board(screen)

        # 2. Zeichne Koordinaten
        board_display.draw_coordinates(screen, flipped=board_flipped)

        # 3. Hebe den letzten Zug hervor (Start- und Endfeld)
        if last_move:
            board_display.highlight_last_move(screen, last_move)

        # 4. Hebe das Feld der "aufgenommenen" Figur hervor
        if source_square_index is not None:
            board_display.highlight_square(screen, source_square_index, config.PICKUP_HIGHLIGHT_COLOR)

        # 5. Hebe das aktuell anvisierte Feld (Cursor) hervor
        #    Zeichne es NACH dem Source-Highlight, falls sie gleich sind
        if selected_square_index is not None:
            board_display.highlight_square(screen, selected_square_index, config.SELECTED_SQUARE_COLOR)

            # 6. Hebe legale Züge hervor (nur wenn eine Figur aufgenommen wurde)
            if config.HIGHLIGHT_LEGAL_MOVES and source_square_index is not None:
                # Zeige legale Züge für die *aufgenommene* Figur
                board_display.highlight_legal_moves(screen, gs.board, source_square_index)

        # 7. Hebe den König hervor, wenn er im Schach steht
        board_display.highlight_check(screen, gs.board)

        # 8. Zeichne die Figuren (über den Hervorhebungen)
        #    Hier wird keine Figur ausgeschlossen, da wir den statischen Zustand zeichnen.
        board_display.draw_pieces(screen, gs.board, exclude_square=None)

        # 9. Zeichne geschlagene Figuren NEBEN dem Brett
        draw_captured_pieces(screen, gs, board_display)

        # 10. Zeichne zusätzliche GUI-Elemente (optional, falls benötigt)
        # draw_player_names(screen, gs)
        # draw_turn_indicator(screen, gs)

    except Exception as e:
        log.error("Error during draw_game_state: %s", e, exc_info=True)
        # Optional: Fehlermeldung auf dem Bildschirm anzeigen?
        # error_font = config.DEFAULT_FONT
        # error_surf = error_font.render("Zeichenfehler!", True, config.RED)
        # screen.blit(error_surf, (10, 10))


# --- Spielende-Anzeige ---

def draw_game_over_text(screen: pygame.Surface, text: str):
    """
    Zeichnet den Spielende-Text zentriert über das Brett.

    Args:
        screen (pygame.Surface): Die Hauptzeichenfläche.
        text (str): Der anzuzeigende Text (z.B. "Schachmatt! Weiß gewinnt.").
    """
    if not text:
        return

    log.debug("Drawing game over text: '%s'", text)
    # Schriftart und Farbe für den Text
    try:
        font = config.DEFAULT_FONT_LARGE # Große Schrift für das Ergebnis
        text_color = config.WHITE        # Helle Farbe für guten Kontrast
        background_color = config.BLACK  # Dunkler Hintergrund für Lesbarkeit
    except AttributeError as e_cfg:
         log.error("Error accessing font/color config for game over text: %s. Using fallbacks.", e_cfg)
         # Fallback-Werte definieren
         try:
             font = pygame.font.Font(None, 36) # Pygame Default Font
             text_color = (255, 255, 255)
             background_color = (0, 0, 0)
         except Exception as e_font_fallback:
              log.critical("Cannot load even fallback font for game over text: %s", e_font_fallback)
              return # Nichts zeichnen, wenn keine Schriftart verfügbar ist

    try:
        # Text rendern (mit Antialiasing)
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))

        # Hintergrundrechteck für den Text zeichnen (etwas größer als der Text)
        bg_padding_x = 20
        bg_padding_y = 10
        bg_rect = text_rect.inflate(bg_padding_x * 2, bg_padding_y * 2)

        # Halbtransparenten Hintergrund zeichnen
        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA) # SRCALPHA für Transparenz
        bg_surface.fill((*background_color, 190)) # Dunkel, halbtransparent (Alpha 0-255)
        screen.blit(bg_surface, bg_rect.topleft)

        # Text über den Hintergrund zeichnen
        screen.blit(text_surface, text_rect)
        log.debug("Game over text drawn successfully.")

    except Exception as e:
        log.error("Error drawing game over text surface or background: %s", e, exc_info=True)
        # Fallback: Nur Text ohne Hintergrund versuchen
        try:
            fallback_font = config.DEFAULT_FONT # Versuche Standard-Schriftart
            txt_surf = fallback_font.render(text, True, config.RED) # Rote Farbe für Fehler
            txt_rect = txt_surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
            screen.blit(txt_surf, txt_rect)
            log.warning("Drew game over text fallback (text only).")
        except Exception as fallback_e:
            log.critical("Critical error drawing game over text fallback: %s", fallback_e, exc_info=True)


# --- Optionale Hilfsfunktionen für zusätzliche GUI-Elemente ---

# def draw_player_names(screen: pygame.Surface, gs: 'GameState'):
#     """ Zeichnet die Namen der Spieler (falls vorhanden) (optional). """
#     pass # Noch nicht implementiert

# def draw_turn_indicator(screen: pygame.Surface, gs: 'GameState'):
#     """ Zeichnet einen Indikator, welcher Spieler am Zug ist (optional). """
#     pass # Noch nicht implementiert
