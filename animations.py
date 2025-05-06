# -*- coding: utf-8 -*-
"""
Dieses Modul enthält die Klasse Animation, die für die visuelle Animation
von Schachfigurenbewegungen auf dem Brett verantwortlich ist.
"""

import pygame, chess, config
# Importiere BoardDisplay und GameState nur für Type Hinting, um Zirkelbezüge zu vermeiden
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from gui.board_display import BoardDisplay
    from game_state import GameState

import logger, logging

# --- Logger Konfiguration (NUR Datei-Logging, mit __name__) ---
log = logger.setup_logger(
    name=__name__,            # Logger-Name ist der Modulname (z.B. 'animations')
    log_file='logs/PyChess.txt', # Loggt in dieselbe Datei wie main.py
    level=logging.DEBUG,      # Loggt alles ab DEBUG-Level
    console=False,            # KEIN Logging in die Konsole
)
log.info("<--- ==================== Starte Modul '%s' ==================== --->", __name__)

class Animation:
    """
    Verwaltet die Animation einer einzelnen Schachfigur von einem Start- zu einem Endfeld.
    """
    def __init__(self, move: chess.Move, piece: chess.Piece, board_display: 'BoardDisplay'):
        """
        Initialisiert die Animation.

        Args:
            move (chess.Move): Der auszuführende Zug.
            piece (chess.Piece): Die Figur, die bewegt wird (vom Startfeld!).
            board_display (BoardDisplay): Das Objekt, das für das Zeichnen des Bretts
                                          und der Figuren verantwortlich ist.
        """
        if piece is None:
             # Dies sollte nicht passieren, wenn start_move_animation korrekt aufgerufen wird
             log.error("Animation.__init__ received None for piece object for move %s.", move.uci())
             raise ValueError("Cannot initialize Animation with None piece.")

        self.move = move
        self.piece = piece # Speichere die Figur direkt
        self.board_display = board_display # Referenz auf das BoardDisplay Objekt speichern
        self.start_square = move.from_square
        self.end_square = move.to_square

        # Hole das Bild für die Figur
        piece_key = f"{'w' if self.piece.color == chess.WHITE else 'b'}{self.piece.symbol().upper()}"
        self.piece_image = config.IMAGES.get(piece_key)
        if not self.piece_image:
            log.warning("Animation.__init__: Image for piece key '%s' not found in config.IMAGES.", piece_key)
            # Optional: Fallback-Bild verwenden oder Fehler auslösen? Aktuell: Animation wird leer sein.

        # Berechne Start- und Endpixelkoordinaten (obere linke Ecke der Felder)
        try:
            start_col, start_row = self.board_display.square_to_coords(self.start_square)
            end_col, end_row = self.board_display.square_to_coords(self.end_square)
        except Exception as e:
            log.error("Error converting squares to coords in Animation.__init__: %s", e, exc_info=True)
            # Setze Standardwerte, um Absturz zu vermeiden, aber Animation wird falsch sein
            start_col, start_row, end_col, end_row = 0, 0, 0, 0

        # Start- und Endpixel (obere linke Ecke)
        self.start_pixel_x = self.board_display.board_offset_x + start_col * config.SQ_SIZE
        self.start_pixel_y = self.board_display.board_offset_y + start_row * config.SQ_SIZE
        self.end_pixel_x = self.board_display.board_offset_x + end_col * config.SQ_SIZE
        self.end_pixel_y = self.board_display.board_offset_y + end_row * config.SQ_SIZE

        # Berechne die Änderung in x und y Richtung pro Frame
        self.total_frames = config.ANIMATION_SPEED
        if self.total_frames <= 0:
            log.warning("Animation speed set to %d, defaulting to 1 frame.", self.total_frames)
            self.total_frames = 1 # Mindestens ein Frame

        # Gesamtdistanz in Pixeln
        delta_x_total = self.end_pixel_x - self.start_pixel_x
        delta_y_total = self.end_pixel_y - self.start_pixel_y

        # Änderung pro Frame
        self.delta_x_per_frame = delta_x_total / self.total_frames
        self.delta_y_per_frame = delta_y_total / self.total_frames

        self.current_frame = 0
        log.debug("Animation initialized for move %s (%s): %d frames.",
                  self.move.uci(), self.piece.symbol(), self.total_frames)

    def update(self) -> bool:
        """
        Aktualisiert den Fortschritt der Animation um einen Frame.

        Returns:
            bool: True, wenn die Animation abgeschlossen ist, sonst False.
        """
        self.current_frame += 1
        finished = self.current_frame >= self.total_frames
        # if finished:
        #     log.debug("Animation for move %s finished after %d frames.", self.move.uci(), self.current_frame)
        return finished

    def draw(self, screen: pygame.Surface):
        """
        Zeichnet den aktuellen Zustand der animierten Figur.

        Args:
            screen (pygame.Surface): Die Oberfläche, auf die gezeichnet wird.
        """
        if not self.piece_image:
            # log.debug("Skipping drawing animation frame for %s, no image.", self.move.uci()) # Kann spammy sein
            return # Nichts zeichnen, wenn kein Bild vorhanden ist

        # Berechne die aktuelle Pixelposition der Figur (obere linke Ecke)
        current_x = self.start_pixel_x + self.delta_x_per_frame * self.current_frame
        current_y = self.start_pixel_y + self.delta_y_per_frame * self.current_frame

        # Zentriere das Bild auf der berechneten Position (optional, je nach gewünschtem Effekt)
        # center_x = current_x + config.SQ_SIZE // 2
        # center_y = current_y + config.SQ_SIZE // 2
        # centered_rect = self.piece_image.get_rect(center=(center_x, center_y))
        # screen.blit(self.piece_image, centered_rect.topleft)

        # Zeichne das Bild an der aktuellen Position (obere linke Ecke)
        screen.blit(self.piece_image, (current_x, current_y))


