# -*- coding: utf-8 -*-
"""
Logik für das Hauptmenü und das Submenü zum Starten eines neuen Spiels.
Enthält auch die Logik für das im Hintergrund ablaufende, zufällige Schachspiel.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import logger
import pygame
import ai_opponent
from game_state import GameState
from typing import List, Dict, Tuple, Any, Optional
from game_state import GameState
from .board_display import BoardDisplay
from . import tts_integration
import config

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in startup_logic.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False, # Konsole auf False setzen
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

        
# --- Zustandsvariablen für das Hauptmenü und Hintergrundspiel ---
_bg_gs: Optional['GameState'] = None # Verwende 'GameState' als String für Forward Reference
_bg_board_display: Optional[BoardDisplay] = None
_last_bg_move_time: int = 0

# Indizes für Tastatur-Highlighting
_main_menu_highlight_index: int = 0
_submenu_highlight_index: int = 0

# Listen zum Speichern der Button-Rechtecke für Klickerkennung
_main_menu_rects: List[Dict[str, Any]] = []
_submenu_rects: List[Dict[str, Any]] = []

# Definition der Menüpunkte (Texte aus config.py)
# Verwende getattr als Fallback, falls Texte in config fehlen
MAIN_MENU_LAYOUT = [
    {"text": getattr(config, 'MAIN_MENU_ITEM_NEW', "NEUES SPIEL"), "action": "SHOW_NEW_GAME_SUBMENU"},
    {"text": getattr(config, 'MAIN_MENU_ITEM_LOAD', "SPIEL LADEN"), "action": "LOAD"},
    {"text": getattr(config, 'MAIN_MENU_ITEM_QUIT', "SPIEL BEENDEN"), "action": "QUIT"}
]
SUBMENU_LAYOUT = [
    {"text": getattr(config, 'SUBMENU_ITEM_LOCAL', "LOKALES SPIEL"), "action": "START_LOCAL"},
    {"text": getattr(config, 'SUBMENU_ITEM_AI', "GEGEN KI"), "action": "START_AI"},
    {"text": getattr(config, 'SUBMENU_ITEM_ONLINE', "ONLINE"), "action": "START_ONLINE"}, # Führt aktuell zu nichts
    {"text": getattr(config, 'SUBMENU_ITEM_BACK', "ZURÜCK"), "action": "BACK_TO_MAIN"}
]
log.debug("Main Menu Layout defined: %s", MAIN_MENU_LAYOUT)
log.debug("Submenu Layout defined: %s", SUBMENU_LAYOUT)

# --- Hilfsfunktionen für Tastatur-Navigation ---

def _move_highlight(direction: int, current_index: int, menu_layout: List[Dict[str, Any]]) -> Tuple[int, Optional[str]]:
    """
    Bewegt die Markierung um 'direction' Schritte (1 oder -1) für das gegebene Menülayout.
    Gibt den NEUEN Index und den Text des NEUEN markierten Elements für TTS zurück oder None.
    """
    num_items = len(menu_layout)
    if num_items == 0:
        return current_index, None

    new_index = (current_index + direction) % num_items
    if new_index != current_index:
        new_text = menu_layout[new_index]["text"]
        log.debug("Highlight moved (Dir: %d): Index %d -> %d ('%s')", direction, current_index, new_index, new_text)
        return new_index, new_text
    return current_index, None # Kein Wechsel

def _get_action_at_index(index: int, menu_layout: List[Dict[str, Any]]) -> Optional[str]:
    """Gibt die Aktion für den Menüpunkt am gegebenen Index zurück."""
    if 0 <= index < len(menu_layout):
        action = menu_layout[index]["action"]
        # log.debug("Action at index %d is '%s'", index, action) # Optional
        return action
    else:
        log.warning("Attempted to get action for invalid index %d in menu layout.", index)
        return None

def reset_highlight_indices():
    """Setzt die Markierungen für beide Menüs zurück."""
    global _main_menu_highlight_index, _submenu_highlight_index
    log.debug("Resetting menu highlight indices (Main: %d -> 0, Sub: %d -> 0)",
              _main_menu_highlight_index, _submenu_highlight_index)
    _main_menu_highlight_index = 0
    _submenu_highlight_index = 0

# --- Initialisierung ---

def initialize_main_menu():
    """Initialisiert den Zustand für das Hauptmenü und das Hintergrundspiel."""
    global _bg_gs, _bg_board_display, _last_bg_move_time
    log.info("Initializing main menu and background game...")
    try:
        # Stelle sicher, dass GameState erfolgreich importiert wurde und eine Klasse ist
        if GameState is None or not isinstance(GameState, type):
             raise ImportError("GameState class was not loaded correctly.")
        _bg_gs = GameState() # Jetzt wird die Klasse instanziiert
        _bg_gs.reset_game() # Stelle sicher, dass es die Standardposition ist

        # Stelle sicher, dass BoardDisplay erfolgreich importiert wurde
        if BoardDisplay is None:
             raise ImportError("BoardDisplay class not found (likely import error).")
        _bg_board_display = BoardDisplay(config.BOARD_WIDTH, config.BOARD_HEIGHT, config.SQ_SIZE,
                                         config.BOARD_OFFSET_X, config.BOARD_OFFSET_Y)

        _last_bg_move_time = pygame.time.get_ticks()
        reset_highlight_indices() # Highlight zurücksetzen
        log.info("Main menu and background game initialized successfully.")
    except Exception as e:
        log.error("Error during main menu initialization: %s", e, exc_info=True)
        _bg_gs = None # Setze auf None, um Fehler in anderen Funktionen zu vermeiden
        _bg_board_display = None

# --- Hintergrundspiel-Logik ---

def _update_background_game():
    """Führt einen zufälligen KI-Zug im Hintergrundspiel aus, wenn genug Zeit vergangen ist."""
    global _last_bg_move_time
    if _bg_gs is None or _bg_board_display is None or ai_opponent is None:
        # log.debug("Skipping background game update (not initialized or ai_opponent missing).") # Kann spammy sein
        return

    current_time = pygame.time.get_ticks()
    if current_time - _last_bg_move_time > config.BACKGROUND_AI_MOVE_DELAY:
        try:
            if not _bg_gs.is_game_over():
                valid_moves = _bg_gs.get_valid_moves()
                if valid_moves:
                    move = ai_opponent.find_random_move(valid_moves)
                    if move:
                        move_number_before = len(_bg_gs.board.move_stack)
                        if _bg_gs.make_move(move):
                            # Soundeffekt für Hintergrundzug
                            if config.ENABLE_SOUNDS and config.mixer_initialized:
                                try:
                                    _bg_gs.board.pop()
                                    was_capture = _bg_gs.board.is_capture(move)
                                    _bg_gs.board.push(move)
                                    config.play_sound('PieceCapture' if was_capture else 'PiecePlace')
                                except IndexError:
                                     log.warning("IndexError during pop/push for background sound check.")
                                except Exception as e_sound:
                                    log.error("Error checking capture/playing sound for background move %s: %s", move.uci(), e_sound)
                                    if len(_bg_gs.board.move_stack) < move_number_before + 1:
                                        try: _bg_gs.board.push(move)
                                        except: pass
                        # else: make_move fehlgeschlagen (wird von make_move geloggt)
                else: # Keine validen Züge -> Spiel vorbei
                     _bg_gs.reset_game() # Korrigierte Einrückung
            else: # Spiel vorbei -> Reset starten
                _bg_gs.reset_game() # Korrigierte Einrückung

            _last_bg_move_time = current_time
        except Exception as e_bg_update:
             log.error("Error during background game update: %s", e_bg_update, exc_info=True)
             # _bg_gs = None # Optional: Deaktivieren bei Fehler


# --- Zeichenfunktionen ---

def _draw_background_game(screen: pygame.Surface):
    """Zeichnet das zentrierte Hintergrund-Schachbrett und die Figuren."""
    if _bg_board_display and _bg_gs:
        try:
            _bg_board_display.board_offset_x = (config.WIDTH - config.BOARD_WIDTH) // 2
            _bg_board_display.board_offset_y = (config.HEIGHT - config.BOARD_HEIGHT) // 2
            _bg_board_display.draw_board(screen)
            _bg_board_display.draw_pieces(screen, _bg_gs.board)
        except Exception as e_draw_bg:
             log.error("Error drawing background game: %s", e_draw_bg, exc_info=True)

def _draw_menu_panel(screen: pygame.Surface, menu_items: List[Dict[str, Any]], is_submenu: bool, highlighted_item_index: int, override_panel_x: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Zeichnet das Menü-Panel (Titel + Buttons).
    Akzeptiert optional override_panel_x für Animationen.

    Args:
        screen: Die Pygame Surface zum Zeichnen.
        menu_items: Liste der Menüpunkte.
        is_submenu: True für das Submenü.
        highlighted_item_index: Index für Tastatur-Highlight.
        override_panel_x (int, optional): Überschreibt die X-Position für Animationen.

    Returns:
        Liste der Button-Rechtecke und Aktionen.
    """
    button_rects = []
    mouse_pos = pygame.mouse.get_pos()

    # Panel-Dimensionen
    panel_width = 300
    item_height = 45
    item_spacing = 15
    title_height = 60
    v_padding = 30
    num_items = len(menu_items)
    panel_height = title_height + (num_items * item_height) + (max(0, num_items - 1) * item_spacing) + (v_padding * 2)

    # Panel-Position
    default_panel_x = config.WIDTH - panel_width - 30
    panel_x = override_panel_x if override_panel_x is not None else default_panel_x
    panel_y = (config.HEIGHT - panel_height) // 2

    # Panel-Hintergrund zeichnen
    try:
        menu_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        menu_surface.fill(config.MAIN_MENU_BACKGROUND_COLOR_RGBA)
        screen.blit(menu_surface, (panel_x, panel_y))
    except Exception as e_panel_bg:
         log.error("Error drawing menu panel background: %s", e_panel_bg)

    # Titel zeichnen
    current_y = panel_y + v_padding
    try:
        title_font = config.MAIN_MENU_TITLE_FONT
        title_text = config.SUBMENU_TITLE if is_submenu else config.MAIN_MENU_TITLE
        title_surface = title_font.render(title_text, True, config.MAIN_MENU_TITLE_COLOR)
        title_rect = title_surface.get_rect(centerx=panel_x + panel_width // 2, top=current_y)
        screen.blit(title_surface, title_rect)
        current_y = title_rect.bottom + 30 # Nächste Position
    except AttributeError as e_cfg_title:
        log.error("Error accessing font/color config for menu title: %s. Skipping title.", e_cfg_title)
        current_y += title_height # Platz lassen
    except Exception as e_title:
        log.error("Error drawing menu title '%s': %s", title_text, e_title, exc_info=True)
        current_y += title_height # Platz lassen

    # Menüpunkte / Buttons zeichnen
    try:
        button_font = config.MAIN_MENU_BUTTON_FONT
        button_width = panel_width * 0.8
        button_start_x = panel_x + (panel_width - button_width) // 2
    except AttributeError as e_cfg_button:
         log.error("Error accessing font config for menu buttons: %s. Skipping items.", e_cfg_button)
         return button_rects # Leere Liste zurückgeben

    for i, item_data in enumerate(menu_items):
        text = item_data["text"]
        action = item_data["action"]
        button_y = current_y + i * (item_height + item_spacing)
        button_rect = pygame.Rect(button_start_x, button_y, button_width, item_height)
        button_rects.append({"rect": button_rect, "action": action})

        # Hervorhebung
        is_keyboard_highlighted = (i == highlighted_item_index)
        is_mouse_hovered = button_rect.collidepoint(mouse_pos)
        text_color = config.MAIN_MENU_BUTTON_TEXT_COLOR # Standardfarbe

        try:
            if is_keyboard_highlighted:
                highlight_rect_surface = pygame.Surface((button_rect.width, button_rect.height), pygame.SRCALPHA)
                highlight_rect_surface.fill((*config.GOLD[:3], 50)) # Gold mit Alpha
                screen.blit(highlight_rect_surface, button_rect.topleft)
                pygame.draw.rect(screen, config.MAIN_MENU_BUTTON_HOVER_BORDER_COLOR, button_rect, 2, border_radius=5)
                text_color = config.MAIN_MENU_BUTTON_HOVER_TEXT_COLOR
            elif is_mouse_hovered:
                pygame.draw.rect(screen, config.MAIN_MENU_BUTTON_HOVER_BORDER_COLOR, button_rect, 2, border_radius=5)
                text_color = config.MAIN_MENU_BUTTON_HOVER_TEXT_COLOR
        except Exception as e_highlight_draw:
             log.error("Error drawing highlight for button %d: %s", i, e_highlight_draw)

        # Text rendern und zentrieren
        try:
            text_surface = button_font.render(text, True, text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)
        except Exception as e_text_draw:
            log.error("Error drawing button text '%s': %s", text, e_text_draw)

    return button_rects


# --- Frame-basierte Funktionen für main.py ---

def run_main_menu_frame(screen: pygame.Surface, clock: pygame.time.Clock, events: List[pygame.event.Event]) -> Optional[str]:
    """
    Führt einen Frame des Hauptmenüs aus: Zeichnet alles, verarbeitet Events.
    Das Zeichnen des Hintergrundspiels wird jetzt von main.py übernommen.

    Args:
        screen: Die Pygame Surface zum Zeichnen.
        clock: Das Pygame Clock Objekt (aktuell nicht verwendet).
        events: Liste der Pygame Events für diesen Frame.

    Returns:
        Optional[str]: Die nächste Aktion/Zustand oder None.
    """
    global _main_menu_rects, _main_menu_highlight_index

    # 1. Zeichne das Menü-Panel
    _main_menu_rects = _draw_menu_panel(screen, MAIN_MENU_LAYOUT, is_submenu=False, highlighted_item_index=_main_menu_highlight_index)

    # 2. Events verarbeiten
    clicked_action: Optional[str] = None
    for event in events:
        # Mausklick
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, item in enumerate(_main_menu_rects):
                if item["rect"].collidepoint(event.pos):
                    clicked_action = item["action"]
                    _main_menu_highlight_index = i # Update Tastatur-Highlight
                    log.info("Main menu action selected (Mouse): '%s'", clicked_action)
                    break
        # Tastatur
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                new_index, new_text = _move_highlight(-1, _main_menu_highlight_index, MAIN_MENU_LAYOUT)
                if new_index != _main_menu_highlight_index:
                    _main_menu_highlight_index = new_index
                    if new_text and config.ENABLE_TTS: tts_integration.speak_text(new_text, interrupt=False)
            elif event.key == pygame.K_DOWN:
                new_index, new_text = _move_highlight(1, _main_menu_highlight_index, MAIN_MENU_LAYOUT)
                if new_index != _main_menu_highlight_index:
                    _main_menu_highlight_index = new_index
                    if new_text and config.ENABLE_TTS: tts_integration.speak_text(new_text, interrupt=False)
            elif event.key == pygame.K_RETURN: # Enter
                action = _get_action_at_index(_main_menu_highlight_index, MAIN_MENU_LAYOUT)
                if action:
                    clicked_action = action
                    log.info("Main menu action selected (Enter): '%s'", clicked_action)
            elif event.key == pygame.K_s: # TTS Toggle
                 config.ENABLE_TTS = not config.ENABLE_TTS
                 status_text = "Sprachausgabe An" if config.ENABLE_TTS else "Sprachausgabe Aus"
                 log.info("TTS toggled (S): %s", status_text)
                 if config.ENABLE_TTS: tts_integration.speak_text(status_text, interrupt=True)

    # 3. Aktion zurückgeben
    # Highlight Reset passiert jetzt in main.py nach der Animation
    return clicked_action


def run_new_game_submenu_frame(screen: pygame.Surface, clock: pygame.time.Clock, events: List[pygame.event.Event]) -> Optional[str]:
    """
    Führt einen Frame des "Neues Spiel"-Submenüs aus.
    Das Zeichnen des Hintergrundspiels wird jetzt von main.py übernommen.

    Args:
        screen: Die Pygame Surface zum Zeichnen.
        clock: Das Pygame Clock Objekt (aktuell nicht verwendet).
        events: Liste der Pygame Events für diesen Frame.

    Returns:
        Optional[str]: Die nächste Aktion/Zustand oder None.
    """
    global _submenu_rects, _submenu_highlight_index

    # 1. Zeichne das Menü-Panel
    _submenu_rects = _draw_menu_panel(screen, SUBMENU_LAYOUT, is_submenu=True, highlighted_item_index=_submenu_highlight_index)

    # 2. Events verarbeiten
    clicked_action: Optional[str] = None
    for event in events:
        # Mausklick
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, item in enumerate(_submenu_rects):
                if item["rect"].collidepoint(event.pos):
                    clicked_action = item["action"]
                    _submenu_highlight_index = i # Update Tastatur-Highlight
                    log.info("Submenu action selected (Mouse): '%s'", clicked_action)
                    break
        # Tastatur
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                new_index, new_text = _move_highlight(-1, _submenu_highlight_index, SUBMENU_LAYOUT)
                if new_index != _submenu_highlight_index:
                    _submenu_highlight_index = new_index
                    if new_text and config.ENABLE_TTS: tts_integration.speak_text(new_text, interrupt=False)
            elif event.key == pygame.K_DOWN:
                new_index, new_text = _move_highlight(1, _submenu_highlight_index, SUBMENU_LAYOUT)
                if new_index != _submenu_highlight_index:
                    _submenu_highlight_index = new_index
                    if new_text and config.ENABLE_TTS: tts_integration.speak_text(new_text, interrupt=False)
            elif event.key == pygame.K_RETURN: # Enter
                action = _get_action_at_index(_submenu_highlight_index, SUBMENU_LAYOUT)
                if action:
                    clicked_action = action
                    log.info("Submenu action selected (Enter): '%s'", clicked_action)
            elif event.key == pygame.K_ESCAPE: # ESC im Submenü geht zurück
                 clicked_action = "BACK_TO_MAIN"
                 log.info("Back to main menu requested (ESC from submenu).")
            elif event.key == pygame.K_s: # TTS Toggle
                 config.ENABLE_TTS = not config.ENABLE_TTS
                 status_text = "Sprachausgabe An" if config.ENABLE_TTS else "Sprachausgabe Aus"
                 log.info("TTS toggled (S): %s", status_text)
                 if config.ENABLE_TTS: tts_integration.speak_text(status_text, interrupt=True)

    # Online Modus führt zurück zum Hauptmenü (da nicht implementiert)
    if clicked_action == "START_ONLINE":
        log.warning("Online mode selected but not implemented. Returning to main menu.")
        clicked_action = "BACK_TO_MAIN" # Signalisiert Rückkehr

    # Highlight Reset passiert jetzt in main.py nach der Animation
    return clicked_action
