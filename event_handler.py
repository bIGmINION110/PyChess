# -*- coding: utf-8 -*-
"""
Verarbeitet Benutzereingaben (Maus, Tastatur) im Hauptspielzustand ('GAME').
Verwaltet die Figurenauswahl, Zugversuche und Interaktionen mit dem In-Game-Menü.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import logger
import config
import animations
from typing import Optional, List, Dict, Any
from pygame.event import Event
from game_state import GameState
import pygame, chess
from gui.board_display import BoardDisplay
# Importiere alle GUI-Module, um sicherzustellen, dass sie verfügbar sind
from gui import menu_logic, save_load_logic, navigation_logic, tts_integration, timer_logic, status_display

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in event_handler.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False, # Konsole auf False setzen
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

# --- Zustand der Tastatureingabe ---
selected_square_index: Optional[chess.Square] = chess.E4 # Cursor startet auf e4
source_square_selected: Optional[chess.Square] = None # Feld der "aufgenommenen" Figur

# Modulvariable für BoardDisplay (wird von _execute_move benötigt)
_board_display_ref: Optional[BoardDisplay] = None

# --- Haupt-Event-Handling-Funktion für den Spielzustand ---

def handle_events(screen: pygame.Surface, gs: 'GameState', board_display: 'BoardDisplay', gui_state: Dict[str, Any], events: List['Event']) -> Optional[str]:
    """
    Verarbeitet Pygame-Ereignisse für den 'GAME'-Zustand.
    Implementiert Tastatursteuerung mit Aufnehmen/Absetzen und TTS-Feedback.
    Gibt eine Aktions-Zeichenkette zurück, wenn ein Zustandswechsel erforderlich ist (z.B. 'QUIT', 'TO_MAIN_MENU').
    """
    global selected_square_index, source_square_selected, _board_display_ref
    _board_display_ref = board_display # Referenz speichern für _execute_move

    action_result: Optional[str] = None # Rückgabewert für Aktionen

    for event in events:
        # --- Mausereignisse ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            location = pygame.mouse.get_pos()
            log.debug("Mouse button down at %s", location)

            # --- Klick im In-Game-Menü ---
            if gui_state.get('menu_active', False):
                menu_action = menu_logic.handle_menu_click(location, gs, gui_state)
                log.debug("Menu click detected, action: %s", menu_action)
                if menu_action:
                    if menu_action == "quit": action_result = 'QUIT'
                    elif menu_action == "main_menu": action_result = 'TO_MAIN_MENU'
                    elif menu_action == "new_game": action_result = 'NEW_GAME_REQUESTED'
                    elif menu_action == "save":
                        # Übergebe gs UND gui_state an die Speicherfunktion
                        save_load_logic.save_game(gs, gui_state)
                    elif menu_action == "load":
                        # Übergebe gs UND gui_state an die Ladefunktion
                        if save_load_logic.load_game(gs, gui_state):
                            log.info("Game loaded successfully via menu click.")
                            # Signal an main.py senden, um GUI-Status zu aktualisieren
                            action_result = 'GAME_LOADED'
                        else:
                             log.info("Game load via menu click failed or cancelled.")
                    elif menu_action == "resume":
                         gui_state['menu_active'] = False; menu_logic.reset_highlight()
                         if not gui_state['game_over']: timer_logic.start_game_timer()
                         log.info("Resuming game from menu.")
                if action_result: return action_result # Frühzeitiger Ausstieg bei Menüaktion oder Laden
                continue # Nächstes Event verarbeiten

            # --- Klick auf dem Brett (wenn kein Menü aktiv, keine Animation, keine KI denkt) ---
            if not gui_state.get('menu_active', False) and \
               not animations.is_animating() and \
               not gui_state.get('ai_thinking', False):

                col, row = board_display.coords_to_square(location[0], location[1])
                if 0 <= col <= 7 and 0 <= row <= 7:
                    clicked_square = chess.square(col, 7 - row)
                    log.debug("Board clicked at square %s (%d)", chess.square_name(clicked_square), clicked_square)
                    selected_square_index = clicked_square # Cursor folgt dem Klick

                    if not gui_state.get('game_over', False):
                        piece = gs.board.piece_at(clicked_square)

                        # Fall 1: Keine Figur ausgewählt -> Versuche Figur aufzunehmen
                        if source_square_selected is None:
                            if piece and piece.color == gs.board.turn:
                                source_square_selected = clicked_square
                                log.info("Mouse: Picked up piece %s from %s", piece.symbol(), chess.square_name(source_square_selected))
                                if config.ENABLE_TTS: tts_integration.speak_selection(piece, source_square_selected)
                            # else: Klick auf leeres/gegnerisches Feld ohne Auswahl -> nichts tun

                        # Fall 2: Figur ist ausgewählt -> Versuche Zug oder ändere Auswahl
                        else:
                            move = try_create_move(gs.board, source_square_selected, clicked_square)
                            if move:
                                log.info("Mouse: Attempting move %s", move.uci())
                                action_result = _execute_move(gs, gui_state, move)
                                source_square_selected = None # Auswahl aufheben nach Zugversuch
                                if action_result: return action_result
                            else:
                                # Ungültiges Zielfeld geklickt
                                if piece and piece.color == gs.board.turn and clicked_square != source_square_selected:
                                    log.info("Mouse: Changed selection from %s to %s", chess.square_name(source_square_selected), chess.square_name(clicked_square))
                                    source_square_selected = clicked_square
                                    if config.ENABLE_TTS: tts_integration.speak_selection(piece, source_square_selected)
                                else: # Klick auf leeres/gegnerisches Feld oder dasselbe Feld -> Auswahl aufheben
                                    log.info("Mouse: Invalid target square or click on same square. Deselected %s.", chess.square_name(source_square_selected))
                                    source_square_selected = None
                    else: # Spiel ist vorbei
                         log.debug("Mouse click ignored, game is over.")
                         source_square_selected = None # Auswahl aufheben bei Klick nach Spielende
                else: # Klick außerhalb des Bretts
                    log.debug("Mouse click outside board. Deselecting piece.")
                    source_square_selected = None

        # --- Tastaturereignisse ---
        elif event.type == pygame.KEYDOWN:
            log.debug("Key down event: %s (Key: %d, Mod: %d)", pygame.key.name(event.key), event.key, event.mod)
            allow_game_action = not animations.is_animating() and not gui_state.get('ai_thinking', False)
            allow_menu_toggle = not animations.is_animating()
            allow_global_action = True

            is_ctrl_pressed = event.mod & pygame.KMOD_CTRL
            if is_ctrl_pressed and (event.key == pygame.K_x or event.key == pygame.K_q):
                 log.info("Quit requested via Ctrl+X or Ctrl+Q.")
                 return 'QUIT'

            # --- Tastatursteuerung im Menü ---
            if gui_state.get('menu_active', False):
                if event.key == pygame.K_UP:
                    new_item_text = menu_logic.move_highlight(-1)
                    log.debug("Menu Up: Highlight moved. New item: %s", new_item_text)
                    if new_item_text and config.ENABLE_TTS: tts_integration.speak_text(new_item_text, interrupt=False)
                elif event.key == pygame.K_DOWN:
                    new_item_text = menu_logic.move_highlight(1)
                    log.debug("Menu Down: Highlight moved. New item: %s", new_item_text)
                    if new_item_text and config.ENABLE_TTS: tts_integration.speak_text(new_item_text, interrupt=False)
                elif event.key == pygame.K_RETURN:
                    selected_index = menu_logic.get_highlighted_index()
                    menu_action = menu_logic.get_action_at_index(selected_index)
                    log.info("Menu Enter: Action selected: %s", menu_action)
                    if menu_action:
                        if menu_action == "quit": action_result = 'QUIT'
                        elif menu_action == "main_menu": action_result = 'TO_MAIN_MENU'
                        elif menu_action == "new_game": action_result = 'NEW_GAME_REQUESTED'
                        elif menu_action == "save":
                            # Übergebe gs UND gui_state an die Speicherfunktion
                            save_load_logic.save_game(gs, gui_state)
                        elif menu_action == "load":
                            # Übergebe gs UND gui_state an die Ladefunktion
                            if save_load_logic.load_game(gs, gui_state):
                                log.info("Game loaded successfully via menu enter.")
                                # Signal an main.py senden, um GUI-Status zu aktualisieren
                                action_result = 'GAME_LOADED'
                            else:
                                log.info("Game load via menu enter failed or cancelled.")
                        elif menu_action == "resume":
                             gui_state['menu_active'] = False; menu_logic.reset_highlight()
                             if not gui_state['game_over']: timer_logic.start_game_timer()
                             log.info("Resuming game from menu.")

                elif event.key == pygame.K_ESCAPE:
                     gui_state['menu_active'] = False; menu_logic.reset_highlight()
                     if not gui_state['game_over']: timer_logic.start_game_timer()
                     log.info("In-game menu closed (ESC).")

                if action_result: return action_result
                continue

            # --- Tastatursteuerung auf dem Brett (Menü nicht aktiv) ---
            else:
                # -- Undo/Redo (Z/Y) --
                if event.key == pygame.K_z and allow_game_action and not gui_state.get('game_over', False):
                    if navigation_logic.undo_move(gs): # Ruft gs.undo_move() auf
                        # Timer wird jetzt in main.py nach dem Signal 'UNDO_PERFORMED' gestoppt
                        # timer_logic.stop_game_timer(); reset_selection() # Entfernt
                        reset_selection()
                        gui_state.update({'game_over': gs.is_game_over(), 'player_turn_finished': False, 'last_move': gs.board.peek() if gs.board.move_stack else None})
                        log.info("Undo performed (Z).")
                        action_result = 'UNDO_PERFORMED' # Signal an main.py
                    else:
                        log.debug("Undo failed (no moves in stack?).")
                        status_display.display_message("Kein Zug zum Rückgängigmachen", 'warning', duration=2)

                elif event.key == pygame.K_y and allow_game_action and not gui_state.get('game_over', False):
                    if navigation_logic.redo_move(gs): # Ruft gs.redo_move() auf
                        # Timer wird jetzt in main.py nach dem Signal 'REDO_PERFORMED' gestartet
                        # if not gui_state['game_over']: timer_logic.start_game_timer() # Entfernt
                        reset_selection()
                        gui_state.update({'game_over': gs.is_game_over(), 'player_turn_finished': False, 'last_move': gs.board.peek() if gs.board.move_stack else None})
                        log.info("Redo performed (Y).")
                        action_result = 'REDO_PERFORMED' # Signal an main.py
                    else:
                        log.debug("Redo failed (no moves in redo stack?).")
                        status_display.display_message("Kein Zug zum Wiederherstellen", 'warning', duration=2)

                # -- Pfeiltasten --
                elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT] and allow_game_action:
                    new_index = selected_square_index
                    if new_index is None: new_index = chess.E4
                    current_file = chess.square_file(new_index)
                    current_rank = chess.square_rank(new_index)
                    moved = False
                    if event.key == pygame.K_UP:
                        if current_rank < 7: new_index += 8; moved = True
                    elif event.key == pygame.K_DOWN:
                        if current_rank > 0: new_index -= 8; moved = True
                    elif event.key == pygame.K_LEFT:
                        if current_file > 0: new_index -= 1; moved = True
                    elif event.key == pygame.K_RIGHT:
                        if current_file < 7: new_index += 1; moved = True
                    if moved:
                        selected_square_index = max(0, min(new_index, 63))
                        sq_name = chess.square_name(selected_square_index)
                        log.debug("Arrow key: Cursor moved to %s", sq_name)
                        if config.ENABLE_TTS:
                            piece = gs.board.piece_at(selected_square_index)
                            if piece: tts_integration.speak_selection(piece, selected_square_index, interrupt=True)
                            else: tts_integration.speak_text(f"Leerfeld {sq_name}", interrupt=True)
                        if source_square_selected is not None and not gui_state.get('game_over', False):
                            move_check = try_create_move(gs.board, source_square_selected, selected_square_index)
                            if move_check:
                                tts_text = f"Gültiger Zug nach {sq_name}"
                                log.debug("TTS Check: %s", tts_text)
                                if config.ENABLE_TTS: tts_integration.speak_text(tts_text, interrupt=True)

                # -- Leertaste (`K_SPACE`) --
                elif event.key == pygame.K_SPACE and allow_game_action and not gui_state.get('game_over', False):
                    if source_square_selected is None: # Nichts ausgewählt -> Aufnehmen
                        current_cursor_square = selected_square_index
                        if current_cursor_square is not None:
                            piece = gs.board.piece_at(current_cursor_square)
                            if piece and piece.color == gs.board.turn:
                                source_square_selected = current_cursor_square
                                log.info("Spacebar: Picked up piece %s from %s", piece.symbol(), chess.square_name(source_square_selected))
                                if config.ENABLE_TTS: tts_integration.speak_selection(piece, source_square_selected, interrupt=True)
                            else:
                                log.debug("Spacebar: Cannot pick up empty square or opponent's piece.")
                                if config.ENABLE_TTS: tts_integration.speak_text("Nicht möglich", interrupt=True)
                    else: # Etwas war ausgewählt -> Auswahl abbrechen
                        log.info("Spacebar: Deselected piece from %s.", chess.square_name(source_square_selected))
                        source_square_selected = None
                        if config.ENABLE_TTS: tts_integration.speak_text("Auswahl aufgehoben", interrupt=True)

                # -- Enter (`K_RETURN`) --
                elif event.key == pygame.K_RETURN and allow_game_action and not gui_state.get('game_over', False):
                    if source_square_selected is not None and selected_square_index is not None:
                        move = try_create_move(gs.board, source_square_selected, selected_square_index)
                        if move:
                            log.info("Enter: Attempting move %s", move.uci())
                            action_result = _execute_move(gs, gui_state, move)
                            source_square_selected = None # Auswahl aufheben
                        else:
                            status_display.display_message("Ungültiger Zug", 'error', duration=3)
                            log.warning("Enter: Invalid move attempt from %s to %s", chess.square_name(source_square_selected), chess.square_name(selected_square_index))
                            if config.ENABLE_TTS: tts_integration.speak_text("Ungültiger Zug", interrupt=True)
                    # else: log.debug("Enter: No source or target selected.")

                # -- Andere Tasten --
                elif event.key == pygame.K_ESCAPE and allow_menu_toggle:
                    gui_state['menu_active'] = True; menu_logic.reset_highlight(); reset_selection()
                    timer_logic.stop_game_timer()
                    log.info("In-game menu opened (ESC).")
                    if config.ENABLE_TTS: tts_integration.speak_text(config.INGAME_MENU_TITLE, interrupt=False)

                elif event.key == pygame.K_s and is_ctrl_pressed: # Strg+S Speichern
                    if allow_game_action:
                        log.info("Save initiated (Ctrl+S)...")
                        # Übergebe gs UND gui_state an die Speicherfunktion
                        save_load_logic.save_game(gs, gui_state)
                    else: log.debug("Save (Ctrl+S) ignored while action not allowed.")

                elif event.key == pygame.K_l and is_ctrl_pressed: # Strg+L Laden
                    if allow_game_action:
                        log.info("Load initiated (Ctrl+L)...")
                        # Übergebe gs UND gui_state an die Ladefunktion
                        if save_load_logic.load_game(gs, gui_state):
                            log.info("Game loaded successfully via Ctrl+L.")
                            # Signal an main.py senden, um GUI-Status zu aktualisieren
                            action_result = 'GAME_LOADED'
                        else: log.info("Load (Ctrl+L) failed or cancelled.")
                    else: log.debug("Load (Ctrl+L) ignored while action not allowed.")

                elif event.key == pygame.K_t and allow_global_action: # T Zeit ansagen
                     try:
                         formatted_time = timer_logic.get_formatted_time()
                         log.info("Announcing time (T): %s", formatted_time)
                         tts_integration.speak_text(f"Spielzeit: {formatted_time}", interrupt=True)
                     except AttributeError:
                         log.warning("timer_logic does not have get_formatted_time function.")
                         tts_integration.speak_text("Zeitfunktion nicht verfügbar", interrupt=True)
                     except Exception as e:
                         log.error("Error getting or speaking time: %s", e, exc_info=True)
                         tts_integration.speak_text("Fehler bei Zeitansage", interrupt=True)

                elif event.key == pygame.K_a and allow_global_action: # A Audio an/aus
                     config.ENABLE_SOUNDS = not config.ENABLE_SOUNDS
                     status_text = "Soundeffekte An" if config.ENABLE_SOUNDS else "Soundeffekte Aus"
                     log.info("Sound effects toggled (A): %s", status_text)
                     status_display.display_message(status_text, 'info', duration=2)
                     tts_integration.speak_text(status_text, interrupt=True)

                elif event.key == pygame.K_s and not is_ctrl_pressed and allow_global_action: # S TTS an/aus
                    config.ENABLE_TTS = not config.ENABLE_TTS
                    status_text = "Sprachausgabe An" if config.ENABLE_TTS else "Sprachausgabe Aus"
                    log.info("TTS toggled (S): %s", status_text)
                    status_display.display_message(status_text, 'info', duration=2)
                    if config.ENABLE_TTS: tts_integration.speak_text(status_text, interrupt=True)

                elif event.key == pygame.K_f and allow_global_action: # F Brett drehen
                    gui_state['board_flipped'] = not gui_state.get('board_flipped', False)
                    log.info("Board view flipped (F): %s", gui_state['board_flipped'])
                    status_display.display_message(f"Brettansicht {'gedreht' if gui_state['board_flipped'] else 'normal'}", 'info', duration=2)

                elif event.key == pygame.K_p and config.DEBUG_MODE: # P Debug Info
                    log.debug("\n--- DEBUG INFO (Key 'p') ---")
                    log.debug("Board State:\n%s", gs.board)
                    log.debug("FEN: %s", gs.get_fen())
                    log.debug("Move: %d %s", gs.board.fullmove_number, 'White' if gs.board.turn else 'Black')
                    try: log.debug("Legal moves count: %d", gs.board.legal_moves.count())
                    except: log.debug("Legal moves count: Error")
                    log.debug("Cursor Square: %s (%s)", selected_square_index, chess.square_name(selected_square_index) if selected_square_index is not None else 'None')
                    log.debug("Source Square: %s (%s)", source_square_selected, chess.square_name(source_square_selected) if source_square_selected is not None else 'None')
                    log.debug("GUI State: %s", gui_state)
                    log.debug("TTS Enabled: %s", config.ENABLE_TTS)
                    log.debug("Sounds Enabled: %s", config.ENABLE_SOUNDS)
                    log.debug("Animating: %s", animations.is_animating())
                    log.debug("AI Thinking: %s", gui_state.get('ai_thinking', False))
                    # Verwende die neuen Getter-Methoden
                    log.debug("Captured White: %s", [p.symbol() for p in gs.get_captured_by_black()])
                    log.debug("Captured Black: %s", [p.symbol() for p in gs.get_captured_by_white()])
                    log.debug("Redo Stack: %s", [(m.uci(), p.symbol() if p else None) for m, p in gs.redo_stack_prop])
                    log.debug("----------------------------\n")


        # --- Andere Ereignistypen könnten hier behandelt werden ---
        # elif event.type == ...

    return action_result # Gibt None zurück, wenn kein Zustandswechsel nötig ist

# --- Hilfsfunktionen ---

def _execute_move(gs: 'GameState', gui_state: Dict[str, Any], move: chess.Move) -> Optional[str]:
    """
    Führt einen gegebenen Zug aus, aktualisiert GUI/Spielzustand und startet Animation/Sounds.
    Gibt potenziell eine Aktions-Zeichenkette zurück (aktuell nicht verwendet).
    """
    global _board_display_ref
    if _board_display_ref is None:
        log.critical("_execute_move called but _board_display_ref is None!")
        return None # Kann nicht fortfahren

    log.debug("Executing move: %s", move.uci())
    piece_to_animate = gs.board.piece_at(move.from_square)
    if piece_to_animate is None:
         log.error("Attempting to execute move %s but no piece found at source square %s!",
                   move.uci(), chess.square_name(move.from_square))

    # Redo-Stack wird jetzt automatisch in gs.make_move() gelöscht
    # navigation_logic.clear_redo_stack(gs) # ENTFERNT

    try:
        # make_move kümmert sich jetzt um alles: push, capture list, clear redo stack
        move_successful = gs.make_move(move)
        if not move_successful:
             log.error("gs.make_move returned False for move %s", move.uci())
             status_display.display_message(f"Fehler bei Zugausführung!", 'error', duration=5)
             return None # Zug konnte nicht ausgeführt werden
        log.debug("Move %s made successfully via gs.make_move.", move.uci())
    except Exception as e:
        log.error("Exception during gs.make_move(%s): %s", move.uci(), e, exc_info=True)
        status_display.display_message(f"Fehler bei Zugausführung: {e}", 'error', duration=5)
        return None # Zug konnte nicht ausgeführt werden

    # Statusanzeige und letzter Zug aktualisieren
    detailed_speech_text = tts_integration.format_move_for_speech_post_move(gs.board, move)
    display_text = detailed_speech_text if detailed_speech_text else move.uci()
    status_display.display_message(display_text, 'move', config.STATUS_MOVE_DURATION)
    gui_state['last_move'] = move

    # Animation starten (nur wenn eine Figur vorhanden war)
    if piece_to_animate:
        animations.start_move_animation(move, piece_to_animate, _board_display_ref)
    else:
        log.warning("Skipping animation for move %s because piece_to_animate was None.", move.uci())

    # Sounds abspielen
    play_move_sounds(gs.board, move) # Übergibt das Board *nach* dem Zug

    # TTS-Ansage nach dem Zug
    if config.ENABLE_TTS:
        tts_integration.speak_move_after(gs.board, move) # Ansage NACH dem Zug

    # Flag setzen, damit ggf. die KI starten kann
    gui_state['player_turn_finished'] = True
    log.debug("Player turn finished flag set to True.")

    # Aktuell gibt diese Funktion keine Zustandswechsel zurück
    return None


def try_create_move(board: chess.Board, from_sq: Optional[chess.Square], to_sq: Optional[chess.Square]) -> Optional[chess.Move]:
    """
    Versucht, ein gültiges chess.Move Objekt zu erstellen und zu validieren.
    Berücksichtigt Bauernumwandlung (Standard: Dame).
    """
    if from_sq is None or to_sq is None: return None
    piece = board.piece_at(from_sq)
    if not piece or piece.color != board.turn: return None

    promotion_piece = None
    if piece.piece_type == chess.PAWN:
        target_rank = chess.square_rank(to_sq)
        if (piece.color == chess.WHITE and target_rank == 7) or \
           (piece.color == chess.BLACK and target_rank == 0):
            promotion_piece = chess.QUEEN

    move = chess.Move(from_sq, to_sq, promotion=promotion_piece)
    is_legal = False
    try:
        is_legal = move in board.legal_moves
    except Exception as e:
        log.warning("Exception during 'move in board.legal_moves' check for %s: %s", move.uci(), e, exc_info=True)
        is_legal = False

    return move if is_legal else None


def play_move_sounds(board_after_move: chess.Board, move: chess.Move):
    """
    Spielt passende Sounds für den gerade ausgeführten Zug ab.
    Benötigt das Board *nach* dem Zug, um auf Schach/Matt zu prüfen.
    """
    if not config.ENABLE_SOUNDS or not config.mixer_initialized: return

    sound_to_play: Optional[str] = None
    try:
        # Prüfe auf Spielende-Zustände zuerst
        if board_after_move.is_checkmate(): sound_to_play = 'Checkmate'
        elif board_after_move.is_stalemate() or board_after_move.is_insufficient_material(): sound_to_play = 'game_over'
        # Dann auf Schach
        elif board_after_move.is_check(): sound_to_play = 'Check'
        # Dann auf Rochade
        elif board_after_move.is_castling(move): sound_to_play = 'Castle'
        else:
            # Prüfe auf Schlagzug (durch temporäres Zurücknehmen des Zuges vom *aktuellen* Brett)
            was_capture = False
            try:
                board_after_move.pop() # Zug zurücknehmen
                was_capture = board_after_move.is_capture(move) # Prüfen, ob der Zug *jetzt* ein Schlagzug wäre
                board_after_move.push(move) # Zug wieder ausführen
            except IndexError: log.warning("play_move_sounds: Could not pop move %s to check for capture.", move.uci())
            except Exception as e: log.error("play_move_sounds: Error during capture check for move %s: %s", move.uci(), e, exc_info=True)

            if was_capture: sound_to_play = 'PieceCapture'
            else: sound_to_play = 'PiecePlace' # Normaler Zug

        if sound_to_play:
            log.debug("Playing sound for move %s: %s", move.uci(), sound_to_play)
            config.play_sound(sound_to_play)
        else:
            log.warning("No specific sound determined for move %s, playing default.", move.uci())
            config.play_sound('PiecePlace')
    except Exception as e:
        log.error("Error determining sound for move %s: %s", move.uci(), e, exc_info=True)
        config.play_sound('PiecePlace') # Fallback


# --- Getter für Zustände ---
def get_selected_square() -> Optional[chess.Square]:
    """Gibt das aktuell mit dem Cursor ausgewählte Feld zurück."""
    return selected_square_index

def get_source_square() -> Optional[chess.Square]:
    """Gibt das Feld zurück, von dem eine Figur aufgenommen wurde."""
    return source_square_selected

# --- Reset-Funktion ---
def reset_selection():
    """ Setzt Cursor und Figurenauswahl zurück (z.B. nach Zug, Laden, Menü). """
    global selected_square_index, source_square_selected
    selected_square_index = chess.E4 # Cursor zurück zur Mitte
    source_square_selected = None
    log.debug("Selection reset: Cursor -> E4, Source -> None.")