# Globale Variable, um die aktuell laufende Animation zu speichern
current_animation: Optional[Animation] = None

def start_move_animation(move: chess.Move, piece: chess.Piece, board_display: 'BoardDisplay'):
    """
    Startet eine neue Zuganimation.

    Args:
        move (chess.Move): Der Zug, der animiert werden soll.
        piece (chess.Piece): Die Figur, die bewegt wird (vom Startfeld!).
        board_display (BoardDisplay): Das BoardDisplay-Objekt.
    """
    global current_animation
    # Nur eine Animation gleichzeitig erlauben
    if current_animation is None:
        if piece is None:
             log.error("Attempted to start animation for move %s with piece=None!", move.uci())
             return # Animation nicht starten

        try:
            current_animation = Animation(move, piece, board_display)
            log.info("Animation started for move: %s", move.uci())
        except ValueError as ve:
            log.error("Failed to initialize Animation: %s", ve)
        except Exception as e:
            log.error("Unexpected error starting animation for move %s: %s", move.uci(), e, exc_info=True)
            current_animation = None # Sicherstellen, dass keine fehlerhafte Animation gespeichert wird
    else:
        log.warning("Attempted to start new animation for %s while animation for %s is still running.",
                    move.uci(), current_animation.move.uci())


def update_animation(screen: pygame.Surface, gs: 'GameState', board_display: 'BoardDisplay') -> bool:
    """
    Aktualisiert und zeichnet die laufende Animation, falls vorhanden.
    Diese Funktion sollte in der Hauptschleife aufgerufen werden, *nachdem*
    das statische Brett gezeichnet wurde, aber *bevor* die Figuren gezeichnet werden.

    Args:
        screen (pygame.Surface): Die Hauptzeichenfläche.
        gs (GameState): Der aktuelle Spielzustand (wird *nicht* mehr direkt für die Animation benötigt,
                        aber zum Neuzeichnen des Hintergrunds).
        board_display (BoardDisplay): Das BoardDisplay-Objekt (wird für Neuzeichnen benötigt).

    Returns:
        bool: True, wenn eine Animation läuft, sonst False.
    """
    global current_animation
    if current_animation:
        try:
            # 1. Zeichne das Brett und alle Figuren neu, *außer* der animierten Figur auf ihrem *Startfeld*
            #    (Das Startfeld wird während der Animation als leer behandelt).
            #    Das Zielfeld wird normal gezeichnet (falls eine Figur geschlagen wird).
            board_display.draw_board(screen)
            board_display.draw_coordinates(screen, flipped=gs.board.turn != chess.WHITE) # Beispiel: Koordinaten an Spieler anpassen
            # Zeichne alle Figuren, außer der auf dem Startfeld der Animation
            board_display.draw_pieces(screen, gs.board, exclude_square=current_animation.start_square)
            # Hervorhebungen auch neu zeichnen (z.B. letzter Zug, Schach)
            # Diese Logik muss ggf. aus chess_gui.draw_game_state hierher kopiert oder angepasst werden
            if gs.board.move_stack:
                 last_move = gs.board.peek()
                 board_display.highlight_last_move(screen, last_move)
            board_display.highlight_check(screen, gs.board)


            # 2. Zeichne die animierte Figur an ihrer aktuellen Position
            current_animation.draw(screen)

            # 3. Aktualisiere die Animation
            if current_animation.update():
                # Animation ist beendet
                log.info("Animation finished for move: %s", current_animation.move.uci())
                current_animation = None
                # Optional: Brett nach der Animation final neu zeichnen, um sicherzustellen,
                # dass die Figur korrekt auf dem Zielfeld ist. Ist aber redundant,
                # wenn der nächste Frame sowieso alles neu zeichnet.
                # board_display.draw_game_state(...) # Oder spezifische Zeichenaufrufe
                return False # Keine Animation läuft mehr
            else:
                return True # Animation läuft noch

        except Exception as e:
            log.error("Error during update_animation: %s", e, exc_info=True)
            # Breche die fehlerhafte Animation ab
            current_animation = None
            return False
    else:
        return False # Keine Animation aktiv

def is_animating() -> bool:
    """
    Gibt zurück, ob gerade eine Animation läuft.

    Returns:
        bool: True, wenn eine Animation aktiv ist, sonst False.
    """
    return current_animation is not None
