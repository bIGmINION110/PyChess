# -*- coding: utf-8 -*-
"""
Dieses Modul kümmert sich um das Speichern und Laden von Spielständen.
Es verwendet das JSON-Format für die Serialisierung des Spielzustands
und Tkinter für die Anzeige von Datei-Dialogen.
"""
import logger, logging
import json # Für JSON Serialisierung/Deserialisierung
import os
import tkinter as tk
from tkinter import filedialog # Für Datei-Dialoge
import time
import datetime # Für Zeitstempel
import chess # Für chess.Board, chess.Move, chess.Piece etc.
import config # Für SAVE_DIR, SAVE_FORMAT_VERSION etc.
from gui.status_display import display_message # Für die Anzeige von Statusmeldungen
from game_state import GameState
from gui import timer_logic # Zum Abrufen der aktuellen Zeit
from typing import Optional, Dict, Any, Tuple # Für Type Hinting

# --- Logger Konfiguration ---
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

# Standard-Verzeichnis für Speicherstände (aus config.py)
if not os.path.exists(config.SAVE_DIR):
    log.warning("Save directory '%s' does not exist. Attempting to create.", config.SAVE_DIR)
    try:
        os.makedirs(config.SAVE_DIR)
        log.info("Save directory created successfully: %s", config.SAVE_DIR)
    except OSError as e:
        log.error("Failed to create save directory '%s': %s", config.SAVE_DIR, e, exc_info=True)

# Standarddateiname mit Zeitstempel
try:
    timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    # Verwende .pcg weiterhin als Endung, obwohl es JSON ist
    DEFAULT_SAVE_FILENAME = f"SaveGame_{timestamp_str}.pcg"
    log.debug("Default save filename generated: %s", DEFAULT_SAVE_FILENAME)
except Exception as e:
    log.error("Failed to generate timestamped default save filename: %s", e, exc_info=True)
    DEFAULT_SAVE_FILENAME = "SaveGame_fallback.pcg" # Fallback

# --- Hilfsfunktionen für Dateidialoge (unverändert) ---

def _get_save_filepath() -> Optional[str]:
    """Zeigt einen "Speichern unter"-Dialog und gibt den gewählten Pfad zurück."""
    log.debug("Opening 'Save As' dialog...")
    root = None
    filepath = None
    try:
        root = tk.Tk()
        root.withdraw() # Verstecke das Hauptfenster von Tkinter
        root.attributes('-topmost', True) # Versuche, Dialog im Vordergrund zu halten
        filepath = filedialog.asksaveasfilename(
            initialdir=config.SAVE_DIR,
            initialfile=DEFAULT_SAVE_FILENAME, # Standarddateiname vorgeben
            title="Spiel speichern unter...",
            defaultextension=".pcg", # Behalte .pcg als Endung
            filetypes=[("PyChess Speicherdatei", "*.pcg"), ("Alle Dateien", "*.*")]
        )
        root.attributes('-topmost', False)
        if filepath:
             log.info("Save path selected: %s", filepath)
             # Stelle sicher, dass die Endung .pcg ist
             if not filepath.lower().endswith(".pcg"):
                 filepath += ".pcg"
                 log.debug("Appended .pcg extension: %s", filepath)
             return filepath
        else:
             log.info("'Save As' dialog cancelled by user.")
             return None
    except Exception as e:
        log.error("Error displaying 'Save As' dialog: %s", e, exc_info=True)
        return None
    finally:
        if root:
            try:
                root.destroy()
                log.debug("Tkinter root window destroyed for save dialog.")
            except tk.TclError as e:
                 log.debug("TclError destroying Tk root (save dialog): %s. Likely already destroyed.", e)
            except Exception as e:
                 log.error("Unexpected error destroying Tk root (save dialog): %s", e, exc_info=True)

