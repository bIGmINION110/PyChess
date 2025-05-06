# -*- coding: utf-8 -*-
"""
Dieses Modul stellt Hilfsfunktionen für die Schachlogik bereit,
einschließlich der Konvertierung von Zügen in die Schachnotation,
der Überprüfung von Spielende-Bedingungen und anderer schachspezifischer Utilities.
Es interagiert primär mit der `python-chess` Bibliothek und der `config.py`.
"""
import chess, config
from typing import Optional # Für Type Hinting
import logger, logging

# --- Logger Konfiguration (NUR Datei-Logging, mit __name__) ---
log = logger.setup_logger(
    name=__name__,            # Logger-Name ist der Modulname (z.B. 'chess_utils')
    log_file='logs/PyChess.txt', # Loggt in dieselbe Datei wie andere Module
    level=logging.DEBUG,      # Loggt alles ab DEBUG-Level
    console=False,            # KEIN Logging in die Konsole
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

def get_move_notation(board: chess.Board, move: chess.Move) -> str:
    """
    Konvertiert einen Zug in die Standard Algebraic Notation (SAN).

    Args:
        board (chess.Board): Das aktuelle Schachbrett (Zustand *vor* dem Zug).
        move (chess.Move): Der zu konvertierende Zug.

    Returns:
        str: Der Zug in SAN-Notation (z.B. "Nf3", "e4", "O-O").
             Gibt die UCI-Notation zurück, wenn SAN fehlschlägt.
    """
    try:
        # Versuche, die SAN-Notation vom Brett zu erhalten.
        san_notation = board.san(move)
        # log.debug("Converted move %s to SAN: %s", move.uci(), san_notation) # Optional: Für Debugging
        return san_notation
    except ValueError as ve:
        # Wenn SAN fehlschlägt (z.B. bei illegalem Zug)
        uci_move = move.uci()
        log.warning("Could not get SAN for move %s (ValueError: %s). Using UCI notation.", uci_move, ve)
        return uci_move
    except Exception as e:
        # Andere unerwartete Fehler abfangen
        uci_move = move.uci()
        log.error("Unexpected error getting SAN for move %s: %s. Using UCI notation.", uci_move, e, exc_info=True)
        return uci_move


def get_game_over_text(board: chess.Board) -> Optional[str]:
    """
    Ermittelt den Text, der angezeigt werden soll, wenn das Spiel endet.

    Args:
        board (chess.Board): Das Schachbrett im Endzustand.

    Returns:
        str | None: Eine Zeichenkette, die das Ergebnis beschreibt (z.B. "Schachmatt! Schwarz gewinnt.", "Patt!"),
                    oder None, wenn das Spiel noch nicht beendet ist.
    """
    # outcome() prüft alle Endbedingungen, claim_draw=True berücksichtigt 3/5-fache Wiederholung und 50/75-Züge-Regel
    try:
        outcome = board.outcome(claim_draw=True)
    except Exception as e:
         # Seltene Fehler in outcome() abfangen
         log.error("Error getting board outcome: %s (FEN: %s)", e, board.fen(), exc_info=True)
         return "Spiel beendet (Fehler bei Ergebnisprüfung)"


    if outcome:
        termination_reason = outcome.termination
        winner = outcome.winner
        result = outcome.result() # "1/2-1/2", "1-0", "0-1"
        log.info("Game over detected. Reason: %s, Winner: %s, Result: %s",
                 termination_reason.name, winner, result)

        if termination_reason == chess.Termination.CHECKMATE:
            winning_color = "Weiß" if winner == chess.WHITE else "Schwarz"
            return f"Schachmatt! {winning_color} gewinnt."
        elif termination_reason == chess.Termination.STALEMATE:
            return "Patt!"
        elif termination_reason == chess.Termination.INSUFFICIENT_MATERIAL:
            return "Unzureichendes Material! Remis."
        elif termination_reason == chess.Termination.SEVENTYFIVE_MOVES:
            return "75-Züge-Regel! Remis."
        elif termination_reason == chess.Termination.FIVEFOLD_REPETITION:
            return "Fünffache Stellungswiederholung! Remis."
        elif termination_reason == chess.Termination.FIFTY_MOVES: # Wird durch claim_draw=True abgedeckt
            return "50-Züge-Regel! Remis."
        elif termination_reason == chess.Termination.THREEFOLD_REPETITION: # Wird durch claim_draw=True abgedeckt
            return "Dreifache Wiederholung! Remis."
        # Weitere mögliche Gründe (Variantenschach etc.) könnten hier hinzugefügt werden
        else:
            # Allgemeiner Remis-Text oder spezifischerer Text je nach termination_reason
            # Ersetze Unterstriche und mache Titel-Case für bessere Lesbarkeit
            reason_text = termination_reason.name.replace('_', ' ').title()
            log.info("Game ended with reason: %s. Result: %s", reason_text, result)
            return f"Spiel beendet: {reason_text}. Ergebnis: {result}"
    else:
        # Spiel ist nicht vorbei
        # log.debug("get_game_over_text: Game is not over.") # Nicht nötig, dies zu loggen
        return None

def is_capture(board: chess.Board, move: chess.Move) -> bool:
    """
    Überprüft, ob ein gegebener Zug ein Schlagzug ist (inkl. en passant).

    Args:
        board (chess.Board): Das aktuelle Schachbrett (Zustand *vor* dem Zug).
        move (chess.Move): Der zu überprüfende Zug.

    Returns:
        bool: True, wenn der Zug ein Schlagzug ist, sonst False.
    """
    try:
        return board.is_capture(move)
    except Exception as e:
        # Fängt Fehler ab, falls der Zug ungültig für das Brett ist
        log.warning("Error checking if move %s is capture: %s", move.uci(), e, exc_info=True)
        return False

def is_check(board: chess.Board, move: chess.Move) -> bool:
    """
    Überprüft, ob ein gegebener Zug den gegnerischen König ins Schach setzt.
    Wichtig: Diese Funktion modifiziert das Brett temporär!

    Args:
        board (chess.Board): Das aktuelle Schachbrett (Zustand *vor* dem Zug).
        move (chess.Move): Der zu überprüfende Zug.

    Returns:
        bool: True, wenn der Zug Schach gibt, sonst False.
              Gibt False zurück, wenn der Zug nicht legal ist oder ein Fehler auftritt.
    """
    is_check_flag = False
    try:
        # Führe den Zug temporär aus, um das Ergebnis zu prüfen
        board.push(move)
        is_check_flag = board.is_check()
    except ValueError:
        # Der Zug war nicht legal
        log.warning("is_check() called with illegal move %s for FEN %s", move.uci(), board.fen())
        return False # Illegaler Zug kann kein Schach geben
    except Exception as e:
        log.error("Unexpected error during board.push() in is_check() for move %s: %s", move.uci(), e, exc_info=True)
        return False # Bei Fehler annehmen, dass es kein Schach ist
    finally:
        # Mache den Zug *immer* rückgängig, wenn push erfolgreich war oder auch nicht (um sicherzugehen)
        # Prüfe, ob der Stack leer ist, bevor pop aufgerufen wird
        if board.move_stack:
            try:
                board.pop()
            except IndexError:
                 # Sollte nicht passieren, wenn push erfolgreich war, aber sicher ist sicher
                 log.warning("IndexError during board.pop() in is_check() for move %s, stack might be inconsistent.", move.uci())
            except Exception as e:
                 log.error("Unexpected error during board.pop() in is_check() for move %s: %s", move.uci(), e, exc_info=True)
                 # Board könnte in inkonsistentem Zustand sein!

    # log.debug("Checked if move %s gives check: %s", move.uci(), is_check_flag) # Optional
    return is_check_flag

def get_piece_value(piece: Optional[chess.Piece]) -> int:
    """
    Gibt den Materialwert einer Figur zurück, basierend auf der Konfiguration.

    Args:
        piece (chess.Piece | None): Die Figur oder None.

    Returns:
        int: Der Wert der Figur (z.B. 1 für Bauer, 9 für Dame).
             Gibt 0 zurück, wenn die Figur None ist oder der Typ unbekannt ist.
    """
    if piece:
        # Greift auf das PIECE_VALUES Dictionary in config.py zu
        value = config.PIECE_VALUES.get(piece.piece_type, 0)
        # log.debug("Value for piece type %s: %d", piece.piece_type, value) # Optional
        return value
    return 0

def square_to_algebraic(square: chess.Square) -> str:
    """
    Konvertiert einen Feldindex (0-63) in die algebraische Notation (z.B. "a1", "h8").

    Args:
        square (int): Der Feldindex (0-63).

    Returns:
        str: Das Feld in algebraischer Notation.
    """
    try:
        return chess.square_name(square)
    except Exception as e:
        log.error("Error converting square index %d to algebraic notation: %s", square, e, exc_info=True)
        return "??" # Fallback

def algebraic_to_square(algebraic_notation: str) -> Optional[chess.Square]:
    """
    Konvertiert die algebraische Notation eines Feldes (z.B. "e4") in den Feldindex (0-63).

    Args:
        algebraic_notation (str): Das Feld in algebraischer Notation (Groß-/Kleinschreibung egal).

    Returns:
        int | None: Der Feldindex (0-63) oder None, wenn die Notation ungültig ist.
    """
    try:
        # stellt sicher, dass die Notation klein geschrieben ist, wie von parse_square erwartet
        square_index = chess.parse_square(algebraic_notation.lower())
        return square_index
    except ValueError:
        # Dies ist ein erwarteter Fehler bei ungültiger Eingabe, daher nur Debug-Log
        log.debug("Invalid algebraic notation provided: '%s'", algebraic_notation)
        return None
    except Exception as e:
        log.error("Unexpected error parsing algebraic notation '%s': %s", algebraic_notation, e, exc_info=True)
        return None

def get_square_color(square: chess.Square) -> tuple:
    """
    Gibt die Farbe (hell oder dunkel) eines Feldes zurück, basierend auf config.

    Args:
        square (int): Der Feldindex (0-63).

    Returns:
        tuple: Die RGB-Farbe des Feldes (z.B. config.LIGHT_SQUARE_COLOR).
               Gibt im Fehlerfall eine Standardfarbe zurück.
    """
    try:
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        # Felder sind hell, wenn Summe von Rang und Zeile gerade ist (oder ungerade, je nach a1)
        # Annahme: a1 (Index 0) ist dunkel. rank=0, file=0 -> sum=0 (gerade) -> dunkel
        if (rank + file) % 2 == 0:
            return config.DARK_SQUARE_COLOR
        else:
            return config.LIGHT_SQUARE_COLOR
    except Exception as e:
         log.error("Error determining square color for index %d: %s", square, e, exc_info=True)
         return (255, 0, 255) # Magenta als Fehlerfarbe

def get_piece_color_char(piece: chess.Piece) -> str:
    """
    Gibt die Farbe einer Figur als Kleinbuchstaben zurück ('w' oder 'b').
    Nützlich für den Zugriff auf Figurenbilder im config.IMAGES Dict.

    Args:
        piece (chess.Piece): Die Figur.

    Returns:
        str: 'w' für Weiß, 'b' für Schwarz. Gibt '?' bei Fehler zurück.
    """
    try:
        return 'w' if piece.color == chess.WHITE else 'b'
    except AttributeError: # Falls piece None oder kein chess.Piece ist
         log.warning("get_piece_color_char called with invalid piece object: %s", piece)
         return '?'
    except Exception as e:
         log.error("Unexpected error in get_piece_color_char: %s", e, exc_info=True)
         return '?'


def get_piece_symbol_upper(piece: chess.Piece) -> str:
    """
    Gibt das Symbol einer Figur als Großbuchstaben zurück (z.B. 'P', 'N', 'Q').

    Args:
        piece (chess.Piece): Die Figur.

    Returns:
        str: Der Großbuchstabe des Figurensymbols. Gibt '?' bei Fehler zurück.
    """
    try:
        return piece.symbol().upper()
    except AttributeError: # Falls piece None oder kein chess.Piece ist
         log.warning("get_piece_symbol_upper called with invalid piece object: %s", piece)
         return '?'
    except Exception as e:
         log.error("Unexpected error in get_piece_symbol_upper: %s", e, exc_info=True)
         return '?'

# Entferne get_piece_color, da es nicht verwendet wird und get_piece_color_char existiert.
# def get_piece_color(piece: chess.Piece) -> str:
#     """
#     Gibt die Farbe einer Figur als String zurück (z.B. 'Weiß' oder 'Schwarz').
#     """
#     return 'Weiß' if piece.color == chess.WHITE else 'Schwarz'

