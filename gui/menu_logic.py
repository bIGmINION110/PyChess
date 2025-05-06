# -*- coding: utf-8 -*-
"""
Dieses Modul verwaltet die Logik für das In-Game-Menü,
einschließlich des Zeichnens der Menüoptionen und der Verarbeitung von
Benutzerinteraktionen (Mausklicks und Tastaturnavigation).
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import os # Für sys.path Manipulation (Fallback)
import logger
import pygame
import config
from game_state import GameState
from typing import TYPE_CHECKING, List, Dict, Tuple, Any, Optional

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in menu_logic.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

# --- Menüdefinition ---
# Verwende Texte aus config für Konsistenz
MENU_ITEMS = [
    {"text": getattr(config, 'INGAME_MENU_ITEM_NEW', "Neues Spiel"), "action": "new_game"},
    {"text": getattr(config, 'INGAME_MENU_ITEM_SAVE', "Spiel speichern"), "action": "save"},
    {"text": getattr(config, 'INGAME_MENU_ITEM_LOAD', "Spiel laden"), "action": "load"},
    {"text": getattr(config, 'INGAME_MENU_ITEM_MAIN', "Hauptmenü"), "action": "main_menu"},
    {"text": getattr(config, 'INGAME_MENU_ITEM_QUIT', "Spiel beenden"), "action": "quit"},
    {"text": getattr(config, 'INGAME_MENU_ITEM_RESUME', "Fortsetzen"), "action": "resume"}
]
log.debug("In-Game Menu Items defined: %s", MENU_ITEMS)

# --- Modul-Variablen ---
menu_item_rects: List[Dict[str, Any]] = [] # Speichert Rects und Aktionen für Klickerkennung
highlighted_index: int = 0 # Index des per Tastatur ausgewählten Eintrags (startet bei 0)
_cached_title_surface: Optional[pygame.Surface] = None # Cache für Titel-Rendering
_cached_title_rect: Optional[pygame.Rect] = None

# --- Hilfsfunktionen für Tastatur-Navigation ---

def get_highlighted_index() -> int:
    """Gibt den aktuell per Tastatur markierten Index zurück."""
    return highlighted_index

def set_highlighted_index(index: int):
    """Setzt den markierten Index sicher innerhalb der Grenzen."""
    global highlighted_index
    num_items = len(MENU_ITEMS)
    if num_items > 0:
        new_index = max(0, min(index, num_items - 1)) # Bleibe innerhalb der Grenzen 0 bis num_items-1
        if new_index != highlighted_index:
             log.debug("Highlight index set manually from %d to %d", highlighted_index, new_index)
             highlighted_index = new_index
    else:
        highlighted_index = 0 # Kein Highlight möglich bei leerem Menü

def move_highlight(direction: int) -> Optional[str]:
    """
    Bewegt die Markierung um 'direction' Schritte (1 für runter, -1 für hoch).
    Implementiert Wrap-Around.
    Gibt den Text des NEUEN markierten Elements für TTS zurück oder None.
    """
    global highlighted_index
    num_items = len(MENU_ITEMS)
    if num_items == 0:
        log.debug("move_highlight called with no menu items.")
        return None

    # Berechne den neuen Index mit Wrap-Around
    new_index = (highlighted_index + direction) % num_items
    if new_index != highlighted_index:
        old_index = highlighted_index
        highlighted_index = new_index
        new_item_text = MENU_ITEMS[highlighted_index]["text"]
        log.debug("Highlight moved (Direction: %d) from index %d to %d ('%s')", direction, old_index, new_index, new_item_text)
        return new_item_text # Text für TTS zurückgeben
    else:
        # log.debug("Highlight not moved (Direction: %d, Index: %d)", direction, highlighted_index) # Kann spammy sein
        return None # Kein Wechsel

def get_action_at_index(index: int) -> Optional[str]:
    """Gibt die Aktion für den Menüpunkt am gegebenen Index zurück."""
    if 0 <= index < len(MENU_ITEMS):
        action = MENU_ITEMS[index]["action"]
        # log.debug("Action at index %d is '%s'", index, action) # Optional
        return action
    else:
        log.warning("Attempted to get action for invalid index: %d (Menu size: %d)", index, len(MENU_ITEMS))
        return None

def reset_highlight():
    """Setzt die Markierung auf das erste Element (Index 0) zurück."""
    global highlighted_index
    log.debug("Resetting menu highlight to index 0 (was %d).", highlighted_index)
    highlighted_index = 0

# --- Zeichnen des Menüs ---

def draw_menu(screen: pygame.Surface, current_highlighted_index: int):
    """
    Zeichnet das In-Game-Menü zentriert auf den Bildschirm, inklusive Titel.
    Hebt das Element am `current_highlighted_index` hervor.

    Args:
        screen (pygame.Surface): Die Hauptzeichenfläche.
        current_highlighted_index (int): Der Index des hervorzuhebenden Elements.
    """
    global menu_item_rects, _cached_title_surface, _cached_title_rect
    menu_item_rects = [] # Zurücksetzen für jede Neuzeichnung

    # --- Menü-Layout und Hintergrund ---
    num_items = len(MENU_ITEMS)
    item_height = 40   # Höhe pro Menüpunkt (etwas kleiner)
    item_spacing = 8   # Abstand zwischen Items (etwas kleiner)
    title_height = 45  # Höhe für den Titel
    v_padding = 15     # Vertikaler Innenabstand oben/unten
    h_padding = 20     # Horizontaler Innenabstand
    menu_width = 300   # Feste Breite

    # Gesamthöhe berechnen
    menu_height = v_padding + title_height + 15 + (num_items * item_height) + (max(0, num_items - 1) * item_spacing) + v_padding
    menu_x = (config.WIDTH - menu_width) // 2
    menu_y = (config.HEIGHT - menu_height) // 2

    # Menü-Hintergrund zeichnen
    try:
        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        menu_bg_color_rgba = config.INGAME_MENU_BACKGROUND_COLOR_RGBA
        menu_surface.fill(menu_bg_color_rgba)
        screen.blit(menu_surface, (menu_x, menu_y))
    except Exception as e_bg:
        log.error("Error drawing menu background: %s", e_bg, exc_info=True)
        # Ohne Hintergrund weiterzeichnen?

    # --- Titel zeichnen ---
    current_y = menu_y + v_padding # Startposition für Inhalt
    # Cache verwenden, um Titel nicht jedes Mal neu zu rendern/positionieren
    # Prüfe auch, ob sich die Position geändert hat (wichtig bei Resize)
    expected_title_centerx = menu_x + menu_width // 2
    if _cached_title_surface is None or _cached_title_rect is None or _cached_title_rect.centerx != expected_title_centerx:
        try:
            title_font = config.MAIN_MENU_TITLE_FONT # Gekringelte Schrift (oder andere?)
            title_text = config.INGAME_MENU_TITLE    # Text aus config (z.B. "PAUSE")
            title_color = config.MAIN_MENU_TITLE_COLOR # Goldene Farbe (oder andere?)
            _cached_title_surface = title_font.render(title_text, True, title_color)
            _cached_title_rect = _cached_title_surface.get_rect(centerx=expected_title_centerx, top=current_y)
            log.debug("In-game menu title re-rendered/re-positioned.")
        except AttributeError as e_cfg_title:
             log.error("Error accessing font/color config for menu title: %s. Using fallbacks.", e_cfg_title)
             _cached_title_surface = None # Cache leeren bei Fehler
             _cached_title_rect = pygame.Rect(menu_x, current_y, menu_width, title_height) # Platzhalter
        except Exception as e_render_title:
            log.error("Error rendering in-game menu title '%s': %s", config.INGAME_MENU_TITLE, e_render_title, exc_info=True)
            _cached_title_surface = None
            _cached_title_rect = pygame.Rect(menu_x, current_y, menu_width, title_height)

    # Titel zeichnen (aus Cache oder direkt)
    if _cached_title_surface and _cached_title_rect:
        screen.blit(_cached_title_surface, _cached_title_rect)
        current_y = _cached_title_rect.bottom + 15 # Y-Position für die Items nach dem Titel (+ Abstand)
    else:
        # Falls Rendern fehlschlug, trotzdem Platz für Titel lassen
        current_y += title_height + 15

    # --- Zeichne Menüpunkte ---
    try:
        font = config.DEFAULT_FONT_BOLD
        text_color_default = config.INGAME_MENU_TEXT_COLOR
        highlight_bg_color = config.INGAME_MENU_HIGHLIGHT_COLOR
        hover_border_color = config.GOLD # Oder eine andere Hover-Farbe
    except AttributeError as e_cfg_items:
        log.error("Error accessing font/color config for menu items: %s. Using fallbacks.", e_cfg_items)
        # Fallback-Werte definieren
        try:
            font = pygame.font.Font(None, 24)
            text_color_default = (200, 200, 200)
            highlight_bg_color = (100, 100, 100)
            hover_border_color = (255, 255, 0)
        except Exception as e_font_fallback_items:
            log.critical("Cannot load even fallback font for menu items: %s", e_font_fallback_items)
            return # Zeichnen abbrechen

    mouse_pos = pygame.mouse.get_pos()

    # Items unterhalb des Titels positionieren
    button_width_ratio = 0.85 # Breite der Buttons relativ zur Menübreite
    button_width = int(menu_width * button_width_ratio)
    button_start_x = menu_x + (menu_width - button_width) // 2 # Zentrierter Start X

    for i, item_data in enumerate(MENU_ITEMS):
        text = item_data["text"]
        action = item_data["action"]

        # Y-Position für diesen Button berechnen
        button_y = current_y + i * (item_height + item_spacing)
        item_rect = pygame.Rect(
            button_start_x,
            button_y,
            button_width,
            item_height
        )
        # Speichere Rect und Aktion für Klickerkennung
        menu_item_rects.append({"rect": item_rect, "action": action})

        is_keyboard_highlighted = (i == current_highlighted_index)
        is_mouse_hovered = item_rect.collidepoint(mouse_pos)

        # --- Hervorhebung zeichnen ---
        try:
            if is_keyboard_highlighted:
                # Solider Hintergrund für Tastatur-Highlight
                highlight_rect_surface = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
                highlight_rect_surface.fill((*highlight_bg_color[:3], 150)) # RGB + Alpha
                screen.blit(highlight_rect_surface, item_rect.topleft)
                current_text_color = config.WHITE # Hellerer Text bei Highlight
            elif is_mouse_hovered:
                 # Rahmen für Maus-Hover (nur wenn nicht schon durch Tastatur hervorgehoben)
                 pygame.draw.rect(screen, hover_border_color, item_rect, 2, border_radius=3) # Dicke 2
                 current_text_color = config.WHITE # Hellerer Text bei Hover
            else:
                 current_text_color = text_color_default
        except Exception as e_highlight:
             log.error("Error drawing highlight for menu item %d: %s", i, e_highlight)
             current_text_color = text_color_default # Fallback

        # --- Text rendern und zentrieren ---
        try:
            text_surface = font.render(text, True, current_text_color)
            text_rect = text_surface.get_rect(center=item_rect.center)
            screen.blit(text_surface, text_rect)
        except Exception as e_text:
             log.error("Error rendering text for menu item %d ('%s'): %s", i, text, e_text)

# --- Klick-Verarbeitung im Menü ---

def handle_menu_click(location: Tuple[int, int], gs: 'GameState', gui_state: Dict[str, Any]) -> Optional[str]:
    """
    Verarbeitet einen Mausklick innerhalb des gezeichneten Menüs.
    Gibt die Aktion des geklickten Elements zurück.

    Args:
        location (tuple): Die (x, y)-Koordinaten des Mausklicks.
        gs (GameState): Der aktuelle Spielzustand (aktuell nicht verwendet hier).
        gui_state (dict): Der GUI-Zustand (aktuell nicht verwendet hier).

    Returns:
        Optional[str]: Die Aktion als String ('quit', 'main_menu', etc.) oder None.
    """
    clicked_action: Optional[str] = None
    for i, item in enumerate(menu_item_rects):
        try:
            item_rect = item["rect"]
            item_action = item["action"]
            if item_rect.collidepoint(location):
                clicked_action = item_action
                set_highlighted_index(i) # Aktualisiere auch Tastatur-Highlight bei Klick
                log.info("Menu item clicked: '%s' (Action: %s, Index: %d)", MENU_ITEMS[i]['text'], clicked_action, i)
                break # Nur das erste getroffene Element berücksichtigen
        except KeyError as e_key:
             log.error("KeyError accessing menu_item_rects data at index %d: %s", i, e_key)
             continue # Nächstes Item versuchen
        except Exception as e_click:
             log.error("Error processing menu click for item %d: %s", i, e_click, exc_info=True)
             continue

    if clicked_action is None:
        log.debug("Menu click at %s did not hit any menu item.", location)

    return clicked_action # Aktion wird in event_handler verarbeitet
