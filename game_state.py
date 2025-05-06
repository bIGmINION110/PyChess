# -*- coding: utf-8 -*-
"""
Dieses Modul definiert die Klasse GameState, die den Kernzustand des Schachspiels verwaltet.
Sie kapselt das `chess.Board`-Objekt aus der python-chess Bibliothek, verwaltet die Zughistorie
(Undo/Redo) und verfolgt geschlagene Figuren.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import copy # Für deepcopy der Listen
import logger
import chess
from typing import Optional, List, Tuple

# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in game_state.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)


class GameState:
    """
    Repräsentiert den aktuellen logischen Zustand des Schachspiels.

    Attributes:
        board (chess.Board): Das aktuelle Schachbrett-Objekt.
        redo_stack (List[Tuple[chess.Move, Optional[chess.Piece]]]): Stack für Wiederherstellungszüge.
                                                                    Speichert den Zug und die evtl. geschlagene Figur.
        captured_by_white (List[chess.Piece]): Liste der schwarzen Figuren, die von Weiß geschlagen wurden.
        captured_by_black (List[chess.Piece]): Liste der weißen Figuren, die von Schwarz geschlagen wurden.
    """
    def __init__(self, fen: Optional[str] = None, board: Optional[chess.Board] = None,
                 captured_w: Optional[List[chess.Piece]] = None,
                 captured_b: Optional[List[chess.Piece]] = None,
                 redo_s: Optional[List[Tuple[chess.Move, Optional[chess.Piece]]]] = None):
        """
        Initialisiert den Spielzustand. Kann entweder mit FEN oder einem bestehenden Board/Listen initialisiert werden.
        """
        if board is not None:
             self.board = board # Verwende übergebenes Board (z.B. für copy())
             log.debug("GameState initialized with provided board.")
        else:
             self.board = chess.Board() # Initialisiere mit Standard
             log.debug("GameState initialized with default board.")

        # Initialisiere Listen (entweder übergeben oder leer)
        self.redo_stack = redo_s if redo_s is not None else []
        self.captured_by_white = captured_w if captured_w is not None else []
        self.captured_by_black = captured_b if captured_b is not None else []
        log.debug("Initial capture lists - White: %d, Black: %d. Redo stack size: %d",
                  len(self.captured_by_white), len(self.captured_by_black), len(self.redo_stack))


        # Wenn FEN angegeben wird UND kein Board übergeben wurde, setze FEN
        if fen and board is None:
            log.info("Attempting to initialize GameState with FEN: %s", fen)
            try:
                self.board.set_fen(fen)
                # Bei FEN immer Stacks/Listen leeren
                self.redo_stack.clear()
                self.captured_by_white.clear()
                self.captured_by_black.clear()
                log.warning("GameState initialized with FEN. Capture lists and history are reset.")
            except ValueError:
                log.warning("Invalid FEN string '%s' provided. Using default setup.", fen)
                self.reset_game()
            except Exception as e:
                 log.error("Unexpected error setting FEN '%s': %s. Using default setup.", fen, e, exc_info=True)
                 self.reset_game()
        elif not fen and board is None:
             log.info("GameState initialized with standard setup (no FEN/board provided).")


    def copy(self) -> 'GameState':
        """ Erstellt eine Kopie des aktuellen GameState. """
        log.debug("Creating a copy of the GameState.")
        # Erstelle eine Kopie des Boards
        new_board = self.board.copy()
        # Erstelle Kopien der Listen (deepcopy ist sicherer für Listen von Objekten)
        new_captured_w = copy.deepcopy(self.captured_by_white)
        new_captured_b = copy.deepcopy(self.captured_by_black)
        # Der Redo-Stack wird für die Kopie (z.B. in der KI-Suche) normalerweise nicht benötigt
        # und sollte leer starten, um Verwirrung zu vermeiden.
        new_redo_s = []
        # Erstelle eine neue Instanz mit den kopierten Daten
        return GameState(board=new_board, captured_w=new_captured_w, captured_b=new_captured_b, redo_s=new_redo_s)


    def make_move(self, move: chess.Move) -> bool:
        """
        Führt einen Zug auf dem Brett aus, aktualisiert den Zustand und die Capture-Listen.
        Löscht den Redo-Stack.

        Args:
            move (chess.Move): Das auszuführende chess.Move-Objekt.

        Returns:
            bool: True, wenn der Zug erfolgreich ausgeführt wurde, sonst False.
        """
        captured_piece: Optional[chess.Piece] = None
        is_capture = False
        moving_color = self.board.turn

        try:
            if move in self.board.legal_moves:
                # --- Ermittle geschlagene Figur VOR dem Zug ---
                is_capture = self.board.is_capture(move)
                if is_capture:
                    if self.board.is_en_passant(move):
                        capture_sq = move.to_square - 8 if moving_color == chess.WHITE else move.to_square + 8
                        captured_piece = chess.Piece(chess.PAWN, not moving_color)
                        log.debug("En passant capture detected by %s. Captured piece: %s at %s (assumed)",
                                  "White" if moving_color == chess.WHITE else "Black",
                                  captured_piece.symbol(), chess.square_name(capture_sq))
                    else:
                        captured_piece = self.board.piece_at(move.to_square)
                        if captured_piece:
                             log.debug("Regular capture detected by %s. Captured piece: %s at %s",
                                       "White" if moving_color == chess.WHITE else "Black",
                                       captured_piece.symbol(), chess.square_name(move.to_square))
                        else:
                             log.warning("is_capture is True for move %s, but no piece found at target square %s!",
                                         move.uci(), chess.square_name(move.to_square))
                             is_capture = False # Korrigiere Flag

                # --- Führe den Zug aus ---
                self.board.push(move)

                # --- Füge geschlagene Figur zur Liste hinzu ---
                if is_capture and captured_piece:
                    if moving_color == chess.WHITE: # Weiß hat geschlagen (schwarze Figur)
                        self.captured_by_white.append(captured_piece)
                        log.debug("Added captured %s to captured_by_white list (Total: %d)",
                                  captured_piece.symbol(), len(self.captured_by_white))
                    else: # Schwarz hat geschlagen (weiße Figur)
                        self.captured_by_black.append(captured_piece)
                        log.debug("Added captured %s to captured_by_black list (Total: %d)",
                                  captured_piece.symbol(), len(self.captured_by_black))

                # --- Lösche den Redo-Stack ---
                if self.redo_stack:
                    log.debug("Clearing redo stack (%d items) due to new move.", len(self.redo_stack))
                    self.redo_stack.clear()

                log.info("Move executed: %s", move.uci())
                return True
            else:
                log.warning("Attempted to execute illegal move %s in make_move.", move.uci())
                return False
        except Exception as e:
            log.error("Exception during make_move(%s): %s", move.uci(), e, exc_info=True)
            return False

    def undo_move(self) -> Optional[chess.Move]:
        """
        Macht den letzten Zug rückgängig, aktualisiert Capture-Listen und Redo-Stack.
        """
        if not self.board.move_stack:
            log.info("No move available to undo.")
            return None

        try:
            # 1. Ermittle den Zug und ob er ein Schlagzug war *bevor* pop()
            move_to_undo = self.board.peek()
            moving_color_that_made_the_move = self.board.turn # Farbe *vor* dem Pop
            captured_piece_to_restore: Optional[chess.Piece] = None
            was_capture = self.board.is_capture(move_to_undo)

            if was_capture:
                # Entferne die zuletzt hinzugefügte Figur aus der Capture-Liste des Spielers, der zog
                if moving_color_that_made_the_move == chess.WHITE:
                    if self.captured_by_white:
                        captured_piece_to_restore = self.captured_by_white.pop()
                        log.debug("Undo: Removed %s from captured_by_white list.", captured_piece_to_restore.symbol())
                    else:
                        log.warning("Undo: Move %s was capture by White, but captured_by_white list is empty! "
                                    "This might happen during AI search on copied boards if captures aren't tracked there.",
                                    move_to_undo.uci())
                        if self.board.is_en_passant(move_to_undo):
                             captured_piece_to_restore = chess.Piece(chess.PAWN, chess.BLACK)
                             log.debug("Undo: Assuming captured piece was black Pawn for en passant.")
                else: # Black made the move
                    if self.captured_by_black:
                        captured_piece_to_restore = self.captured_by_black.pop()
                        log.debug("Undo: Removed %s from captured_by_black list.", captured_piece_to_restore.symbol())
                    else:
                        log.warning("Undo: Move %s was capture by Black, but captured_by_black list is empty! "
                                    "This might happen during AI search on copied boards if captures aren't tracked there.",
                                    move_to_undo.uci())
                        if self.board.is_en_passant(move_to_undo):
                             captured_piece_to_restore = chess.Piece(chess.PAWN, chess.WHITE)
                             log.debug("Undo: Assuming captured piece was white Pawn for en passant.")

            # 2. Pop den Zug vom Board-Stack
            undone_move = self.board.pop()

            # 3. Füge Zug und wiederhergestellte Figur zum Redo-Stack hinzu
            self.redo_stack.append((undone_move, captured_piece_to_restore))

            log.info("Move undone: %s. Added to redo stack (Captured piece restored: %s). Redo stack size: %d",
                     undone_move.uci(), captured_piece_to_restore.symbol() if captured_piece_to_restore else "None", len(self.redo_stack))
            return undone_move

        except IndexError:
            log.error("IndexError during board operation in undo_move.")
            return None
        except Exception as e_undo:
            log.error("Exception during undo_move: %s", e_undo, exc_info=True)
            return None

    def redo_move(self) -> Optional[chess.Move]:
        """
        Wiederholt den letzten rückgängig gemachten Zug vom Redo-Stack,
        aktualisiert Capture-Listen und führt den Zug direkt aus.
        """
        if not self.redo_stack:
            log.info("No move available to redo.")
            return None

        try:
            # 1. Hole Zug und ursprünglich geschlagene Figur vom Redo-Stack
            move_to_redo, originally_captured_piece = self.redo_stack.pop()
            moving_color = self.board.turn

            # 2. Prüfe Legalität (Sicherheitscheck)
            if move_to_redo not in self.board.legal_moves:
                log.error("Cannot redo move %s: It is not legal in the current position! FEN: %s",
                          move_to_redo.uci(), self.board.fen())
                self.redo_stack.append((move_to_redo, originally_captured_piece)) # Zurücklegen
                return None

            # 3. Führe den Zug direkt auf dem Brett aus
            self.board.push(move_to_redo)

            # 4. Füge die ursprünglich geschlagene Figur wieder zur Capture-Liste hinzu
            if originally_captured_piece:
                if moving_color == chess.WHITE: # Weiß hat geschlagen
                    self.captured_by_white.append(originally_captured_piece)
                    log.debug("Redo: Added captured %s back to captured_by_white list.", originally_captured_piece.symbol())
                else: # Schwarz hat geschlagen
                    self.captured_by_black.append(originally_captured_piece)
                    log.debug("Redo: Added captured %s back to captured_by_black list.", originally_captured_piece.symbol())

            log.info("Move redone: %s. Redo stack size: %d", move_to_redo.uci(), len(self.redo_stack))
            return move_to_redo

        except IndexError:
             log.error("IndexError during redo_stack.pop() in redo_move.")
             return None
        except ValueError as e_push:
             log.error("ValueError redoing move %s: %s", move_to_redo.uci(), e_push, exc_info=True)
             self.redo_stack.append((move_to_redo, originally_captured_piece)) # Zurücklegen
             return None
        except Exception as e_redo:
             log.error("Exception during redo_move (%s): %s", move_to_redo.uci(), e_redo, exc_info=True)
             # Versuche, den Eintrag zurückzulegen? Könnte inkonsistent sein
             self.redo_stack.append((move_to_redo, originally_captured_piece))
             return None

    # --- Restliche Methoden bleiben gleich ---

    def get_valid_moves(self) -> List[chess.Move]:
        """Gibt eine Liste aller legalen Züge zurück."""
        try:
            return list(self.board.legal_moves)
        except Exception as e:
            log.error("Exception generating legal moves: %s (FEN: %s)", e, self.board.fen(), exc_info=True)
            return []

    def is_game_over(self) -> bool:
        """Prüft, ob das Spiel beendet ist (inkl. Remis-Claims)."""
        try:
            return self.board.is_game_over(claim_draw=True)
        except Exception as e:
            log.error("Exception during is_game_over check: %s (FEN: %s)", e, self.board.fen(), exc_info=True)
            return False

    def is_game_over_for_ai(self) -> bool:
        """Prüft, ob das Spiel beendet ist (OHNE Remis-Claims)."""
        try:
            return self.board.is_game_over(claim_draw=False)
        except Exception as e:
            log.error("Exception during is_game_over_for_ai check: %s (FEN: %s)", e, self.board.fen(), exc_info=True)
            return False

    def get_game_result(self) -> Optional[str]:
         """Gibt das Ergebnis des Spiels zurück ("1-0", "0-1", "1/2-1/2") oder None."""
         try:
             outcome = self.board.outcome(claim_draw=True)
             return outcome.result() if outcome else None
         except Exception as e:
             log.error("Exception during get_game_result check: %s (FEN: %s)", e, self.board.fen(), exc_info=True)
             return None

    def reset_game(self, fen: Optional[str] = None):
        """Setzt das Spiel zurück und leert Stacks/Listen."""
        log.info("Resetting game state...")
        try:
            if fen:
                log.info("Resetting to FEN: %s", fen)
                self.board.set_fen(fen)
            else:
                log.info("Resetting to standard setup.")
                self.board.reset()
            self.redo_stack.clear()
            self.captured_by_white.clear()
            self.captured_by_black.clear()
            log.info("Game reset complete. Stacks and capture lists cleared.")
        except ValueError:
            log.warning("Invalid FEN '%s' during reset. Using default setup.", fen)
            self.board.reset()
            self.redo_stack.clear()
            self.captured_by_white.clear()
            self.captured_by_black.clear()
        except Exception as e_reset:
            log.error("Exception during game reset: %s. Re-initializing board.", e_reset, exc_info=True)
            self.board = chess.Board()
            self.redo_stack.clear()
            self.captured_by_white.clear()
            self.captured_by_black.clear()

    def get_fen(self) -> str:
        """Gibt die aktuelle Brettstellung als FEN-String zurück."""
        try:
            return self.board.fen()
        except Exception as e:
            log.error("Exception getting FEN: %s", e, exc_info=True)
            return chess.Board().fen()

    @property
    def move_stack(self) -> List[chess.Move]:
         """Gibt den aktuellen Zugstapel (undo stack) zurück."""
         return self.board.move_stack

    @property
    def redo_stack_prop(self) -> List[Tuple[chess.Move, Optional[chess.Piece]]]:
         """Gibt den aktuellen Redo-Stack zurück."""
         return self.redo_stack

    def clear_redo_stack(self):
        """Leert den Redo-Stack."""
        if self.redo_stack:
             log.debug("Clearing redo stack explicitly (size: %d).", len(self.redo_stack))
             self.redo_stack.clear()

    def get_captured_by_white(self) -> List[chess.Piece]:
        """Gibt die Liste der von Weiß geschlagenen (schwarzen) Figuren zurück."""
        return self.captured_by_white

    def get_captured_by_black(self) -> List[chess.Piece]:
        """Gibt die Liste der von Schwarz geschlagenen (weißen) Figuren zurück."""
        return self.captured_by_black

