# -*- coding: utf-8 -*-
"""
Dieses Modul definiert die Klasse BoardDisplay, die für die detaillierte
visuelle Darstellung des Schachbretts, der Figuren, Koordinaten und
Hervorhebungen verantwortlich ist.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import pygame
import chess
import config
import logger
# Importiere GameState nur für Type Hinting, um Zirkelbezüge zu vermeiden
from typing import TYPE_CHECKING, Optional, Tuple
from game_state import GameState
# --- Logger Konfiguration ---
if logger is None:
     print("FEHLER in board_display.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=False,
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

class BoardDisplay:
    """
    Verwaltet die detaillierte Darstellung des Schachbretts und seiner Elemente.
    """
    def __init__(self, width: int, height: int, square_size: int,
                 board_offset_x: int = 0, board_offset_y: int = 0):
        """
        Initialisiert die Brettanzeige.

        Args:
            width (int): Breite des Bretts in Pixeln.
            height (int): Höhe des Bretts in Pixeln.
            square_size (int): Größe eines einzelnen Feldes in Pixeln.
            board_offset_x (int): X-Versatz des Bretts auf dem Bildschirm.
            board_offset_y (int): Y-Versatz des Bretts auf dem Bildschirm.
        """
        self.width = width
        self.height = height
        self.sq_size = square_size
        self.board_offset_x = board_offset_x
        self.board_offset_y = board_offset_y
        self.coord_font = config.COORDINATE_FONT
        self.coord_font = pygame.font.Font(None, config.DEFAULT_FONT_SMALL_SIZE)
        
        log.info("BoardDisplay initialized (Size: %dx%d, Offset: %d,%d, SqSize: %d)",
                 width, height, board_offset_x, board_offset_y, square_size)

    # --- Rest der Methoden bleibt gleich (draw_board, draw_coordinates, etc.) ---
    # (Ich füge sie hier nicht erneut ein, um die Antwort kurz zu halten,
    #  aber sie sind Teil der Klasse und verwenden den Logger wie zuvor)
    def draw_board(self, screen: pygame.Surface):
        """Zeichnet die Quadrate des Schachbretts."""
        try:
            colors = [config.LIGHT_SQUARE_COLOR, config.DARK_SQUARE_COLOR]
            for r in range(8):
                for c in range(8):
                    color_index = (r + c) % 2
                    pygame.draw.rect(screen, colors[color_index], pygame.Rect(
                        self.board_offset_x + c * self.sq_size,
                        self.board_offset_y + r * self.sq_size,
                        self.sq_size, self.sq_size))
        except Exception as e:
            log.error("Error drawing board squares: %s", e, exc_info=True)

    def draw_coordinates(self, screen: pygame.Surface, flipped: bool = False):
        """Zeichnet die algebraischen Koordinaten."""
        if not self.coord_font:
             log.warning("Cannot draw coordinates, font not available.")
             return
        try:
            coord_color_light = config.COORDINATE_TEXT_COLOR_LIGHT
            coord_color_dark = config.COORDINATE_TEXT_COLOR_DARK
            files = "abcdefgh"
            ranks = "12345678"
            if flipped:
                files = files[::-1]
                ranks = ranks[::-1]
            padding = 2
            for i in range(8):
                file_char = files[i]
                is_dark_square_last_rank = (7 + i) % 2 == 1
                if flipped: is_dark_square_last_rank = not is_dark_square_last_rank
                text_color_file = coord_color_light if is_dark_square_last_rank else coord_color_dark
                text_surface_file = self.coord_font.render(file_char, True, text_color_file)
                text_rect_file = text_surface_file.get_rect(bottomright=(
                    self.board_offset_x + (i + 1) * self.sq_size - padding,
                    self.board_offset_y + 8 * self.sq_size - padding ))
                screen.blit(text_surface_file, text_rect_file)

                rank_char = ranks[i]
                is_dark_square_first_file = (i + 0) % 2 == 1
                if flipped: is_dark_square_first_file = not is_dark_square_first_file
                text_color_rank = coord_color_dark if is_dark_square_first_file else coord_color_light
                text_surface_rank = self.coord_font.render(rank_char, True, text_color_rank)
                text_rect_rank = text_surface_rank.get_rect(topleft=(
                    self.board_offset_x + padding,
                    self.board_offset_y + i * self.sq_size + padding ))
                screen.blit(text_surface_rank, text_rect_rank)
        except Exception as e:
            log.error("Error drawing coordinates: %s", e, exc_info=True)

    def draw_pieces(self, screen: pygame.Surface, board: chess.Board, exclude_square: Optional[chess.Square] = None):
        """Zeichnet die Figuren auf dem Brett."""
        try:
            for square_index in chess.SQUARES:
                if square_index == exclude_square: continue
                piece = board.piece_at(square_index)
                if piece:
                    piece_color_char = 'w' if piece.color == chess.WHITE else 'b'
                    piece_symbol_upper = piece.symbol().upper()
                    piece_key = f"{piece_color_char}{piece_symbol_upper}"
                    rank = chess.square_rank(square_index)
                    file = chess.square_file(square_index)
                    pygame_row = 7 - rank
                    pygame_col = file
                    image = config.IMAGES.get(piece_key)
                    if image:
                        pixel_x = self.board_offset_x + pygame_col * self.sq_size
                        pixel_y = self.board_offset_y + pygame_row * self.sq_size
                        image_rect = image.get_rect(center=(pixel_x + self.sq_size // 2, pixel_y + self.sq_size // 2))
                        screen.blit(image, image_rect.topleft)
                    else:
                        log.warning("Image for piece '%s' not found. Drawing fallback.", piece_key)
                        try:
                            fallback_font = config.DEFAULT_FONT_BOLD
                            fallback_text = piece.symbol()
                            fallback_color = config.WHITE if piece.color == chess.WHITE else config.BLACK
                            txt_surf = fallback_font.render(fallback_text, True, fallback_color)
                            txt_rect = txt_surf.get_rect(center=(self.board_offset_x + pygame_col * self.sq_size + self.sq_size // 2,
                                                                  self.board_offset_y + pygame_row * self.sq_size + self.sq_size // 2))
                            screen.blit(txt_surf, txt_rect)
                        except Exception as e_fallback:
                            log.error("Error drawing fallback text for piece %s: %s", piece_key, e_fallback)
        except Exception as e:
            log.error("Error drawing pieces: %s", e, exc_info=True)

    def highlight_square(self, screen: pygame.Surface, square_index: chess.Square, color: Tuple[int, int, int, int]):
        """Hebt ein einzelnes Feld hervor."""
        if not (0 <= square_index <= 63):
            log.warning("Attempted to highlight invalid square index: %s", square_index)
            return
        try:
            col, row = self.square_to_coords(square_index)
            if col == -1: return
            pixel_x = self.board_offset_x + col * self.sq_size
            pixel_y = self.board_offset_y + row * self.sq_size
            highlight_surface = pygame.Surface((self.sq_size, self.sq_size), pygame.SRCALPHA)
            highlight_surface.fill(color)
            screen.blit(highlight_surface, (pixel_x, pixel_y))
        except Exception as e:
            log.error("Error highlighting square %s: %s", square_index, e, exc_info=True)

    def highlight_legal_moves(self, screen: pygame.Surface, board: chess.Board, square_index: chess.Square):
        """Hebt legale Züge hervor."""
        if not config.HIGHLIGHT_LEGAL_MOVES: return
        if not (0 <= square_index <= 63): return
        try:
            piece = board.piece_at(square_index)
            if not piece or piece.color != board.turn: return
            legal_moves = [move for move in board.legal_moves if move.from_square == square_index]
            if not legal_moves: return
            current_time_ms = pygame.time.get_ticks()
            for move in legal_moves:
                target_square = move.to_square
                center_x, center_y = self.get_square_center_coords(target_square)
                if center_x is None: continue
                if board.is_capture(move):
                    pygame.draw.circle(screen, config.HIGHLIGHT_COLOR_LEGAL_CAPTURE[:3], (center_x, center_y), self.sq_size // 2 - 4, 3)
                else:
                    if (current_time_ms % config.LEGAL_MOVE_BLINK_CYCLE_MS) < config.LEGAL_MOVE_BLINK_ON_MS:
                         pygame.draw.circle(screen, config.HIGHLIGHT_COLOR_LEGAL_MOVE[:3], (center_x, center_y), self.sq_size // 6)
        except Exception as e:
            log.error("Error highlighting legal moves for square %s: %s", square_index, e, exc_info=True)

    def highlight_last_move(self, screen: pygame.Surface, move: Optional[chess.Move]):
        """Hebt den letzten Zug hervor."""
        if move:
            try:
                self.highlight_square(screen, move.from_square, config.LAST_MOVE_HIGHLIGHT_COLOR)
                self.highlight_square(screen, move.to_square, config.LAST_MOVE_HIGHLIGHT_COLOR)
            except Exception as e:
                 log.error("Error highlighting last move %s: %s", move.uci(), e, exc_info=True)

    def highlight_check(self, screen: pygame.Surface, board: chess.Board):
        """Hebt den König im Schach hervor."""
        if board.is_check():
            king_square = board.king(board.turn)
            if king_square is not None:
                try:
                    self.highlight_square(screen, king_square, config.CHECK_HIGHLIGHT_COLOR)
                except Exception as e:
                     log.error("Error highlighting king in check at %s: %s", king_square, e, exc_info=True)

    def coords_to_square(self, pixel_x: int, pixel_y: int) -> Tuple[int, int]:
        """Konvertiert Pixelkoordinaten zu Brettkoordinaten."""
        relative_x = pixel_x - self.board_offset_x
        relative_y = pixel_y - self.board_offset_y
        if 0 <= relative_x < self.width and 0 <= relative_y < self.height:
            col = int(relative_x // self.sq_size)
            row = int(relative_y // self.sq_size)
            return col, row
        else:
            return -1, -1

    def square_to_coords(self, square_index: chess.Square) -> Tuple[int, int]:
        """Konvertiert Feldindex zu Brettkoordinaten."""
        if 0 <= square_index <= 63:
            rank = chess.square_rank(square_index)
            file = chess.square_file(square_index)
            pygame_row = 7 - rank
            pygame_col = file
            return pygame_col, pygame_row
        else:
            log.warning("Invalid square index %s provided to square_to_coords.", square_index)
            return -1, -1

    def get_square_center_coords(self, square_index: chess.Square) -> Optional[Tuple[int, int]]:
        """Berechnet die Pixelkoordinaten des Feldmittelpunkts."""
        col, row = self.square_to_coords(square_index)
        if col != -1:
            try:
                center_x = self.board_offset_x + col * self.sq_size + self.sq_size // 2
                center_y = self.board_offset_y + row * self.sq_size + self.sq_size // 2
                return center_x, center_y
            except Exception as e:
                 log.error("Error calculating center coords for square %s: %s", square_index, e, exc_info=True)
                 return None
        else:
            return None