def _get_load_filepath() -> Optional[str]:
    """Zeigt einen "Öffnen"-Dialog und gibt den gewählten Pfad zurück."""
    log.debug("Opening 'Load Game' dialog...")
    root = None
    filepath = None
    try:
        root = tk.Tk()
        root.withdraw() # Verstecke das Hauptfenster von Tkinter
        root.attributes('-topmost', True) # Versuche, Dialog im Vordergrund zu halten
        filepath = filedialog.askopenfilename(
            initialdir=config.SAVE_DIR,
            title="Spiel laden",
            filetypes=[("PyChess Speicherdatei", "*.pcg"), ("Alle Dateien", "*.*")]
        )
        root.attributes('-topmost', False)
        if filepath:
             log.info("Load path selected: %s", filepath)
             return filepath
        else:
             log.info("'Load Game' dialog cancelled by user.")
             return None
    except Exception as e:
        log.error("Error displaying 'Load Game' dialog: %s", e, exc_info=True)
        return None
    finally:
        if root:
            try:
                root.destroy()
                log.debug("Tkinter root window destroyed for load dialog.")
            except tk.TclError as e:
                 log.debug("TclError destroying Tk root (load dialog): %s. Likely already destroyed.", e)
            except Exception as e:
                 log.error("Unexpected error destroying Tk root (load dialog): %s", e, exc_info=True)


# --- Serialisierungs- und Deserialisierungsfunktionen ---

