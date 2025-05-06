# -*- coding: utf-8 -*-
"""
Dieses Modul dient als Brücke zwischen der Spiel-GUI/-Logik und dem TTS-System (tts_utils).
Es formatiert spielspezifische Informationen (Züge, Auswahl) in natürlich klingende
Sprachausgaben und ruft die zentrale `speak`-Funktion auf.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import logger
import chess
import config
import tts_utils
import chess_utils
from typing import Optional
# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in tts_integration.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False, # Konsole auf False setzen
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)
          

# --- Konstanten ---
# Mapping von englischen Figurensymbolen (Großbuchstaben) zu deutschen Namen
PIECE_NAMES_DE = {
    ('w', 'P'): 'Weißer Bauer', ('w', 'N'): 'Weißer Springer', ('w', 'B'): 'Weißer Läufer',
    ('w', 'R'): 'Weißer Turm',  ('w', 'Q'): 'Weiße Königin',    ('w', 'K'): 'Weißer König',
    ('b', 'P'): 'Schwarzer Bauer', ('b', 'N'): 'Schwarzer Springer', ('b', 'B'): 'Schwarzer Läufer',
    ('b', 'R'): 'Schwarzer Turm',  ('b', 'Q'): 'Schwarze Königin',    ('b', 'K'): 'Schwarzer König',
}
log.debug("German piece names map initialized.")

# --- Interne Hilfsfunktionen ---

def _get_color_name_de(color: chess.Color) -> str:
    """Gibt den deutschen Namen für eine Farbe zurück."""
    return "Weiß" if color == chess.WHITE else "Schwarz"

def _get_piece_type_name_de(piece: Optional[chess.Piece]) -> str:
    """
    Gibt den deutschen Typnamen einer Figur zurück (z.B. "Springer", "Bauer").
    Beinhaltet NICHT die Farbe.
    """
    if not piece:
        return ""
    type_map_de = {
        chess.PAWN: "Bauer", chess.KNIGHT: "Springer", chess.BISHOP: "Läufer",
        chess.ROOK: "Turm", chess.QUEEN: "Dame", chess.KING: "König"
    }
    return type_map_de.get(piece.piece_type, piece.symbol().upper()) # Fallback auf Symbol

def _get_full_piece_name_de(piece: Optional[chess.Piece]) -> str:
    """Gibt den vollen deutschen Namen einer Figur zurück (z.B. "Weiß Springer")."""
    if not piece:
        return "Leeres Feld"
    color_char = 'w' if piece.color == chess.WHITE else 'b'
    symbol_upper = piece.symbol().upper()
    return PIECE_NAMES_DE.get((color_char, symbol_upper), symbol_upper) # Fallback auf Symbol


# --- Haupt-Wrapper für Sprachausgabe ---
def speak_text(text: str, interrupt: bool = False):
    """
    Gibt einen beliebigen Text über die TTS-Engine aus, falls TTS aktiviert ist.
    Delegiert direkt an tts_utils.speak.
    """
    if not config.ENABLE_TTS: return
    if text:
        log.debug("Requesting TTS speak: '%s' (Interrupt: %s)", text, interrupt)
        try:
            # Rufe die synchrone speak-Funktion auf
            tts_utils.speak(text, interrupt=interrupt)
        except Exception as e:
            log.error("Error calling tts_utils.speak for text '%s': %s", text, e, exc_info=True)
    else:
        log.debug("Speak_text called with empty text, ignoring.")

# --- Zug-spezifische Sprachausgabe ---
def speak_move_after(board_after_move: chess.Board, move: chess.Move, interrupt: bool = False):
    """
    Formatiert einen Zug NACH dessen Ausführung und gibt ihn detailliert per TTS aus.
    """
    if not config.ENABLE_TTS: return
    try:
        speech_text = format_move_for_speech_post_move(board_after_move, move)
        if speech_text:
            log.debug("Requesting TTS speak for move (post-move): '%s' (UCI: %s)", speech_text, move.uci())
            tts_utils.speak(speech_text, interrupt=interrupt)
        else:
            log.warning("Could not format move %s for speech (post-move).", move.uci())
    except Exception as e:
         log.error("Error in speak_move_after for move %s: %s", move.uci(), e, exc_info=True)


# --- Auswahl-spezifische Sprachausgabe ---
def speak_selection(piece: chess.Piece, square: chess.Square, interrupt: bool = False):
    """
    Gibt die ausgewählte Figur und ihr Feld per TTS aus.
    """
    if not config.ENABLE_TTS or not piece: return
    try:
        square_name = chess_utils.square_to_algebraic(square)
        piece_full_name = _get_full_piece_name_de(piece)
        speech_text = f"{piece_full_name} auf {square_name}"
        log.debug("Requesting TTS speak for selection: '%s'", speech_text)
        tts_utils.speak(speech_text, interrupt=interrupt)
    except Exception as e:
         log.error("Error in speak_selection for piece %s at %s: %s", piece.symbol(), chess.square_name(square), e, exc_info=True)


# --- Formatierungslogik für Züge ---

def format_move_for_speech_post_move(board_after_move: chess.Board, move: chess.Move) -> Optional[str]:
    """
    Formatiert einen Zug SEHR detailliert in eine natürlich klingende deutsche Sprachausgabe.
    Nennt Figurentypen, Felder, geschlagene Figuren, Schach/Matt-Zustand, Gewinner/Remisgrund
    und ob ein Schachgebot abgewehrt wurde.

    Args:
        board_after_move (chess.Board): Das Brett *nachdem* der Zug ausgeführt wurde.
                                        Wird temporär modifiziert (pop/push).
        move (chess.Move): Der ausgeführte Zug.

    Returns:
        str | None: Der formatierte String für die Sprachausgabe oder None bei Fehlern.
    """
    if not move: return None
    log.debug("Formatting move %s for detailed speech...", move.uci())

    original_from_sq = move.from_square
    original_to_sq = move.to_square
    is_promotion = move.promotion is not None

    # Temporäres Board für die Analyse des Zustands *vor* dem Zug
    board_before_move = board_after_move.copy()

    try:
        # --- Informationen über den Zustand NACH dem Zug sammeln ---
        is_check_after = board_after_move.is_check()
        is_checkmate_after = board_after_move.is_checkmate()
        is_game_over_after = board_after_move.is_game_over(claim_draw=True)
        turn_color_after = board_after_move.turn # Wer ist NACH dem Zug dran?

        # --- Informationen über den Zustand VOR dem Zug sammeln (durch pop auf der Kopie) ---
        moved_piece: Optional[chess.Piece] = None
        captured_piece: Optional[chess.Piece] = None
        is_capture = False
        is_castle_kingside = False
        is_castle_queenside = False
        is_en_passant = False
        was_player_in_check_before = False

        try:
            board_before_move.pop() # Zug auf Kopie rückgängig machen
            moved_piece = board_before_move.piece_at(original_from_sq)
            was_player_in_check_before = board_before_move.is_check()
            is_capture = board_before_move.is_capture(move)
            is_en_passant = board_before_move.is_en_passant(move)
            is_castle_kingside = board_before_move.is_kingside_castling(move)
            is_castle_queenside = board_before_move.is_queenside_castling(move)

            if is_capture:
                if is_en_passant:
                    capture_sq = original_to_sq - 8 if moved_piece and moved_piece.color == chess.WHITE else original_to_sq + 8
                    captured_piece = board_before_move.piece_at(capture_sq)
                    if not captured_piece: captured_piece = chess.Piece(chess.PAWN, not moved_piece.color) if moved_piece else None
                    log.debug("En passant capture detected. Captured piece at %s: %s", chess.square_name(capture_sq), captured_piece)
                else:
                    captured_piece = board_before_move.piece_at(original_to_sq)
                    log.debug("Regular capture detected. Captured piece at %s: %s", chess.square_name(original_to_sq), captured_piece)

        except IndexError:
            log.error("IndexError during pop() on board copy in format_move for %s. Analysis might be incomplete.", move.uci())
            moved_piece = board_after_move.piece_at(original_to_sq)
        except Exception as e_pop:
             log.error("Exception during pop() on board copy in format_move for %s: %s", move.uci(), e_pop, exc_info=True)
             return move.uci() # Sicherer Fallback

        if not moved_piece:
            log.error("Could not determine moved piece for move %s. Returning UCI.", move.uci())
            return move.uci()

        # --- Baue den Sprachstring ---
        speech_parts = []
        from_sq_name = chess_utils.square_to_algebraic(original_from_sq)
        to_sq_name = chess_utils.square_to_algebraic(original_to_sq)
        moving_piece_type_name = _get_piece_type_name_de(moved_piece) # Typ ohne Farbe

        # 1. Zugbeschreibung
        if is_castle_kingside: speech_parts.append("Kurze Rochade")
        elif is_castle_queenside: speech_parts.append("Lange Rochade")
        elif is_promotion and move.promotion:
            promo_type_name = _get_piece_type_name_de(chess.Piece(move.promotion, moved_piece.color))
            speech_parts.append(f"Bauer {from_sq_name}")
            if is_capture:
                captured_piece_full_name = _get_full_piece_name_de(captured_piece)
                speech_parts.append(f"schlägt {captured_piece_full_name} auf {to_sq_name}")
            else:
                speech_parts.append(f"nach {to_sq_name}")
            speech_parts.append(f"wird {promo_type_name}")
        else:
            moving_piece_full_name = _get_full_piece_name_de(moved_piece) # Name mit Farbe
            speech_parts.append(f"{moving_piece_full_name} von {from_sq_name}")
            if is_capture:
                captured_piece_full_name = _get_full_piece_name_de(captured_piece)
                speech_parts.append(f"schlägt {captured_piece_full_name} auf {to_sq_name}")
                if is_en_passant: speech_parts.append("en passant")
            else:
                speech_parts.append(f"nach {to_sq_name}")

        # 2. Status nach dem Zug
        status_suffix = ""
        if was_player_in_check_before and not is_check_after and not is_checkmate_after:
             status_suffix = ". Nicht mehr im Schach"
        elif is_game_over_after:
            game_over_reason = chess_utils.get_game_over_text(board_after_move)
            if game_over_reason: status_suffix = f". {game_over_reason}"
        elif is_check_after:
             checked_color_name = _get_color_name_de(turn_color_after)
             status_suffix = f". {checked_color_name} im Schach"

        if status_suffix: speech_parts.append(status_suffix)

        # Kombiniere die Teile
        final_speech_text = " ".join(speech_parts)
        log.debug("Formatted speech: '%s'", final_speech_text)
        return final_speech_text

    except Exception as e:
        log.error("Exception formatting move %s for speech: %s", move.uci(), e, exc_info=True)
        return move.uci() # Fallback auf UCI


# --- Formatierung basierend auf SAN (Alternative, weniger detailliert) ---
def format_move_for_speech_from_san(san: str) -> str:
    """Formatiert eine SAN-Notation in eine einfachere Sprachausgabe."""
    if not san: return ""
    log.debug("Formatting SAN '%s' for simple speech...", san)
    try:
        speech_text = san; original_san = san
        if san == "O-O": return "Kurze Rochade"
        if san == "O-O-O": return "Lange Rochade"

        check_suffix = ""
        if speech_text.endswith('#'): check_suffix = ", Schachmatt"; speech_text = speech_text[:-1]
        elif speech_text.endswith('+'): check_suffix = ", Schach"; speech_text = speech_text[:-1]

        promo_suffix = ""
        if '=' in speech_text:
            parts = speech_text.split('=')
            field_part = parts[0]
            promo_symbol = parts[1]
            promo_type_name = _get_piece_type_name_de(chess.Piece.from_symbol(promo_symbol))
            base_move = field_part.replace('x', ' schlägt ') if 'x' in field_part else f"nach {field_part}"
            speech_text = f"{base_move} wird {promo_type_name}"
            promo_suffix = " (Umwandlung)"
        else:
            if speech_text and speech_text[0].upper() in ['P', 'N', 'B', 'R', 'Q', 'K']:
                piece_symbol = speech_text[0].upper()
                piece_type_name = _get_piece_type_name_de(chess.Piece.from_symbol(piece_symbol))
                rest = speech_text[1:]
                separator = "" if rest.startswith('x') else " "
                speech_text = piece_type_name + separator + rest
            speech_text = speech_text.replace('x', ' schlägt ')

        speech_text += promo_suffix
        speech_text += check_suffix
        final_text = " ".join(speech_text.split())
        log.debug("Formatted SAN '%s' to '%s'", original_san, final_text)
        return final_text.strip()
    except Exception as e:
        log.error("Error formatting SAN '%s' for speech: %s", san, e, exc_info=True)
        return san # Fallback auf Original-SAN

def speak_san(san_move: str, interrupt: bool = False):
    """Formatiert eine SAN-Notation und gibt sie per TTS aus."""
    if not config.ENABLE_TTS: return
    try:
        speech_text = format_move_for_speech_from_san(san_move)
        if speech_text:
            log.debug("Requesting TTS speak for SAN: '%s' (Original: %s)", speech_text, san_move)
            tts_utils.speak(speech_text, interrupt=interrupt)
        else:
            log.warning("Could not format SAN '%s' for speech.", san_move)
    except Exception as e:
        log.error("Error in speak_san for SAN '%s': %s", san_move, e, exc_info=True)

