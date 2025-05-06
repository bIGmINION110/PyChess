# -*- coding: utf-8 -*-
"""
Dieses Modul verwaltet die Spielzeit als einfachen, hochzählenden Timer.
Es zeigt die seit Spielbeginn vergangene Zeit an.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import logger
import pygame
import config

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in timer_logic.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False, # Konsole auf False setzen
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

# --- Timer-Zustandsvariablen (Modul-Level) ---
# Zeitpunkt (in Pygame Ticks), zu dem der Timer gestartet/fortgesetzt wurde
_start_tick: int = 0
# Gesamte vergangene Zeit in Millisekunden, bevor der Timer zuletzt gestoppt wurde
_elapsed_ms_before_pause: int = 0
# Flag, ob der Timer gerade aktiv läuft
_is_running: bool = False

# --- Timer-Steuerungsfunktionen ---

def start_game_timer():
    """
    Startet oder setzt den Spielzeit-Timer fort.
    Wenn der Timer bereits läuft, passiert nichts.
    """
    global _is_running, _start_tick
    if not _is_running:
        _is_running = True
        # Setze den Startpunkt für die aktuelle Laufzeitmessung
        _start_tick = pygame.time.get_ticks()
        log.info("Game timer started/resumed at tick %d.", _start_tick)
    # else:
    #    log.debug("Game timer already running, start_game_timer() ignored.") # Optional

def stop_game_timer():
    """
    Stoppt (pausiert) den Spielzeit-Timer.
    Die bis jetzt vergangene Zeit wird gespeichert.
    """
    global _is_running, _elapsed_ms_before_pause, _start_tick
    if _is_running:
        # Berechne die Zeit, die seit dem letzten Start/Resume vergangen ist
        current_ticks = pygame.time.get_ticks()
        elapsed_this_run = current_ticks - _start_tick
        # Addiere sie zur bisherigen Gesamtzeit
        _elapsed_ms_before_pause += elapsed_this_run
        _is_running = False
        _start_tick = 0 # Zurücksetzen, da nicht mehr relevant bis zum nächsten Start
        log.info("Game timer stopped. Elapsed this run: %d ms. Total paused time: %d ms.",
                 elapsed_this_run, _elapsed_ms_before_pause)
    # else:
    #    log.debug("Game timer already stopped, stop_game_timer() ignored.") # Optional

def reset_game_timer():
    """
    Setzt den Spielzeit-Timer komplett zurück auf 00:00 und stoppt ihn.
    """
    global _is_running, _elapsed_ms_before_pause, _start_tick
    log.info("Resetting game timer (Running: %s, Paused time: %d ms).",
             _is_running, _elapsed_ms_before_pause)
    _is_running = False
    _elapsed_ms_before_pause = 0
    _start_tick = 0

def get_elapsed_time_ms() -> int:
    """
    Gibt die gesamte seit dem ersten Start vergangene Spielzeit in Millisekunden zurück.
    Berücksichtigt Pausen.

    Returns:
        int: Vergangene Spielzeit in Millisekunden.
    """
    if _is_running:
        # Aktuell laufende Zeit + bisher gespeicherte Zeit
        current_run_time = pygame.time.get_ticks() - _start_tick
        total_elapsed = _elapsed_ms_before_pause + current_run_time
        # log.debug("Timer running. Elapsed: %d (paused) + %d (current) = %d ms",
        #           _elapsed_ms_before_pause, current_run_time, total_elapsed) # Spammy
        return total_elapsed
    else:
        # Timer läuft nicht, gib nur die gespeicherte Zeit zurück
        # log.debug("Timer stopped. Returning paused time: %d ms", _elapsed_ms_before_pause) # Spammy
        return _elapsed_ms_before_pause

def set_elapsed_time_ms(elapsed_ms: int):
    """
    Setzt die gespeicherte vergangene Zeit. Nützlich beim Laden eines Spiels.
    Der Timer bleibt gestoppt, bis start_game_timer() aufgerufen wird.

    Args:
        elapsed_ms (int): Die zu setzende Zeit in Millisekunden.
    """
    global _is_running, _elapsed_ms_before_pause, _start_tick
    log.info("Setting elapsed time to %d ms (Timer running state: %s -> False).", elapsed_ms, _is_running)
    _is_running = False # Timer wird immer gestoppt, wenn Zeit gesetzt wird
    _elapsed_ms_before_pause = max(0, elapsed_ms) # Stelle sicher, dass die Zeit nicht negativ ist
    _start_tick = 0 # Startpunkt ist irrelevant, wenn Zeit manuell gesetzt wird

def format_time(time_ms: int) -> str:
    """
    Formatiert die Zeit in Millisekunden in einen String (HH:MM:SS oder MM:SS).

    Args:
        time_ms (int): Zeit in Millisekunden.

    Returns:
        str: Formatierter Zeitstring (z.B. "05:12" oder "01:15:33").
    """
    if time_ms < 0:
        log.warning("format_time received negative value: %d. Using 0.", time_ms)
        time_ms = 0
    total_seconds = time_ms // 1000 # Umwandlung in ganze Sekunden

    # Berechne Stunden, Minuten und Sekunden
    seconds = total_seconds % 60
    total_minutes = total_seconds // 60
    minutes = total_minutes % 60
    hours = total_minutes // 60

    # Formatieren mit führenden Nullen
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

# --- Zeichenfunktion ---

def draw_game_timer(screen: pygame.Surface):
    """
    Zeichnet den aktuellen Stand des Spielzeit-Timers auf den Bildschirm.

    Args:
        screen (pygame.Surface): Die Hauptzeichenfläche.
    """
    # log.debug("Drawing game timer...") # Sehr spammy
    try:
        # Hole die aktuell vergangene Zeit
        elapsed_ms = get_elapsed_time_ms()
        # Formatiere sie
        time_str = format_time(elapsed_ms)

        # Rendere den Text
        font = config.TIMER_FONT
        text_color = config.TIMER_TEXT_COLOR
        text_surface = font.render(time_str, True, text_color)

        # Positioniere den Text oben links (Koordinaten aus config)
        text_rect = text_surface.get_rect(topleft=(config.TIMER_POS_X, config.TIMER_POS_Y))

        # Hintergrund für besseren Kontrast
        bg_rect = text_rect.inflate(6, 4) # Kleiner Rand
        # Zeichne einen halbtransparenten schwarzen Hintergrund
        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 150)) # Schwarz mit Alpha
        screen.blit(bg_surface, bg_rect.topleft)

        # Zeichne den Text über den Hintergrund
        screen.blit(text_surface, text_rect)

    except AttributeError as e_cfg:
         log.error("Error accessing font/color config for timer display: %s. Using fallbacks.", e_cfg)
         # Zeichne einfachen Text als Fallback
         try:
             fallback_font = pygame.font.Font(None, 18)
             fallback_surf = fallback_font.render(format_time(get_elapsed_time_ms()), True, (255, 0, 0)) # Rot als Fehlerindikator
             fallback_rect = fallback_surf.get_rect(topleft=(10, 10)) # Feste Position
             screen.blit(fallback_surf, fallback_rect)
         except Exception as e_fallback_draw:
              log.critical("Cannot draw even fallback timer text: %s", e_fallback_draw)
    except Exception as e:
        log.error("Error drawing game timer: %s", e, exc_info=True)

def get_formatted_time() -> str:
    """
    Gibt die aktuell formatierte Zeit als String zurück (für TTS).

    Returns:
        str: Formatierte Zeit (MM:SS oder HH:MM:SS).
    """
    try:
        return format_time(get_elapsed_time_ms())
    except Exception as e:
        log.error("Error getting formatted time: %s", e, exc_info=True)
        return "Zeitfehler" # Fallback-String

