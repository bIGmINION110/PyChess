# -*- coding: utf-8 -*-
"""
Dieses Modul enthält die Logik für die Spielnavigation,
insbesondere das Rückgängigmachen (Undo) und Wiederherstellen (Redo) von Zügen.
Es interagiert mit dem GameState-Objekt, um Züge rückgängig zu machen oder
wiederherzustellen, und verwendet dessen internen Redo-Stack.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import logger
import config
from typing import Optional
from game_state import GameState
# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in navigation_logic.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

def undo_move(gs: 'GameState') -> bool:
    """
    Macht den letzten Zug im Spiel rückgängig, indem es die Methode
    des GameState-Objekts aufruft.

    Args:
        gs (GameState): Der aktuelle Spielzustand, der modifiziert wird.

    Returns:
        bool: True, wenn ein Zug erfolgreich rückgängig gemacht wurde, sonst False.
    """
    log.debug("Attempting to undo last move...")
    # Nutze die undo_move Methode von GameState
    undone_move = gs.undo_move() # Loggt intern

    if undone_move:
        config.play_sound('undo')
        log.info("Undo successful.")
        return True
    else:
        log.info("Undo failed (no moves to undo or error).")
        return False

# --- Redo Funktion ---

def redo_move(gs: 'GameState') -> bool:
    """
    Stellt den zuletzt rückgängig gemachten Zug wieder her, indem es die Methode
    des GameState-Objekts aufruft.

    Args:
        gs (GameState): Der aktuelle Spielzustand, der modifiziert wird.

    Returns:
        bool: True, wenn ein Zug erfolgreich wiederhergestellt wurde, sonst False.
    """
    log.debug("Attempting to redo last undone move...")
    # Nutze die redo_move Methode von GameState
    redone_move = gs.redo_move() # Loggt intern

    if redone_move:
        config.play_sound('redo')
        log.info("Redo successful.")
        return True
    else:
        log.info("Redo failed (no moves to redo or error).")
        return False

# --- Redo-Stack leeren ---

def clear_redo_stack(gs: Optional['GameState'] = None):
    """
    Leert den Redo-Stack im GameState-Objekt.

    Wird normalerweise *innerhalb* von `GameState.make_move` aufgerufen.

    Args:
        gs (GameState, optional): Das GameState-Objekt. Wenn None, wird nichts getan.
    """
    if gs and hasattr(gs, 'clear_redo_stack') and callable(gs.clear_redo_stack):
         gs.clear_redo_stack() # Loggt intern
         log.debug("Explicit call to clear_redo_stack completed (delegated to GameState).")
    elif gs:
         log.warning("clear_redo_stack called, but GameState object has no 'clear_redo_stack' method.")
    else:
         log.warning("clear_redo_stack called without a valid GameState object.")

