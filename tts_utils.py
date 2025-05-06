# -*- coding: utf-8 -*-
"""
Dieses Modul stellt synchrone Funktionen für die Text-to-Speech (TTS) Ausgabe bereit,
primär über die Tolk-Bibliothek zur Anbindung an Screenreader unter Windows.
Die Sprachausgabe blockiert den aufrufenden Thread.
"""
import logger, logging
import sys # Für kritische Fehler
import time
import atexit
import config
from typing import Optional

# --- Logger Konfiguration (NUR Datei-Logging, mit __name__) ---
log = logger.setup_logger(
    name=__name__,            # Logger-Name ist der Modulname (z.B. 'tts_utils')
    log_file='logs/PyChess.txt', # Loggt in dieselbe Datei wie andere Module
    level=logging.DEBUG,      # Loggt alles ab DEBUG-Level
    console=False,            # KEIN Logging in die Konsole
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)



# --- Globale Variablen für TTS-Engine-Status ---
_tolk_instance: Optional[object] = None # Hält die Tolk-Instanz (oder None)
_tolk_loaded: bool = False             # Zeigt an, ob Tolk erfolgreich geladen wurde
_last_interrupt_time: float = 0.0      # Zeitstempel für letztes Interrupt (für Debounce)
_INTERRUPT_DEBOUNCE_S: float = 0.1     # Mindestabstand für silence() Aufrufe (in Sekunden)

# --- Engine-spezifische Initialisierung und Shutdown (Intern) ---

def _initialize_tolk() -> bool:
    """
    Initialisiert die Tolk-Engine, falls noch nicht geschehen.
    Wird bei Bedarf von `speak()` aufgerufen.

    Returns:
        bool: True bei Erfolg oder wenn bereits initialisiert, False bei Fehlern.
    """
    global _tolk_instance, _tolk_loaded

    if _tolk_loaded:
        # log.debug("Tolk already loaded.") # Optional: Kann spammy sein
        return True

    if not config.ENABLE_TTS or config.TTS_ENGINE != 'Tolk':
        log.debug("Skipping Tolk initialization (TTS disabled or engine is not Tolk).")
        return False

    log.info("Attempting to initialize Tolk engine...")
    try:
        # Dynamischer Import, um Fehler abzufangen, falls Tolk nicht installiert ist
        import Tolk
        _tolk_instance = Tolk # Referenz speichern (obwohl Tolk meist statisch ist)

        # Versuche Tolk zu laden. Dies initialisiert die Verbindung zum Screenreader.
        _tolk_instance.load()
        log.debug("Tolk.load() called.")

        # Prüfen, ob ein Screenreader gefunden wurde
        sr_name = _tolk_instance.detect_screen_reader()
        if sr_name:
            log.info("Tolk loaded successfully. Active Screenreader: %s", sr_name)
            _tolk_loaded = True
            return True
        else:
            log.warning("Tolk loaded, but no active screenreader detected.")
            _tolk_instance.unload() # Wieder entladen, wenn keiner gefunden wurde
            _tolk_instance = None
            _tolk_loaded = False
            return False
    except ImportError:
        log.error("Failed to initialize Tolk: The 'Tolk' module was not found. Please ensure Tolk is installed correctly (Python package and DLL).")
        _tolk_instance = None
        _tolk_loaded = False
        return False
    except Exception as e:
        log.error("Failed to initialize Tolk engine: %s", e, exc_info=True)
        # Versuche trotzdem, unload aufzurufen, falls teilweise geladen
        if _tolk_instance and hasattr(_tolk_instance, 'unload'):
             try: _tolk_instance.unload()
             except: pass
        _tolk_instance = None
        _tolk_loaded = False
        return False

def _shutdown_tolk():
    """Versucht, die Tolk-Engine sauber herunterzufahren, falls sie geladen war."""
    global _tolk_instance, _tolk_loaded
    if not _tolk_loaded or _tolk_instance is None:
        log.debug("Skipping Tolk shutdown (not loaded).")
        return

    log.info("Attempting to shut down Tolk engine...")
    try:
        if hasattr(_tolk_instance, 'unload'):
             _tolk_instance.unload() # Gibt die Verbindung zum Screenreader frei
             log.info("Tolk engine unloaded successfully.")
        else:
             log.warning("Tolk instance found but has no 'unload' method.")
    except Exception as e:
        log.error("Error shutting down Tolk engine: %s", e, exc_info=True)
    finally:
        _tolk_instance = None
        _tolk_loaded = False

