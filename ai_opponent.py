# -*- coding: utf-8 -*-
"""
Modul für die Schach-KI (Gegner).
Enthält Bewertungsfunktionen, Suchalgorithmen (Minimax mit Alpha-Beta)
und die Logik zur Nutzung von Eröffnungsbüchern und Endspieldatenbanken.
"""

import logger, logging
import sys # Für kritische Fehler
from game_state import GameState
import random, chess, chess.polyglot, chess.syzygy
import config
from typing import Optional, List, Union
import queue # Für die Kommunikation mit dem Hauptthread

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in ai_opponent.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")

log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False, # Konsole auf False setzen
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

# --- Bewertungsfunktionen (unverändert) ---

def score_material(board: chess.Board) -> int:
    """Bewertet das Brett basierend auf dem Materialwert der Figuren."""
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            score += config.PIECE_VALUES.get(piece.piece_type, 0) * (1 if piece.color == chess.WHITE else -1)
    return score

def evaluate_board(board: chess.Board) -> int:
    """Bewertet die aktuelle Brettstellung umfassender."""
    try:
        if board.is_checkmate():
            return -config.CHECKMATE if board.turn == chess.WHITE else config.CHECKMATE
        elif board.is_stalemate() or \
             board.is_insufficient_material() or \
             board.is_seventyfive_moves():
            return config.STALEMATE
    except Exception as e:
        log.warning("Exception during game over check in evaluate_board: %s (FEN: %s)", e, board.fen(), exc_info=True)
    return score_material(board)

# --- Zugfindungsalgorithmen (unverändert) ---

def find_random_move(valid_moves: List[chess.Move]) -> Optional[chess.Move]:
    """Wählt einen zufälligen Zug aus."""
    if not valid_moves:
        log.debug("find_random_move: No valid moves provided.")
        return None
    try:
        return random.choice(valid_moves)
    except IndexError:
        log.warning("find_random_move: IndexError despite non-empty check.")
        return None
    except Exception as e:
        log.error("find_random_move: Unexpected error: %s", e, exc_info=True)
        return None


def minimax(gs: 'GameState', depth: int, alpha: float, beta: float, maximizing_player: bool) -> Union[int, float]:
    """Implementiert den Minimax-Algorithmus mit Alpha-Beta-Pruning."""
    if depth == 0 or gs.is_game_over_for_ai():
        return evaluate_board(gs.board)

    try:
        valid_moves = list(gs.get_valid_moves())
        if not valid_moves: return evaluate_board(gs.board)
    except Exception as e:
        log.error("Exception getting valid moves in minimax: %s (Depth: %d, FEN: %s)", e, depth, gs.board.fen(), exc_info=True)
        return config.STALEMATE

    random.shuffle(valid_moves)

    if maximizing_player: # Weiß
        max_eval = -config.CHECKMATE - 1
        for move in valid_moves:
            move_made = False
            eval_score = -config.CHECKMATE -1
            try:
                if gs.make_move(move): # Wichtig: make_move modifiziert gs!
                    move_made = True
                    eval_score = minimax(gs, depth - 1, alpha, beta, False)
                else:
                    log.warning("Minimax (max): make_move(%s) returned False. FEN: %s", move.uci(), gs.board.fen())
                    eval_score = -config.CHECKMATE - 1
            except Exception as e:
                log.error("Exception during make_move in minimax (max): %s (Move: %s, FEN: %s)", e, move.uci(), gs.board.fen(), exc_info=True)
                eval_score = -config.CHECKMATE - 1
            finally:
                if move_made:
                    try:
                        gs.undo_move() # Macht die Änderung an gs rückgängig
                    except Exception as e:
                        log.critical("CRITICAL Exception during undo_move in minimax (max): %s. Aborting branch.", e, exc_info=True)
                        return config.STALEMATE
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha: break
        return max_eval
    else: # Schwarz
        min_eval = config.CHECKMATE + 1
        for move in valid_moves:
            move_made = False
            eval_score = config.CHECKMATE + 1
            try:
                if gs.make_move(move): # Wichtig: make_move modifiziert gs!
                    move_made = True
                    eval_score = minimax(gs, depth - 1, alpha, beta, True)
                else:
                    log.warning("Minimax (min): make_move(%s) returned False. FEN: %s", move.uci(), gs.board.fen())
                    eval_score = config.CHECKMATE + 1
            except Exception as e:
                log.error("Exception during make_move in minimax (min): %s (Move: %s, FEN: %s)", e, move.uci(), gs.board.fen(), exc_info=True)
                eval_score = config.CHECKMATE + 1
            finally:
                if move_made:
                    try:
                        gs.undo_move() # Macht die Änderung an gs rückgängig
                    except Exception as e:
                        log.critical("CRITICAL Exception during undo_move in minimax (min): %s. Aborting branch.", e, exc_info=True)
                        return config.STALEMATE
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha: break
        return min_eval


