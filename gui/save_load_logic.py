# -*- coding: utf-8 -*-
"""
Dieses Modul stellt die Schnittstelle zwischen der GUI (Menü, Tastenkürzel)
und der Dateisystemlogik (file_io.py) für das Speichern und Laden von Spielen dar.
Es ruft die entsprechenden Funktionen aus file_io auf und behandelt die Aktualisierung
des Spielzustands und relevanter GUI-Zustände nach dem Laden.
"""
# Standardbibliothek-Imports zuerst
import logging
import logger
import sys # Für kritische Fehler
import chess # Für chess.WHITE/BLACK Konstanten
import config # Für AI Einstellungen
import file_io
from . import timer_logic
from game_state import GameState

# Importiere GameState nur für Type Hinting
from typing import Optional, Dict, Any

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in save_load_logic.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

# --- Speicherfunktion ---

def save_game(gs: 'GameState', gui_state: Dict[str, Any], filename: Optional[str] = None) -> bool:
    """
    Initiert den Speichervorgang für den aktuellen Spielzustand und Metadaten.
    Ruft `file_io.save_game_state` auf, das bei Bedarf einen Dialog anzeigt.

    Args:
        gs (GameState): Der zu speichernde Spielzustand.
        gui_state (Dict[str, Any]): Der aktuelle GUI-Zustand für Metadaten.
        filename (str, optional): Der Dateiname zum Speichern. Wenn None, wird
                                  file_io einen Dialog anzeigen.

    Returns:
        bool: True, wenn das Speichern erfolgreich war, sonst False.
    """
    log.info("Save game process initiated...")
    # Rufe die Funktion auf, die die eigentliche Speicherung (jetzt JSON) und den Dialog übernimmt.
    # file_io.save_game_state loggt Erfolg/Misserfolg und zeigt GUI-Nachrichten an.
    success = file_io.save_game_state(gs, gui_state, filename)

    if success:
        log.info("Save game successful (returned from file_io).")
    else:
        log.warning("Save game failed or was cancelled (returned from file_io).")
    return success

# --- Ladefunktion ---

def load_game(gs: 'GameState', gui_state: Dict[str, Any], filename: Optional[str] = None) -> bool:
    """
    Initiert den Ladevorgang für einen Spielzustand.
    Ruft `file_io.load_game_state` auf, das bei Bedarf einen Dialog anzeigt.
    Aktualisiert das übergebene GameState-Objekt (`gs`) und relevante Teile
    des `gui_state`, wenn das Laden erfolgreich war.

    Args:
        gs (GameState): Der aktuelle Spielzustand, der mit den geladenen Daten
                        überschrieben wird.
        gui_state (Dict[str, Any]): Der aktuelle GUI-Zustand, der mit geladenen
                                    Metadaten aktualisiert wird (z.B. board_flipped).
        filename (str, optional): Der Dateiname zum Laden. Wenn None, wird
                                  file_io einen Dialog anzeigen.

    Returns:
        bool: True, wenn das Laden erfolgreich war und die Zustände aktualisiert wurden,
              sonst False.
    """
    log.info("Load game process initiated...")
    # Rufe die neue Ladefunktion auf, die GameState und Metadaten zurückgibt
    loaded_gs, loaded_metadata = file_io.load_game_state(filename)

    success = False # Standardmäßig nicht erfolgreich
    if loaded_gs and loaded_metadata is not None: # Prüfe beides
        log.info("Game state and metadata loaded successfully from file.")
        # --- Aktualisiere das bestehende GameState-Objekt (`gs`) ---
        try:
            # Kopiere die Kernattribute vom geladenen GameState
            gs.board = loaded_gs.board.copy() # Kopiere das Brett (mit Stack!)
            gs.captured_by_white = loaded_gs.captured_by_white[:] # Kopiere Capture-Listen
            gs.captured_by_black = loaded_gs.captured_by_black[:]
            gs.redo_stack.clear() # Redo-Stack wird beim Laden immer gelöscht

            log.info("Current GameState object updated with loaded data.")

            # --- Aktualisiere relevante GUI-Zustände und Konfigurationen ---
            log.info("Applying loaded metadata...")

            # 1. Timer zurücksetzen und auf geladenen Wert setzen
            elapsed_time_ms = loaded_metadata.get('elapsed_time_ms', 0)
            timer_logic.set_elapsed_time_ms(elapsed_time_ms)
            log.info("Timer set to %d ms.", elapsed_time_ms)
            # Timer wird in main.py gestartet, wenn das Spiel nicht vorbei ist

            # 2. KI-Einstellungen wiederherstellen
            config.AI_ENABLED = loaded_metadata.get('is_ai_game', False)
            ai_color_str = loaded_metadata.get('ai_player_color')
            if config.AI_ENABLED and ai_color_str:
                config.AI_PLAYER = chess.WHITE if ai_color_str == 'WHITE' else chess.BLACK
                config.AI_DEPTH = loaded_metadata.get('ai_depth', config.AI_DEPTH) # Behalte alten Wert bei Fehler
                log.info("AI settings restored: Enabled=True, Player=%s, Depth=%d",
                         ai_color_str, config.AI_DEPTH)
            else:
                config.AI_ENABLED = False
                log.info("AI settings restored: Enabled=False")

            # 3. Brett-Orientierung wiederherstellen
            gui_state['board_flipped'] = loaded_metadata.get('board_flipped', False)
            log.info("Board flipped state restored: %s", gui_state['board_flipped'])

            # 4. Weitere GUI-Status zurücksetzen (wird meist in main.py gemacht)
            # gui_state['menu_active'] = False
            # gui_state['game_over'] = gs.is_game_over()
            # gui_state['player_turn_finished'] = False
            # gui_state['ai_thinking'] = False
            # gui_state['last_move'] = gs.board.peek() if gs.board.move_stack else None

            success = True # Laden und Aktualisieren war erfolgreich

        except Exception as e_update:
            log.error("Error updating current GameState object or applying metadata after loading: %s", e_update, exc_info=True)
            # Optional: GUI-Nachricht anzeigen
            # status_display.display_message("Fehler beim Anwenden des geladenen Spiels.", 'error', duration=5)
            success = False # Aktualisierung fehlgeschlagen
    else:
        log.warning("Load game failed or was cancelled (load_game_state returned None).")
        # GUI-Nachricht wird bereits in file_io angezeigt
        success = False

    return success