# --- Sprachausgabe und Stop (Intern) ---

def _speak_tolk_sync(text: str) -> bool:
    """Interne Funktion zum synchronen Sprechen mit Tolk. Gibt Erfolg zurück."""
    if not _tolk_loaded or _tolk_instance is None:
        log.warning("Cannot speak with Tolk: Engine not loaded.")
        return False

    try:
        log.debug("Speaking with Tolk (sync): '%s'", text)
        # Tolk.speak() ist blockierend, wenn der Screenreader es so implementiert.
        # Der interrupt-Parameter wird hier nicht direkt genutzt,
        # da der Interrupt über _stop_speaking() gesteuert wird.
        success = _tolk_instance.speak(text)
        log.debug("Tolk speak() call finished for '%s' (Success: %s).", text, success)
        # Tolk.speak gibt True zurück, wenn erfolgreich zur Ausgabe angestoßen.
        return success if success is not None else False # Behandle None als False
    except Exception as e:
        log.error("Error during Tolk speak() call: %s", e, exc_info=True)
        # Bei Fehler eventuell Engine als instabil markieren?
        # _tolk_loaded = False # Könnte zu Reinitialisierungsversuchen führen
        return False

def _stop_speaking():
    """Stoppt die aktuelle Sprachausgabe (intern) mit Debouncing."""
    global _last_interrupt_time
    if not _tolk_loaded or _tolk_instance is None:
        return # Nichts zu stoppen

    current_time = time.monotonic()
    if current_time - _last_interrupt_time < _INTERRUPT_DEBOUNCE_S:
        log.debug("Debounce: Skipping repeated Tolk silence() call.")
        # Wichtig: Zeitstempel trotzdem updaten, um eine Kette von Debounces zu ermöglichen
        _last_interrupt_time = current_time
        return

    log.debug("Attempting to stop current Tolk speech output...")
    try:
        # Prüfen, ob STRG gedrückt ist? Nicht mehr nötig, da Interrupt explizit kommt.
        # if pygame.K_LCTRL in pygame.key.get_pressed() or pygame.K_RCTRL in pygame.key.get_pressed():
        if hasattr(_tolk_instance, 'silence'):
            _tolk_instance.silence() # Stoppt die aktuelle Ausgabe des Screenreaders
            log.info("Tolk silence() called.")
            _last_interrupt_time = current_time # Zeitstempel des erfolgreichen Aufrufs speichern
        else:
            log.warning("Tolk instance has no 'silence' method.")

    except Exception as e:
        log.error("Error calling Tolk silence(): %s", e, exc_info=True)
        # Bei Stop-Fehler ist die Engine evtl. instabil -> Neuinitialisierung anfordern?
        # _tolk_loaded = False


# --- Öffentliche Funktionen ---

def speak(text: str, interrupt: bool = False):
    """
    Gibt einen Text synchron über die konfigurierte TTS-Engine aus.

    Args:
        text (str): Der zu sprechende Text.
        interrupt (bool): Wenn True, wird versucht, die aktuelle Sprachausgabe abzubrechen,
                          bevor der neue Text gesprochen wird.
    """
    if not config.ENABLE_TTS:
        return # Tue nichts, wenn TTS deaktiviert ist

    if not text: # Leeren Text nicht ausgeben
        log.debug("Speak called with empty text, ignoring.")
        return

    log.debug("Speak request: '%s' (Interrupt: %s)", text, interrupt)

    # Stelle sicher, dass die Engine initialisiert ist
    if not _initialize_tolk():
        log.warning("Cannot speak: Tolk engine failed to initialize.")
        # Optional: Fehlermeldung anzeigen?
        # status_display.display_message("TTS Fehler: Engine nicht bereit", 'error')
        return

    # Aktuelle Ausgabe stoppen, wenn gewünscht (mit Debouncing)
    if interrupt:
        _stop_speaking()
        # Kurze Pause nach dem Interrupt, damit der Screenreader Zeit hat zu reagieren?
        # time.sleep(0.05) # Kann zu leichten Verzögerungen führen

    # Text synchron ausgeben
    if not _speak_tolk_sync(text):
         log.warning("Failed to speak text: '%s'", text)
         # Optional: Fehlermeldung anzeigen?
         # status_display.display_message("TTS Fehler: Ausgabe fehlgeschlagen", 'error')


