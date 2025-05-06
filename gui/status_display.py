# -*- coding: utf-8 -*-
"""
Dieses Modul verwaltet die Anzeige von Statusnachrichten im Spiel,
wie z.B. Fehler, der letzte Zug oder wer am Zug ist.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import time
import logger
import pygame
import chess
import chess_utils
import config
from game_state import GameState
from typing import Optional

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in status_display.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

# --- Modul-Zustandsvariablen ---
_current_message: str = ""
_message_type: str = 'default' # 'default', 'move', 'error', 'info', 'warning'
_message_start_time: float = 0.0
_message_duration: Optional[float] = None # in Sekunden
_default_message: str = "Weiß am Zug" # Wird von update_default_status gesetzt

def update_default_status(gs: 'GameState'):
    """
    Aktualisiert die Standardnachricht (wer am Zug ist oder Spielende),
    basierend auf dem Spielzustand.
    """
    global _default_message
    try:
        if gs.is_game_over():
            result_text = chess_utils.get_game_over_text(gs.board)
            _default_message = result_text if result_text else "Spiel beendet"
            log.debug("Default status updated to: Game Over ('%s')", _default_message)
        else:
            turn_color = "Weiß" if gs.board.turn == chess.WHITE else "Schwarz"
            _default_message = f"{turn_color} am Zug"
            # log.debug("Default status updated to: '%s'", _default_message) # Kann spammy sein
    except Exception as e:
        log.error("Error updating default status: %s", e, exc_info=True)
        _default_message = "Statusfehler" # Fallback

def display_message(message: str, msg_type: str = 'info', duration: Optional[float] = None):
    """
    Zeigt eine temporäre Nachricht an (z.B. letzter Zug, Fehler, Info).

    Args:
        message (str): Die anzuzeigende Nachricht.
        msg_type (str): Der Typ der Nachricht ('move', 'error', 'info', 'warning', 'debug').
        duration (float, optional): Wie lange die Nachricht angezeigt werden soll (in Sekunden).
                                    Wenn None, wird sie angezeigt, bis eine neue Nachricht kommt
                                    oder der Zustand wechselt.
    """
    global _current_message, _message_type, _message_start_time, _message_duration

    # Logge die eingehende Nachricht (unabhängig davon, ob sie angezeigt wird)
    log_level = logging.INFO # Standard für 'info', 'move'
    if msg_type == 'error':
        log_level = logging.ERROR
    elif msg_type == 'warning':
        log_level = logging.WARNING
    elif msg_type == 'debug':
        log_level = logging.DEBUG

    log.log(log_level, "Status Display Request: '%s' (Type: %s, Duration: %s)", message, msg_type, duration)

    # Priorisierung: Fehler überschreiben alles außer neuere Fehler.
    # Andere Nachrichten überschreiben nur, wenn keine Fehlermeldung aktiv ist.
    can_overwrite = True
    if _message_type == 'error' and msg_type != 'error':
        # Aktuell wird ein Fehler angezeigt, neue Nachricht ist kein Fehler -> nicht überschreiben
        log.debug("Skipping display of '%s' (Type: %s) because an error message is active.", message, msg_type)
        can_overwrite = False

    if can_overwrite:
        _current_message = message
        _message_type = msg_type
        _message_start_time = time.monotonic() # Verwende monotonic für Zeitmessung
        _message_duration = duration
        log.debug("Status Display Updated: '%s' (Type: %s, Duration: %s)", _current_message, _message_type, _message_duration)
    # else: Nachricht wurde nicht angezeigt, aber geloggt.

def draw_status_display(screen: pygame.Surface):
    """
    Zeichnet die aktuelle Statusnachricht auf den Bildschirm.
    Wechselt zur Standardnachricht zurück, wenn die temporäre Nachricht abgelaufen ist.
    """
    global _current_message, _message_type, _message_start_time, _message_duration, _default_message

    display_text = ""
    text_color = config.STATUS_TEXT_COLOR # Standardfarbe

    # Prüfen, ob eine temporäre Nachricht aktiv ist und ob sie abgelaufen ist
    is_temporary_message_active = (_message_type != 'default')
    is_timed_out = False
    if is_temporary_message_active and _message_duration is not None:
        if time.monotonic() - _message_start_time > _message_duration:
            log.debug("Temporary status message '%s' (Type: %s) timed out.", _current_message, _message_type)
            is_timed_out = True
            # Setze zurück auf Default, wenn abgelaufen
            _message_type = 'default'
            _current_message = "" # Leere temporäre Nachricht

    # Entscheide, welche Nachricht angezeigt wird und welche Farbe
    current_display_type = _message_type # Merke dir den aktuellen Typ für die Farbzuweisung

    if current_display_type != 'default':
         display_text = _current_message
    else: # 'default' oder abgelaufen
         display_text = _default_message
         # Stelle sicher, dass der Typ auch 'default' ist, falls er abgelaufen ist
         _message_type = 'default' # Setze den internen Status zurück

    # Farbe basierend auf dem *aktuell anzuzeigenden* Typ setzen
    if current_display_type == 'error':
        text_color = config.STATUS_ERROR_COLOR
    elif current_display_type == 'warning':
        text_color = config.YELLOW # Beispiel: Gelb für Warnungen
    # elif current_display_type == 'info': text_color = config.STATUS_TEXT_COLOR
    # elif current_display_type == 'move': text_color = config.STATUS_TEXT_COLOR
    # elif current_display_type == 'debug': text_color = config.GREY # Beispiel: Grau für Debug
    else: # default
        text_color = config.STATUS_TEXT_COLOR


    # --- Text rendern und zeichnen ---
    if display_text: # Nur zeichnen, wenn Text vorhanden ist
        try:
            font = config.STATUS_FONT
            text_surface = font.render(display_text, True, text_color)

            # Position aus config holen (X ist Mitte, Y ist oben)
            # Verwende midtop, um den Text horizontal zu zentrieren
            text_rect = text_surface.get_rect(midtop=(config.STATUS_POS_X, config.STATUS_POS_Y))

            # Optional: Hintergrund für besseren Kontrast
            bg_rect = text_rect.inflate(6, 4) # Kleiner Rand um den Text
            # Zeichne einen halbtransparenten schwarzen Hintergrund
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 150)) # Schwarz mit Alpha
            screen.blit(bg_surface, bg_rect.topleft)

            # Zeichne den Text über den Hintergrund
            screen.blit(text_surface, text_rect)

        except AttributeError as e_cfg:
             log.error("Error accessing font/color config for status display: %s. Using fallbacks.", e_cfg)
             # Zeichne einfachen Text als Fallback
             try:
                 fallback_font = pygame.font.Font(None, 18)
                 fallback_surf = fallback_font.render(display_text, True, (255, 0, 0)) # Rot als Fehlerindikator
                 fallback_rect = fallback_surf.get_rect(midtop=(config.WIDTH // 2, 10)) # Feste Position oben mittig
                 screen.blit(fallback_surf, fallback_rect)
             except Exception as e_fallback_draw:
                  log.critical("Cannot draw even fallback status text: %s", e_fallback_draw)
        except Exception as e:
            log.error("Error drawing status display: %s", e, exc_info=True)