def find_best_move_minimax(gs: GameState, valid_moves: List[chess.Move], depth: int) -> Optional[chess.Move]:
    """
    Findet den besten Zug mithilfe des Minimax-Algorithmus.
    Startet die rekursive Suche auf der obersten Ebene.
    WICHTIG: Diese Funktion modifiziert das übergebene `gs`-Objekt während der Suche!
    """
    if not valid_moves:
        log.info("find_best_move_minimax: No valid moves to evaluate.")
        return None

    log.info("Starting Minimax search with depth %d for %s.", depth, "White" if gs.board.turn == chess.WHITE else "Black")
    best_move = None
    current_player_color = gs.board.turn
    alpha = -config.CHECKMATE - 1
    beta = config.CHECKMATE + 1
    best_value = -config.CHECKMATE - 1 if current_player_color == chess.WHITE else config.CHECKMATE + 1

    moves_to_evaluate = list(valid_moves)
    random.shuffle(moves_to_evaluate)
    log.debug("Evaluating %d moves: %s", len(moves_to_evaluate), [m.uci() for m in moves_to_evaluate])

    for i, move in enumerate(moves_to_evaluate):
        move_made = False
        board_value = 0

        try:
            if gs.make_move(move): # Modifiziert gs
                move_made = True
                is_opponent_maximizer = (gs.board.turn == chess.WHITE)
                board_value = minimax(gs, depth - 1, alpha, beta, is_opponent_maximizer) # Ruft minimax auf demselben gs auf
            else:
                log.warning("find_best_move_minimax: Top-level make_move(%s) returned False. FEN: %s", move.uci(), gs.board.fen())
                board_value = config.CHECKMATE + 1 if current_player_color == chess.WHITE else -config.CHECKMATE - 1
        except Exception as e:
            log.error("Exception during top-level make_move block: %s (Move: %s, FEN: %s)", e, move.uci(), gs.board.fen(), exc_info=True)
            board_value = config.CHECKMATE + 1 if current_player_color == chess.WHITE else -config.CHECKMATE - 1
        finally:
            if move_made:
                try:
                    gs.undo_move() # Macht die Änderung an gs rückgängig
                except Exception as e:
                    log.critical("CRITICAL Exception during top-level undo_move: %s. Skipping move.", e, exc_info=True)
                    continue

        if not move_made:
            log.warning("Skipping evaluation for move %s due to make_move failure.", move.uci())
            continue

        if current_player_color == chess.WHITE:
            if board_value > best_value:
                log.debug("New best move for White: %s (Value: %.1f > %.1f)", move.uci(), board_value, best_value)
                best_value = board_value
                best_move = move
            alpha = max(alpha, board_value)
        else:
            if board_value < best_value:
                log.debug("New best move for Black: %s (Value: %.1f < %.1f)", move.uci(), board_value, best_value)
                best_value = board_value
                best_move = move
            beta = min(beta, board_value)

    if best_move is None and valid_moves:
        log.warning("Minimax search completed but no best move identified. Choosing random move as fallback.")
        best_move = find_random_move(valid_moves)

    if best_move:
        log.info("Minimax search finished. Best move found: %s with evaluation: %.1f", best_move.uci(), best_value)
    else:
        log.warning("Minimax search finished. No move could be selected.")

    return best_move


