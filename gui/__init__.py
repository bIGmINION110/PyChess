# -*- coding: utf-8 -*-
"""
Initialisierungsdatei für das gui-Paket.
Importiert die Submodule und definiert __all__ für eine saubere Schnittstelle.
"""
from . import *
import logging
import logger

log = logger.setup_logger(
    name=__name__,            # Logger-Name ist der Paketname (z.B. 'gui')
    log_file='logs/PyChess.txt', # Loggt in dieselbe Datei wie andere Module
    level=logging.DEBUG,      # Loggt alles ab DEBUG-Level
    console=False,            # KEIN Logging in die Konsole
)

__all__ = [
    "board_display", "chess_gui", "fullscreen_logic", "menu_logic",
    "navigation_logic", "save_load_logic", "startup_logic",
    "status_display", "timer_logic", "tts_integration"
]
log.debug("Paket '%s' initialisiert und __all__ definiert.", __name__)
