# -*- coding: utf-8 -*-
"""
Dieses Modul enthält die Logik zum Umschalten zwischen Fenster- und Vollbildmodus.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import logger
import pygame
import config

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in fullscreen_logic.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)


# --- Globale Variablen für den Vollbildstatus ---
is_fullscreen: bool = False
# Speichere die ursprünglichen Fensterdimensionen für die Rückkehr aus dem Vollbildmodus
# Initialisiere mit Werten aus config
original_width: int = config.WIDTH
original_height: int = config.HEIGHT
log.debug("Initial fullscreen state: %s, Original dimensions stored: %dx%d", is_fullscreen, original_width, original_height)

def toggle_fullscreen(screen: pygame.Surface) -> pygame.Surface:
    """
    Schaltet den Anzeigemodus zwischen Fenster und Vollbild um.

    WICHTIG: Diese Funktion gibt eine *neue* Surface zurück, wenn der Modus
    geändert wird. Der Aufrufer muss diese neue Surface verwenden!

    Args:
        screen (pygame.Surface): Die aktuelle Hauptzeichenfläche.

    Returns:
        pygame.Surface: Die (potenziell neue) Zeichenfläche nach dem Umschalten.
    """
    global is_fullscreen, original_width, original_height
    new_screen = screen # Standardmäßig die alte Surface zurückgeben, falls Fehler auftreten

    # Aktuelle Dimensionen und Flags der übergebenen Surface holen
    current_w = screen.get_width()
    current_h = screen.get_height()
    current_flags = screen.get_flags() # Holt Flags wie RESIZABLE, FULLSCREEN etc.
    log.debug("Toggling fullscreen. Current state: Fullscreen=%s, Size=%dx%d, Flags=%d",
              is_fullscreen, current_w, current_h, current_flags)

    if is_fullscreen:
        # --- Von Vollbild zu Fenster wechseln ---
        log.info("Switching to windowed mode...")
        try:
            # Setze die gespeicherten ursprünglichen Dimensionen und füge RESIZABLE hinzu, entferne FULLSCREEN
            new_flags = (current_flags & ~pygame.FULLSCREEN) | pygame.RESIZABLE
            log.debug("Setting windowed mode: Size=%dx%d, Flags=%d", original_width, original_height, new_flags)
            new_screen = pygame.display.set_mode((original_width, original_height), new_flags)
            is_fullscreen = False
            log.info("Windowed mode activated (%dx%d).", original_width, original_height)
        except pygame.error as e:
            log.error("Error switching to windowed mode: %s", e, exc_info=True)
            # Gib die alte (Vollbild-)Surface zurück, um Absturz zu vermeiden. Status bleibt is_fullscreen=True.
            return screen
    else:
        # --- Von Fenster zu Vollbild wechseln ---
        log.info("Switching to fullscreen mode...")
        try:
            # Speichere aktuelle Dimensionen als "original" für die Rückkehr
            original_width = current_w
            original_height = current_h
            log.debug("Stored original window dimensions: %dx%d", original_width, original_height)

            # Ermittle die Desktop-Auflösung für den Vollbildmodus
            info = pygame.display.Info()
            fullscreen_width = info.current_w
            fullscreen_height = info.current_h
            log.debug("Detected desktop resolution: %dx%d", fullscreen_width, fullscreen_height)

            # Setze den Vollbildmodus mit Desktop-Auflösung und FULLSCREEN-Flag
            # Entferne RESIZABLE, da es im Vollbild oft Probleme macht
            new_flags = (current_flags | pygame.FULLSCREEN) & ~pygame.RESIZABLE
            log.debug("Setting fullscreen mode: Size=%dx%d, Flags=%d", fullscreen_width, fullscreen_height, new_flags)
            new_screen = pygame.display.set_mode((fullscreen_width, fullscreen_height), new_flags)
            is_fullscreen = True
            log.info("Fullscreen mode activated (%dx%d).", fullscreen_width, fullscreen_height)
        except pygame.error as e:
            log.error("Error switching to fullscreen mode: %s", e, exc_info=True)
            # Versuche, zum ursprünglichen Fenstermodus zurückzukehren
            try:
                log.warning("Attempting to revert to previous windowed mode...")
                # Verwende die gerade gespeicherten original_width/height und die alten Flags ohne FULLSCREEN
                revert_flags = (current_flags & ~pygame.FULLSCREEN) | pygame.RESIZABLE
                new_screen = pygame.display.set_mode((original_width, original_height), revert_flags)
                is_fullscreen = False # Sicherstellen, dass Status korrekt ist
                log.info("Successfully reverted to windowed mode (%dx%d) after fullscreen error.", original_width, original_height)
            except Exception as e_reset:
                log.critical("CRITICAL: Could not revert to windowed mode after failed fullscreen attempt: %s", e_reset, exc_info=True)
                # Hier ist es schwierig, weiterzumachen. Gib die alte Surface zurück.
                return screen

    # Gib die (möglicherweise neue) Surface zurück
    log.debug("toggle_fullscreen returning new screen surface.")
    return new_screen

def get_fullscreen_state() -> bool:
    """
    Gibt zurück, ob das Spiel aktuell im Vollbildmodus ist.

    Returns:
        bool: True, wenn im Vollbildmodus, sonst False.
    """
    # log.debug("get_fullscreen_state returning: %s", is_fullscreen) # Kann spammy sein
    return is_fullscreen