# --- Hauptfunktion zur Zugfindung ---
def find_best_move(gs: GameState, valid_moves: List[chess.Move], return_queue: Optional[queue.Queue] = None):
    """
    Hauptfunktion zur Zugfindung der KI. Verwendet Buch, Endspiel-TB oder Minimax.
    Übergibt eine Kopie des GameState an die Minimax-Suche.
    """
    log.info("find_best_move called for %s.", "White" if gs.board.turn == chess.WHITE else "Black")
    best_move_found = None

    if not valid_moves:
        log.info("No valid moves available.")
        if return_queue: return_queue.put(None)
        return None

    # --- Buch/Endspiel-Prüfung (mit Kopie des *Boards*) ---
    board_copy = gs.board.copy()
    log.debug("Created board copy for book/syzygy lookup. FEN: %s", board_copy.fen())

    # 1. Eröffnungsbuch prüfen
    if config.POLYGLOT_BOOK_PATH and config.POLYGLOT_BOOK_PATH != "":
        # (Logik bleibt gleich, verwendet board_copy)
        log.debug("Checking opening book: %s", config.POLYGLOT_BOOK_PATH)
        try:
            with chess.polyglot.open_reader(config.POLYGLOT_BOOK_PATH) as reader:
                entries = list(reader.find_all(board_copy))
                if entries:
                    log.debug("Found %d entries in opening book.", len(entries))
                    opening_move = random.choice(entries).move
                    log.debug("Potential opening move from book: %s", opening_move.uci())
                    if opening_move in valid_moves:
                        log.info("Opening book move found and is legal: %s", opening_move.uci())
                        best_move_found = opening_move
                    else:
                         log.warning("Opening book move %s is NOT currently legal for FEN %s", opening_move.uci(), gs.board.fen())
                else:
                    log.debug("No matching position found in opening book.")
        except FileNotFoundError: log.warning("Opening book file not found at: %s", config.POLYGLOT_BOOK_PATH)
        except IndexError: log.debug("IndexError while accessing opening book.")
        except Exception as e: log.error("Error reading opening book: %s", e, exc_info=True)

    # 2. Endspieldatenbank prüfen
    piece_count = len(board_copy.piece_map())
    syzygy_enabled = config.SYZYGY_PATH and config.SYZYGY_PATH != ""
    syzygy_applicable = piece_count <= config.SYZYGY_MAX_PIECES

    if best_move_found is None and syzygy_enabled and syzygy_applicable:
        # (Logik bleibt gleich, verwendet board_copy)
        log.debug("Checking Syzygy endgame tablebases (Piece count: %d <= %d): %s",
                  piece_count, config.SYZYGY_MAX_PIECES, config.SYZYGY_PATH)
        try:
            with chess.syzygy.open_tablebase(config.SYZYGY_PATH) as tablebase:
                best_syzygy_move = None
                best_wdl = -3
                for move in valid_moves:
                    wdl_opponent = None
                    try:
                        board_copy.push(move)
                        wdl_opponent = tablebase.probe_wdl(board_copy)
                        board_copy.pop()
                    except Exception as e_push_pop:
                        log.error("Exception during push/pop in Syzygy check for move %s: %s", move.uci(), e_push_pop, exc_info=True)
                        if board_copy.move_stack and board_copy.peek() == move:
                            try: board_copy.pop()
                            except IndexError: pass
                        continue
                    if wdl_opponent is not None:
                        current_player_wdl = -wdl_opponent
                        if current_player_wdl > best_wdl:
                            best_wdl = current_player_wdl
                            best_syzygy_move = move
                            if best_wdl > 0: break
                        elif current_player_wdl == best_wdl:
                            if random.choice([True, False]): best_syzygy_move = move
                if best_syzygy_move is not None:
                    if best_syzygy_move in valid_moves:
                        log.info("Syzygy endgame tablebase move found: %s (Best WDL: %d)", best_syzygy_move.uci(), best_wdl)
                        best_move_found = best_syzygy_move
                    else: log.warning("Syzygy found move %s which is not in valid_moves?", best_syzygy_move.uci())
                else: log.debug("Syzygy probe completed, no move selected.")
        except FileNotFoundError: log.warning("Syzygy endgame tablebase path not found: %s", config.SYZYGY_PATH)
        except Exception as e: log.error("Error accessing Syzygy endgame tablebase: %s", e, exc_info=True)

    # 3. Wenn kein Buch/TB-Zug, nutze Minimax mit einer *Kopie* des GameState
    if best_move_found is None:
        log.info("No book/Syzygy move found. Starting Minimax search (Depth: %d)...", config.AI_DEPTH)
        try:
            # *** HIER DIE ÄNDERUNG: Verwende gs.copy() ***
            search_gs = gs.copy()
            log.debug("Created GameState copy for Minimax search.")
            # Übergebe die Kopie an die Suchfunktion
            best_move_found = find_best_move_minimax(search_gs, valid_moves, depth=config.AI_DEPTH)
        except AttributeError as e_copy:
             log.error("GameState object does not have a 'copy' method: %s. Falling back to FEN initialization.", e_copy)
             # Fallback, falls copy() nicht implementiert ist
             search_gs = GameState(fen=gs.get_fen())
             best_move_found = find_best_move_minimax(search_gs, valid_moves, depth=config.AI_DEPTH)
        except Exception as e_search:
             log.error("Exception during Minimax search execution: %s", e_search, exc_info=True)
             best_move_found = None

    # 4. Fallback: Zufälliger Zug
    if best_move_found is None and valid_moves:
        log.warning("No best move identified after all checks. Choosing random move as final fallback.")
        best_move_found = find_random_move(valid_moves)

    # 5. Ergebnis zurückgeben oder in Queue legen
    if return_queue:
        log.debug("Putting best move (%s) into return queue.", best_move_found.uci() if best_move_found else "None")
        try:
            return_queue.put(best_move_found)
        except Exception as e_queue:
            log.error("Exception putting move into queue: %s", e_queue, exc_info=True)
    else:
        log.debug("Returning best move directly: %s", best_move_found.uci() if best_move_found else "None")
        return best_move_found