def list_available_voices() -> list:
    """
    Listet die verfügbaren Stimmen auf (Platzhalter).
    Tolk verwendet die Systemstimme des Screenreaders, daher ist keine Auswahl möglich.

    Returns:
        List: Eine leere Liste, da Tolk keine Stimmenauswahl bietet.
    """
    if config.TTS_ENGINE == 'Tolk':
        log.info("Voice listing requested for Tolk: Tolk uses the active screenreader's voice. No programmatic listing available.")
    else:
        log.warning("Voice listing not supported for TTS engine: %s", config.TTS_ENGINE)

    return [] # Gib immer eine leere Liste zurück

# --- Initialisierung und Aufräumen ---
# Registriere die Shutdown-Funktion, die beim Beenden des Programms aufgerufen wird
atexit.register(_shutdown_tolk)
log.debug("Registered _shutdown_tolk with atexit.")

# Beispielaufruf (zum Testen des Moduls direkt)
if __name__ == '__main__':
    # Konfigurationswerte für den Test setzen
    config.ENABLE_TTS = True
    config.TTS_ENGINE = 'Tolk'
    # config.DEBUG_MODE = True # Wird jetzt über Logger-Level gesteuert

    # Konsole-Handler hinzufügen, damit man im Test etwas sieht
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _console_handler.setFormatter(_formatter)
    log.addHandler(_console_handler)
    log.setLevel(logging.DEBUG) # Sicherstellen, dass Debug-Meldungen angezeigt werden

    log.info("--- Starting TTS Utils Direct Test ---")

    if config.ENABLE_TTS:
        list_available_voices() # Zeigt den Hinweis für Tolk an

        log.info("Speaking test messages (synchronously)...")
        speak("Hallo Welt! Dies ist Test eins mit Tolk.")
        log.info("...speak call 1 finished.")
        time.sleep(0.5) # Kurze Pause zwischen den Aufrufen

        speak("Dies ist Test zwei, er sollte nach eins kommen.")
        log.info("...speak call 2 finished.")
        time.sleep(0.5)

        log.info("--- Testing Interrupt ---")
        speak("Dieser Satz sollte beginnen, aber schnell unterbrochen werden.")
        log.info("...speak call 3 (long) finished (likely cut short).") # Wird sofort nach dem Aufruf geloggt
        # Warte kurz, damit die Ausgabe *starten* kann, bevor sie unterbrochen wird
        time.sleep(0.6)
        speak("Unterbrechung! Dies ist der neue Text.", interrupt=True)
        log.info("...speak call 4 (interrupt) finished.")
        time.sleep(0.5)

        log.info("--- Testing rapid Debounced Interrupt ---")
        speak("Noch ein langer Satz zum Testen der Unterbrechungsfunktion.")
        log.info("...speak call 5 (long) finished.")
        time.sleep(0.05) # Sehr kurz -> sollte debounced werden
        speak("Kurz.", interrupt=True)
        log.info("...speak call 6 (debounce test 1) finished.")
        time.sleep(0.05) # Sehr kurz -> sollte debounced werden
        speak("Mittel.", interrupt=True)
        log.info("...speak call 7 (debounce test 2) finished.")
        time.sleep(0.3) # Länger -> sollte silence() auslösen
        speak("Letzter Test.", interrupt=True)
        log.info("...speak call 8 (interrupt after debounce) finished.")

        log.info("Waiting a bit for last speech to potentially finish...")
        time.sleep(2) # Warte, um die letzte Ausgabe hörbar zu machen

        log.info("--- TTS Test Finished ---")
    else:
        log.warning("TTS is not enabled in config. Cannot run test.")

    # Shutdown wird durch atexit aufgerufen
    log.info("Exiting direct test script.")