def _serialize_game_state(gs: GameState, gui_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Konvertiert den GameState und relevante GUI-Zustände in ein JSON-serialisierbares Dictionary.
    Der Redo-Stack wird NICHT gespeichert.
    """
    log.debug("Serializing game state...")

    # Konvertiere geschlagene Figuren in Symbol-Listen
    captured_by_white_symbols = [f"{'w' if p.color == chess.WHITE else 'b'}{p.symbol().upper()}" for p in gs.get_captured_by_white()]
    captured_by_black_symbols = [f"{'w' if p.color == chess.WHITE else 'b'}{p.symbol().upper()}" for p in gs.get_captured_by_black()]

    # Konvertiere den Move-Stack in UCI-Strings
    move_stack_uci = [move.uci() for move in gs.board.move_stack]

    # Metadaten sammeln
    elapsed_time = 0
    try:
        elapsed_time = timer_logic.get_elapsed_time_ms()
    except Exception as e:
        log.warning("Could not get elapsed time from timer_logic: %s", e)

    is_ai_game = gui_state.get('ai_thinking', False) or config.AI_ENABLED # Prüfe beides
    ai_player_color_str = None
    if is_ai_game:
        ai_player_color_str = 'WHITE' if config.AI_PLAYER == chess.WHITE else 'BLACK'

    save_data = {
        "version": config.SAVE_FORMAT_VERSION,
        "timestamp": datetime.datetime.now().isoformat(),
        "game_state": {
            "fen": gs.board.fen(),
            "move_stack_uci": move_stack_uci,
            # Redo-Stack wird nicht gespeichert
            "captured_by_white_symbols": captured_by_white_symbols,
            "captured_by_black_symbols": captured_by_black_symbols,
        },
        "metadata": {
            "elapsed_time_ms": elapsed_time,
            "is_ai_game": is_ai_game,
            "ai_player_color": ai_player_color_str,
            "ai_depth": config.AI_DEPTH if is_ai_game else None,
            "board_flipped": gui_state.get('board_flipped', False),
            # Füge hier ggf. weitere Metadaten hinzu
        }
    }
    log.debug("Serialization complete.")
    return save_data

def _deserialize_game_state(data: Dict[str, Any]) -> Tuple[Optional[GameState], Optional[Dict[str, Any]]]:
    """
    Konvertiert ein Dictionary (aus JSON geladen) zurück in ein GameState-Objekt und Metadaten.
    """
    log.debug("Deserializing game state from loaded data...")

    # 1. Version prüfen
    loaded_version = data.get("version")
    if loaded_version != config.SAVE_FORMAT_VERSION:
        log.error("Load failed: Save file version mismatch (File: %s, Expected: %s).",
                  loaded_version, config.SAVE_FORMAT_VERSION)
        display_message(f"Ladefehler: Inkompatible Version ({loaded_version})", 'error', duration=5)
        return None, None

    # 2. GameState Daten extrahieren
    gs_data = data.get("game_state", {})
    fen = gs_data.get("fen")
    move_stack_uci = gs_data.get("move_stack_uci", [])
    captured_w_sym = gs_data.get("captured_by_white_symbols", [])
    captured_b_sym = gs_data.get("captured_by_black_symbols", [])

    if not fen:
        log.error("Load failed: FEN string missing in save data.")
        display_message("Ladefehler: Speicherdatei unvollständig (FEN)", 'error', duration=5)
        return None, None

    # 3. GameState Objekt erstellen
    try:
        # Erstelle ein neues, leeres GameState Objekt
        gs = GameState()
        # Setze das Brett aus FEN
        gs.board.set_fen(fen)
        log.debug("Board set from FEN: %s", fen)

        # Stelle den Move-Stack wieder her (wichtig für korrekte FEN/Hash-Werte)
        # Wir müssen die Züge tatsächlich auf dem Board ausführen, um den Stack zu füllen.
        # Das ist potentiell langsam für lange Partien, aber notwendig für Korrektheit.
        temp_board_for_stack = chess.Board() # Starte mit Ausgangsstellung
        valid_moves_replayed = 0
        for uci in move_stack_uci:
            try:
                move = temp_board_for_stack.parse_uci(uci)
                if move in temp_board_for_stack.legal_moves:
                    temp_board_for_stack.push(move)
                    valid_moves_replayed += 1
                else:
                    log.warning("Move %s from save file is not legal at this point during stack reconstruction. Stopping stack replay.", uci)
                    break # Breche ab, wenn ein Zug ungültig wird
            except ValueError:
                log.warning("Invalid UCI string '%s' found in move stack during load. Stopping stack replay.", uci)
                break
        # Übertrage den rekonstruierten Stack auf das Hauptboard des GameState
        if temp_board_for_stack.fen() == gs.board.fen():
             gs.board = temp_board_for_stack # Direkt zuweisen, wenn FEN übereinstimmt
             log.debug("Successfully reconstructed move stack with %d moves.", valid_moves_replayed)
        else:
             log.warning("Reconstructed board FEN (%s) does not match loaded FEN (%s) after replaying %d moves. Move stack might be inconsistent.",
                         temp_board_for_stack.fen(), gs.board.fen(), valid_moves_replayed)
             # Behalte das Board aus dem FEN, aber der Stack ist jetzt leer/inkonsistent

        # Stelle Capture-Listen wieder her
        gs.captured_by_white = []
        for symbol in captured_w_sym:
            try:
                # Symbol ist z.B. 'bP'. chess.Piece.from_symbol braucht nur 'P'.
                piece = chess.Piece.from_symbol(symbol[1])
                piece.color = chess.BLACK # Farbe manuell setzen
                gs.captured_by_white.append(piece)
            except ValueError:
                log.warning("Invalid piece symbol '%s' found in captured_by_white list during load.", symbol)
        log.debug("Reconstructed captured_by_white list with %d pieces.", len(gs.captured_by_white))

        gs.captured_by_black = []
        for symbol in captured_b_sym:
            try:
                piece = chess.Piece.from_symbol(symbol[1])
                piece.color = chess.WHITE # Farbe manuell setzen
                gs.captured_by_black.append(piece)
            except ValueError:
                log.warning("Invalid piece symbol '%s' found in captured_by_black list during load.", symbol)
        log.debug("Reconstructed captured_by_black list with %d pieces.", len(gs.captured_by_black))

        # Redo-Stack bleibt leer
        gs.redo_stack.clear()

        # 4. Metadaten extrahieren
        metadata = data.get("metadata", {})
        log.debug("Deserialization complete.")
        return gs, metadata

    except chess.InvalidFenError:
        log.error("Load failed: Invalid FEN string '%s' found in save data.", fen)
        display_message("Ladefehler: Ungültige Brettstellung in Datei", 'error', duration=5)
        return None, None
    except Exception as e:
        log.error("Unexpected error during GameState deserialization: %s", e, exc_info=True)
        display_message("Ladefehler: Fehler beim Rekonstruieren des Spiels", 'error', duration=5)
        return None, None

# --- Hauptfunktionen zum Speichern und Laden ---

def save_game_state(gs: GameState, gui_state: Dict[str, Any], filename: Optional[str] = None) -> bool:
    """
    Speichert den aktuellen Spielzustand und Metadaten als JSON in einer Datei.

    Args:
        gs (GameState): Das zu speichernde GameState-Objekt.
        gui_state (Dict[str, Any]): Der aktuelle GUI-Zustand für Metadaten.
        filename (str, optional): Der Dateiname (inkl. Pfad) zum Speichern.
                                  Wenn None, wird ein Datei-Dialog angezeigt.

    Returns:
        bool: True bei Erfolg, False bei Fehler oder Abbruch durch Benutzer.
    """
    filepath = filename
    if filepath is None:
        log.debug("No filename provided, opening save dialog.")
        filepath = _get_save_filepath()

    if not filepath: # Benutzer hat abgebrochen oder Dialogfehler
        log.info("Save operation cancelled (no filepath selected).")
        return False

    log.info("Attempting to save game state as JSON to: %s", filepath)
    try:
        # Serialisiere den Zustand
        save_data = _serialize_game_state(gs, gui_state)

        # Schreibe als JSON in die Datei
        with open(filepath, 'w', encoding='utf-8') as f: # 'w' für Write Text (JSON)
            json.dump(save_data, f, indent=4) # indent für Lesbarkeit

        log.info("Game successfully saved as JSON to: %s", filepath)
        config.play_sound('SaveGame') # Sound abspielen bei Erfolg
        display_message(f"Spiel gespeichert: {os.path.basename(filepath)}", 'info', duration=3)
        return True
    except IOError as e:
        log.error("IOError saving game to %s: %s", filepath, e, exc_info=True)
        display_message(f"Speicherfehler (IO): {e}", 'error', duration=5)
        return False
    except TypeError as e:
        log.error("TypeError serializing game state to JSON: %s", e, exc_info=True)
        display_message(f"Speicherfehler (JSON): {e}", 'error', duration=5)
        return False
    except Exception as e:
        log.error("Unexpected error during save operation to %s: %s", filepath, e, exc_info=True)
        display_message(f"Unerwarteter Speicherfehler: {e}", 'error', duration=5)
        return False

def load_game_state(filename: Optional[str] = None) -> Tuple[Optional[GameState], Optional[Dict[str, Any]]]:
    """
    Lädt einen Spielzustand aus einer JSON-Datei.

    Args:
        filename (str, optional): Der Dateiname (inkl. Pfad) zum Laden.
                                  Wenn None, wird ein Datei-Dialog angezeigt.

    Returns:
        Tuple[GameState | None, Dict[str, Any] | None]: Ein Tupel enthält das
                                                        geladene GameState-Objekt und das
                                                        Metadaten-Dictionary bei Erfolg,
                                                        sonst (None, None).
    """
    filepath = filename
    if filepath is None:
        log.debug("No filename provided, opening load dialog.")
        filepath = _get_load_filepath()

    if not filepath: # Benutzer hat abgebrochen oder Dialogfehler
        log.info("Load operation cancelled (no filepath selected).")
        return None, None

    log.info("Attempting to load game state as JSON from: %s", filepath)

    if not os.path.exists(filepath):
        log.error("Load failed: Save file not found at %s", filepath)
        display_message(f"Fehler: Datei nicht gefunden: {os.path.basename(filepath)}", 'error', duration=4)
        return None, None

    try:
        # Lade JSON aus der Datei
        with open(filepath, 'r', encoding='utf-8') as f: # 'r' für Read Text
            loaded_data = json.load(f)

        # Deserialisiere den Zustand
        gs, metadata = _deserialize_game_state(loaded_data)

        if gs:
            log.info("Game successfully loaded from: %s", filepath)
            config.play_sound('LoadGame') # Sound abspielen bei Erfolg
            display_message(f"Spiel geladen: {os.path.basename(filepath)}", 'info', duration=3)
            return gs, metadata
        else:
            # Fehlermeldung wurde bereits in _deserialize_game_state angezeigt/geloggt
            log.error("Deserialization failed for file: %s", filepath)
            return None, None

    except IOError as e:
        log.error("IOError loading game from %s: %s", filepath, e, exc_info=True)
        display_message(f"Ladefehler (IO): {e}", 'error', duration=5)
        return None, None
    except json.JSONDecodeError as e:
        log.error("JSONDecodeError loading game from %s: %s", filepath, e, exc_info=True)
        log.error("The save file might be corrupted or not valid JSON.")
        display_message(f"Ladefehler: Datei beschädigt/ungültig ({os.path.basename(filepath)})", 'error', duration=5)
        return None, None
    except Exception as e:
        log.error("Unexpected error during load operation from %s: %s", filepath, e, exc_info=True)
        display_message(f"Unerwarteter Ladefehler: {e}", 'error', duration=5)
        return None, None
