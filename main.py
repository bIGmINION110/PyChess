# -*- coding: utf-8 -*-
"""
Hauptmodul für das PyChess-Spiel.
Initialisiert Pygame, lädt Ressourcen, verwaltet die Spielzustände
(Menü, Spiel, Animationen) und enthält die Hauptschleife.
"""
# Standardbibliothek-Imports zuerst
import logging
import sys # Für kritische Fehler
import os # Für sys.path Manipulation (Fallback)
import queue
import threading
from typing import List, Tuple, Any # Für Type Hinting
import pygame
# Importiere file_io hier nicht mehr direkt, save/load läuft über save_load_logic
import config
import ai_opponent
from game_state import GameState
import animations
import chess_utils
import event_handler
import chess
import logger

# --- Logger Konfiguration (NUR Datei-Logging, mit __name__) ---
if logger is None:
     print("FEHLER in main.py: Logger-Modul ist None nach Importversuch.", file=sys.stderr)
     sys.exit("Logger konnte nicht initialisiert werden.")
log = logger.setup_logger(
    name=__name__,            # Logger-Name ist '__main__'
    log_file='logs/PyChess.txt', # Loggt in diese Datei
    level=logging.DEBUG,      # Loggt alles ab DEBUG-Level
    console=False,            # KEIN Logging in die Konsole
)
log.info("<--- ==================== Starte Hauptmodul '%s' ==================== --->", __name__)

# --- GUI-Komponenten importieren (aus dem gui-Paket) ---
from gui.board_display import BoardDisplay
from gui import startup_logic
from gui import tts_integration
from gui import fullscreen_logic
from gui import timer_logic
from gui import status_display
from gui import menu_logic
from gui import chess_gui
from gui import save_load_logic # Geändert: save/load wird jetzt hierüber aufgerufen
from gui import navigation_logic # Für Aktionen nach Undo/Redo
log.debug("Alle GUI-Module erfolgreich importiert.")

 # Pygame importieren, nachdem andere Module geladen sind

# --- Globale Variable für Hintergrundmusik-Status ---
_background_music_loaded = False

def main():
    """
    Initialisiert das Spiel und startet die Hauptschleife mit Zustandsmaschine.
    """
    log.debug("Entering main() function.")
    global _background_music_loaded # Zugriff auf globale Variable

    # --- Pygame Initialisierung ---
    log.info("Initializing Pygame...")
    try:
        pygame.init()
        log.info("Pygame initialized successfully.")
    except Exception as e:
        log.critical("CRITICAL: Pygame initialization failed: %s", e, exc_info=True)
        print(f"!!! CRITICAL PYGAME INIT ERROR: {e} !!!", file=sys.stderr)
        sys.exit("Pygame konnte nicht initialisiert werden.")


    # --- Mixer Initialisierung ---
    if config.ENABLE_SOUNDS:
        log.info("Attempting to initialize Pygame Mixer...")
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            config.mixer_initialized = True
            log.info("Mixer initialized successfully.")
        except pygame.error as e:
            log.warning("Mixer initialization failed: %s", e, exc_info=True)
            log.warning("Possible causes: No audio device, driver issue.")
            log.warning("Sounds will be disabled for this session.")
            config.ENABLE_SOUNDS = False
            config.mixer_initialized = False
    else:
        log.info("Sound effects are disabled in config. Skipping Mixer initialization.")
        config.mixer_initialized = False


    # --- Fenster und Display initialisieren ---
    log.info("Setting display mode: %dx%d, Resizable", config.WIDTH, config.HEIGHT)
    try:
        screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(config.MAIN_MENU_TITLE)
        log.info("Display initialized.")
    except pygame.error as e:
        log.critical("Failed to set display mode: %s", e, exc_info=True)
        print(f"!!! CRITICAL DISPLAY INIT ERROR: {e} !!!", file=sys.stderr)
        pygame.quit()
        sys.exit("Display could not be initialized.")

    if not pygame.display.get_init():
        log.critical("Pygame Display is not initialized after set_mode()!")
        print("!!! CRITICAL: Pygame Display not initialized after set_mode() !!!", file=sys.stderr)
        pygame.quit()
        sys.exit("Display could not be initialized (check after set_mode).")

    # --- Bilder laden ---
    log.info("Loading images...")
    try:
        config.load_images() # Bilder laden, NACHDEM Display initialisiert ist
        log.info("Images loaded successfully.")
    except Exception as e:
        log.error("Error loading images: %s", e, exc_info=True)


    # --- Icon setzen ---
    log.debug("Attempting to set application icon...")
    try:
        icon_path_png = os.path.join(config.IMAGE_DIR, f'bK{config.IMAGE_FILE_TYPE}')
        icon_path_svg = os.path.join(config.IMAGE_DIR, f'bK{config.FALLBACK_IMAGE_FILE_TYPE}')
        icon_path_to_load = None
        if os.path.exists(icon_path_png):
             icon_path_to_load = icon_path_png
             log.debug("Found primary icon file: %s", icon_path_png)
        elif os.path.exists(icon_path_svg):
             icon_path_to_load = icon_path_svg
             log.info("Primary icon not found, using fallback SVG icon: %s", icon_path_svg)
        else:
             log.warning("Application icon file not found. Tried: '%s' and '%s'", icon_path_png, icon_path_svg)

        if icon_path_to_load:
            pygame.display.set_icon(pygame.image.load(icon_path_to_load))
            log.info("Application icon set to: %s", icon_path_to_load)
    except Exception as e:
        log.warning("Could not load or set application icon: %s", e, exc_info=True)

    clock = pygame.time.Clock()

    # --- Sounds laden ---
    if config.mixer_initialized:
        log.info("Loading sounds...")
        try:
            config.load_sounds()
            log.info("Sounds loaded.")
        except Exception as e:
            log.error("Error loading sounds: %s", e, exc_info=True)

        # --- Hintergrundmusik laden ---
        log.debug("Attempting to load background music...")
        try:
            music_filename = config.SOUND_FILES.get('BackgroundMusic', (None, None))[0]
            if music_filename:
                music_path = os.path.join(config.SOUND_DIR, music_filename)
                if os.path.exists(music_path):
                    pygame.mixer.music.load(music_path)
                    _background_music_loaded = True
                    log.info("Background music loaded: %s", music_path)
                else:
                    log.warning("Background music file not found: %s", music_path)
                    _background_music_loaded = False
            else:
                log.warning("No entry 'BackgroundMusic' found in config.SOUND_FILES.")
                _background_music_loaded = False
        except pygame.error as e:
            log.error("Pygame error loading background music: %s", e, exc_info=True)
            _background_music_loaded = False
        except Exception as e:
            log.error("Unexpected error loading background music: %s", e, exc_info=True)
            _background_music_loaded = False
    else:
        log.info("Mixer not initialized, skipping loading sounds and music.")

    # --- Spiel-Objekte initialisieren ---
    log.debug("Initializing GameState object...")
    gs = GameState()
    log.debug("Initializing BoardDisplay object...")
    board_display = BoardDisplay(config.BOARD_WIDTH, config.BOARD_HEIGHT, config.SQ_SIZE,
                                 config.BOARD_OFFSET_X, config.BOARD_OFFSET_Y)
    event_handler.reset_selection()
    log.debug("Game objects initialized.")

    # --- Initialisiere Hauptmenü ---
    log.info("Initializing main menu UI.")
    startup_logic.initialize_main_menu()

    # Game-Start Sound beim Anwendungsstart abspielen
    if config.ENABLE_SOUNDS and config.mixer_initialized:
        config.play_sound('game_start')
        log.debug("Played 'game_start' sound at application startup.")

    # --- Zustandsmaschine ---
    app_state = 'MAIN_MENU' # Startzustand
    log.info("Entering main loop. Initial state: '%s'", app_state)
    animation_progress = 0
    board_slide_y_offset = 0
    piece_setup_index = 0
    piece_setup_timer = 0
    start_pieces_with_squares: List[Tuple[int, Any]] = []

    # --- GUI-Zustandsvariablen für den 'GAME' Zustand ---
    # Wird jetzt auch an save_load_logic übergeben
    game_gui_state = {
        'menu_active': False,
        'game_over': False,
        'player_turn_finished': False,
        'ai_thinking': False,
        'exit_requested': False,
        'last_move': None,
        'board_flipped': False
    }
    log.debug("Initial game GUI state: %s", game_gui_state)


    # Initialisiere TTS für Hauptmenü
    if config.ENABLE_TTS:
        log.debug("Initializing TTS for main menu...")
        try:
            if hasattr(startup_logic, 'MAIN_MENU_LAYOUT') and startup_logic.MAIN_MENU_LAYOUT:
                first_item_text = startup_logic.MAIN_MENU_LAYOUT[0]["text"]
                tts_integration.speak_text(f"Hauptmenü. {first_item_text}", interrupt=True)
                log.debug("Spoke main menu welcome via TTS.")
            else:
                log.warning("MAIN_MENU_LAYOUT not found or empty in startup_logic. Cannot speak welcome message.")
                tts_integration.speak_text("Hauptmenü", interrupt=True) # Fallback
        except (IndexError, KeyError, AttributeError) as e:
            log.warning("Could not get first menu item text for TTS welcome: %s", e)
            tts_integration.speak_text("Hauptmenü", interrupt=True) # Fallback
        except Exception as e:
            log.error("Error during initial TTS speak: %s", e, exc_info=True)


    running = True

    # --- KI-Thread Management ---
    ai_move_queue = queue.Queue()
    ai_thread = None

    # --- Hauptschleife ---
    while running:
        current_time_ms = pygame.time.get_ticks()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                log.info("QUIT event received. Initiating shutdown.")
                running = False
                if app_state == 'GAME' and ai_thread and ai_thread.is_alive():
                    log.warning("AI thread still alive during shutdown request.")
                continue # Direkt zur nächsten Iteration (oder Schleifenende)

            if event.type == pygame.VIDEORESIZE:
                if not fullscreen_logic.get_fullscreen_state():
                    old_width, old_height = config.WIDTH, config.HEIGHT
                    new_w, new_h = event.w, event.h
                    config.WIDTH = max(new_w, config.BOARD_WIDTH + 40)
                    config.HEIGHT = max(new_h, config.BOARD_HEIGHT + 80)
                    log.info("VIDEORESIZE event: Attempting resize from %dx%d to %dx%d", old_width, old_height, config.WIDTH, config.HEIGHT)
                    try:
                        screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
                        config.BOARD_OFFSET_X = (config.WIDTH - config.BOARD_WIDTH) // 2
                        config.BOARD_OFFSET_Y = (config.HEIGHT - config.BOARD_HEIGHT) // 2
                        if board_display:
                            board_display.board_offset_x = config.BOARD_OFFSET_X
                            board_display.board_offset_y = config.BOARD_OFFSET_Y
                        config.STATUS_POS_X = config.WIDTH // 2
                        log.info("Window resized successfully to %dx%d", config.WIDTH, config.HEIGHT)
                    except pygame.error as e:
                        log.error("Error handling window resize: %s", e, exc_info=True)
                        config.WIDTH, config.HEIGHT = old_width, old_height
                        log.warning("Reverted to previous window size due to error.")
                        try:
                            screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
                            log.info("Successfully reverted display mode to %dx%d", config.WIDTH, config.HEIGHT)
                        except pygame.error as revert_e:
                            log.critical("Failed to revert display mode after resize error: %s", revert_e, exc_info=True)
                            running = False # Abbruch

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    log.info("F11 key pressed, toggling fullscreen...")
                    try:
                       screen = fullscreen_logic.toggle_fullscreen(screen)
                       new_width, new_height = screen.get_size()
                       config.WIDTH, config.HEIGHT = new_width, new_height
                       config.BOARD_OFFSET_X = (config.WIDTH - config.BOARD_WIDTH) // 2
                       config.BOARD_OFFSET_Y = (config.HEIGHT - config.BOARD_HEIGHT) // 2
                       if board_display:
                           board_display.board_offset_x = config.BOARD_OFFSET_X
                           board_display.board_offset_y = config.BOARD_OFFSET_Y
                       config.STATUS_POS_X = config.WIDTH // 2
                       log.info("Fullscreen toggled. New window size: %dx%d", new_width, new_height)
                    except Exception as e:
                        log.error("Error toggling fullscreen: %s", e, exc_info=True)
                    continue # F11 verarbeitet

        # --- Hintergrund zeichnen ---
        screen.fill(config.WINDOW_BACKGROUND_COLOR)
        if app_state in ['MAIN_MENU', 'NEW_GAME_SUBMENU', 'ANIMATING_TO_SUB', 'ANIMATING_TO_MAIN']:
            # Sicherstellen, dass die Funktionen existieren
            if hasattr(startup_logic, '_update_background_game') and callable(startup_logic._update_background_game) and \
               hasattr(startup_logic, '_draw_background_game') and callable(startup_logic._draw_background_game):
                startup_logic._update_background_game()
                startup_logic._draw_background_game(screen)
            else:
                log.debug("Background game update/draw functions not found in startup_logic.")


        # --- Zustandsabhängige Logik und Zeichnen ---
        current_app_state = app_state # Für Logging des Wechsels

        # === ZUSTAND: MAIN_MENU ===
        if app_state == 'MAIN_MENU':
            action = startup_logic.run_main_menu_frame(screen, clock, events)
            if action: log.debug("Main menu action received: '%s'", action)
            if action == 'SHOW_NEW_GAME_SUBMENU':
                log.info("Changing state from '%s' to 'ANIMATING_TO_SUB'", current_app_state)
                app_state = 'ANIMATING_TO_SUB'
                animation_progress = 0
                if config.ENABLE_TTS: tts_integration.speak_text("Modi wählen", interrupt=True)
            elif action == 'LOAD':
                log.info("Load game action selected. Attempting to load...")
                # Rufe die angepasste Ladefunktion auf, die gs und gui_state aktualisiert
                if save_load_logic.load_game(gs, game_gui_state):
                    log.info("Game loaded successfully.")
                    if config.mixer_initialized: pygame.mixer.music.stop(); log.debug("Stopped background music (if playing).")
                    # Setze GUI-Status basierend auf geladenem Zustand
                    game_gui_state['game_over'] = gs.is_game_over()
                    game_gui_state['menu_active'] = False
                    game_gui_state['player_turn_finished'] = False
                    game_gui_state['ai_thinking'] = False
                    game_gui_state['last_move'] = gs.board.peek() if gs.board.move_stack else None
                    # board_flipped wurde bereits in load_game gesetzt

                    log.debug("Updated game GUI state after load: %s", game_gui_state)
                    status_display.update_default_status(gs) # Aktualisiere "Wer ist am Zug"-Anzeige

                    # Starte Musik und Timer nur, wenn das Spiel nicht vorbei ist
                    if not game_gui_state['game_over']:
                        if _background_music_loaded and config.mixer_initialized:
                            log.debug("Attempting to start background music for loaded game.")
                            try: pygame.mixer.music.play(-1); log.info("Background music started.")
                            except pygame.error as e: log.error("Error starting background music after load: %s", e, exc_info=True)
                        timer_logic.start_game_timer()
                        log.debug("Started game timer.")
                    else:
                        log.debug("Game loaded is already over. Timer remains stopped.")

                    log.info("Changing state from '%s' to 'GAME'", current_app_state)
                    app_state = 'GAME'
                    event_handler.reset_selection() # Auswahl zurücksetzen
                else:
                    log.info("Game load failed or was cancelled. Staying in main menu.")
            elif action == 'QUIT':
                log.info("Quit action selected from main menu.")
                running = False

        # === ZUSTAND: NEW_GAME_SUBMENU ===
        elif app_state == 'NEW_GAME_SUBMENU':
            action = startup_logic.run_new_game_submenu_frame(screen, clock, events)
            if action: log.debug("New game submenu action received: '%s'", action)
            if action == 'START_LOCAL' or action == 'START_AI':
                game_type = 'Local' if action == 'START_LOCAL' else 'vs AI'
                log.info("Starting new game (%s).", game_type)
                if config.mixer_initialized: pygame.mixer.music.stop(); log.debug("Stopped background music (if playing).")
                gs.reset_game()
                gs.board.clear_board() # Brett leeren vor Animation
                log.debug("GameState reset, board cleared.")
                # Setze AI Konfiguration basierend auf Auswahl
                config.AI_ENABLED = (action == 'START_AI')
                if config.AI_ENABLED:
                    config.AI_PLAYER = chess.BLACK # Standardmäßig spielt AI Schwarz
                    log.info("AI Enabled set to: True, Player: BLACK, Depth: %d", config.AI_DEPTH)
                else:
                    log.info("AI Enabled set to: False")

                # Setze GUI Status zurück
                game_gui_state.update({
                    'menu_active': False, 'game_over': False, 'player_turn_finished': False,
                    'ai_thinking': False, 'last_move': None, 'board_flipped': False
                })
                log.debug("Reset game GUI state: %s", game_gui_state)
                event_handler.reset_selection()


                log.info("Changing state from '%s' to 'ANIMATING_BOARD_SLIDE'", current_app_state)
                app_state = 'ANIMATING_BOARD_SLIDE'
                animation_progress = 0
                board_slide_y_offset = -config.BOARD_HEIGHT
                config.play_sound('BoardSlide')

            elif action == 'START_ONLINE':
                 log.info("Start Online selected (currently redirects to main menu).")
                 log.info("Changing state from '%s' to 'ANIMATING_TO_MAIN'", current_app_state)
                 app_state = 'ANIMATING_TO_MAIN'
                 animation_progress = 0
                 if config.ENABLE_TTS: tts_integration.speak_text("Hauptmenü", interrupt=True)
            elif action == 'BACK_TO_MAIN':
                 log.info("Back to Main selected from submenu.")
                 log.info("Changing state from '%s' to 'ANIMATING_TO_MAIN'", current_app_state)
                 app_state = 'ANIMATING_TO_MAIN'
                 animation_progress = 0
                 if config.ENABLE_TTS: tts_integration.speak_text("Hauptmenü", interrupt=True)

        # === ZUSTAND: ANIMATING_TO_SUB ===
        elif app_state == 'ANIMATING_TO_SUB':
            progress_ratio = min(animation_progress / config.MENU_SLIDE_FRAMES, 1.0)
            panel_width = 300; target_x = config.WIDTH - panel_width - 30; start_x = config.WIDTH
            current_x = start_x + (target_x - start_x) * progress_ratio
            if hasattr(startup_logic, '_draw_menu_panel') and callable(startup_logic._draw_menu_panel):
                startup_logic._draw_menu_panel(screen, startup_logic.MAIN_MENU_LAYOUT, False, startup_logic._main_menu_highlight_index)
                startup_logic._draw_menu_panel(screen, startup_logic.SUBMENU_LAYOUT, True, startup_logic._submenu_highlight_index, override_panel_x=int(current_x))
            animation_progress += 1
            if animation_progress > config.MENU_SLIDE_FRAMES:
                log.info("Animation finished. Changing state from '%s' to 'NEW_GAME_SUBMENU'", current_app_state)
                app_state = 'NEW_GAME_SUBMENU'
                startup_logic.reset_highlight_indices()

        # === ZUSTAND: ANIMATING_TO_MAIN ===
        elif app_state == 'ANIMATING_TO_MAIN':
            progress_ratio = min(animation_progress / config.MENU_SLIDE_FRAMES, 1.0)
            panel_width = 300; target_x = config.WIDTH - panel_width - 30; start_x = config.WIDTH
            sub_panel_current_x = target_x + (start_x - target_x) * progress_ratio
            main_panel_current_x = start_x + (target_x - start_x) * progress_ratio
            if hasattr(startup_logic, '_draw_menu_panel') and callable(startup_logic._draw_menu_panel):
                startup_logic._draw_menu_panel(screen, startup_logic.SUBMENU_LAYOUT, True, startup_logic._submenu_highlight_index, override_panel_x=int(sub_panel_current_x))
                startup_logic._draw_menu_panel(screen, startup_logic.MAIN_MENU_LAYOUT, False, startup_logic._main_menu_highlight_index, override_panel_x=int(main_panel_current_x))
            animation_progress += 1
            if animation_progress > config.MENU_SLIDE_FRAMES:
                log.info("Animation finished. Changing state from '%s' to 'MAIN_MENU'", current_app_state)
                app_state = 'MAIN_MENU'
                startup_logic.reset_highlight_indices()

        # === ZUSTAND: ANIMATING_BOARD_SLIDE ===
        elif app_state == 'ANIMATING_BOARD_SLIDE':
            progress_ratio = min(animation_progress / config.BOARD_SLIDE_IN_FRAMES, 1.0)
            start_y = -config.BOARD_HEIGHT; target_y = config.BOARD_OFFSET_Y
            current_y = start_y + (target_y - start_y) * progress_ratio
            board_slide_y_offset = int(current_y)

            original_offset_y = board_display.board_offset_y
            board_display.board_offset_y = board_slide_y_offset
            board_display.draw_board(screen) # Leeres Brett zeichnen
            board_display.board_offset_y = original_offset_y # Wiederherstellen

            if progress_ratio > 0.8: # Koordinaten spät einblenden
                board_display.draw_coordinates(screen, flipped=game_gui_state.get('board_flipped', False))

            animation_progress += 1
            if animation_progress > config.BOARD_SLIDE_IN_FRAMES:
                log.info("Board slide animation finished.")
                log.info("Changing state from '%s' to 'ANIMATING_PIECE_SETUP'", current_app_state)
                app_state = 'ANIMATING_PIECE_SETUP'
                animation_progress = 0
                piece_setup_index = 0
                piece_setup_timer = current_time_ms
                temp_board = chess.Board()
                start_pieces_with_squares = list(temp_board.piece_map().items())
                start_pieces_with_squares.sort(key=lambda item: item[0])
                log.debug("Prepared %d pieces for setup animation.", len(start_pieces_with_squares))
                gs.board.clear_board()

        # === ZUSTAND: ANIMATING_PIECE_SETUP ===
        elif app_state == 'ANIMATING_PIECE_SETUP':
            board_display.draw_board(screen)
            board_display.draw_coordinates(screen, flipped=game_gui_state.get('board_flipped', False))
            board_display.draw_pieces(screen, gs.board) # Zeichnet bisher platzierte

            if piece_setup_index < len(start_pieces_with_squares) and \
               current_time_ms >= piece_setup_timer:
                square, piece = start_pieces_with_squares[piece_setup_index]
                gs.board.set_piece_at(square, piece)
                config.play_sound('PiecePlace')
                piece_setup_index += 1
                piece_setup_timer = current_time_ms + config.PIECE_SETUP_DELAY_MS

            elif piece_setup_index >= len(start_pieces_with_squares):
                log.info("Piece setup animation finished.")
                if _background_music_loaded and config.mixer_initialized:
                    log.debug("Attempting to start background music for new game.")
                    try: pygame.mixer.music.play(-1); log.info("Background music started.")
                    except pygame.error as e: log.error("Error starting background music: %s", e, exc_info=True)

                log.info("Changing state from '%s' to 'GAME'", current_app_state)
                app_state = 'GAME'
                timer_logic.reset_game_timer()
                timer_logic.start_game_timer()
                log.debug("Reset and started game timer.")
                status_display.update_default_status(gs)
                event_handler.reset_selection()

        # === ZUSTAND: GAME ===
        elif app_state == 'GAME':
            status_display.update_default_status(gs)
            # Übergebe game_gui_state an event_handler für Speichern/Laden
            exit_action = event_handler.handle_events(screen, gs, board_display, game_gui_state, events)

            if exit_action: log.debug("Event handler returned action: '%s'", exit_action)
            if exit_action == 'QUIT':
                 log.info("Quit action received from game event handler.")
                 running = False; continue
            elif exit_action == 'TO_MAIN_MENU':
                 log.info("Return to Main Menu action received.")
                 timer_logic.stop_game_timer()
                 if config.mixer_initialized: pygame.mixer.music.stop(); log.debug("Stopped background music.")
                 if ai_thread and ai_thread.is_alive(): log.warning("AI thread still active when returning to menu.")
                 startup_logic.initialize_main_menu()
                 log.info("Changing state from '%s' to 'MAIN_MENU'", current_app_state)
                 app_state = 'MAIN_MENU'
                 if config.ENABLE_TTS: # TTS für Menü wieder aktivieren
                     try:
                         if hasattr(startup_logic, 'MAIN_MENU_LAYOUT') and startup_logic.MAIN_MENU_LAYOUT:
                            first_item_text = startup_logic.MAIN_MENU_LAYOUT[0]["text"]
                            tts_integration.speak_text(f"Hauptmenü. {first_item_text}", interrupt=True)
                         else: tts_integration.speak_text("Hauptmenü", interrupt=True)
                     except (IndexError, KeyError, AttributeError) as e:
                         log.warning("Could not get first menu item text for TTS on return to menu: %s", e)
                         tts_integration.speak_text("Hauptmenü", interrupt=True)
                     except Exception as e: log.error("Error speaking TTS on return to menu: %s", e, exc_info=True)
                 continue # Zustand gewechselt
            elif exit_action == 'NEW_GAME_REQUESTED':
                log.info("New Game requested from in-game menu.")
                if config.mixer_initialized: pygame.mixer.music.stop(); log.debug("Stopped background music.")
                gs.reset_game(); gs.board.clear_board()
                log.debug("GameState reset, board cleared for new game.")
                # Behalte aktuelle AI Einstellung bei Neustart aus dem Spiel
                log.info("Restarting game with current AI settings (Enabled: %s).", config.AI_ENABLED)
                game_gui_state.update({
                    'menu_active': False, 'game_over': False, 'player_turn_finished': False,
                    'ai_thinking': False, 'last_move': None, 'board_flipped': False
                })
                event_handler.reset_selection()
                log.info("Changing state from '%s' to 'ANIMATING_BOARD_SLIDE'", current_app_state)
                app_state = 'ANIMATING_BOARD_SLIDE'
                animation_progress = 0
                board_slide_y_offset = -config.BOARD_HEIGHT
                config.play_sound('BoardSlide')
                continue
            elif exit_action == 'GAME_LOADED': # Spezielles Signal von event_handler nach erfolgreichem Laden
                 log.info("Action 'GAME_LOADED' received. Resetting GUI state.")
                 # Setze GUI-Status basierend auf geladenem Zustand (wurde in load_game gemacht)
                 game_gui_state['game_over'] = gs.is_game_over()
                 game_gui_state['menu_active'] = False
                 game_gui_state['player_turn_finished'] = False
                 game_gui_state['ai_thinking'] = False
                 game_gui_state['last_move'] = gs.board.peek() if gs.board.move_stack else None
                 status_display.update_default_status(gs)
                 event_handler.reset_selection()
                 # Starte Timer nur, wenn Spiel nicht vorbei ist
                 if not game_gui_state['game_over']:
                     timer_logic.start_game_timer()
                     log.debug("Started game timer after load.")
                 else:
                     log.debug("Loaded game is already over. Timer remains stopped.")

            elif exit_action == 'UNDO_PERFORMED' or exit_action == 'REDO_PERFORMED':
                log.info("Action performed: %s", exit_action)
                status_display.update_default_status(gs)
                # Timer wird gestoppt bei Undo, muss ggf. wieder gestartet werden
                if not game_gui_state['game_over'] and not game_gui_state['menu_active']:
                    if exit_action == 'REDO_PERFORMED':
                         timer_logic.start_game_timer() # Timer nach Redo wieder starten
                    else: # Nach Undo bleibt der Timer gestoppt
                         timer_logic.stop_game_timer()
                event_handler.reset_selection() # Auswahl aufheben nach Undo/Redo


            # Spiel-Logik (nur wenn Menü nicht aktiv und keine Animation läuft)
            is_animating_move = animations.is_animating()
            if not game_gui_state['menu_active'] and not is_animating_move:
                # Spielende prüfen
                if not game_gui_state['game_over'] and gs.is_game_over():
                    game_gui_state['game_over'] = True
                    timer_logic.stop_game_timer()
                    if config.mixer_initialized: pygame.mixer.music.stop(); log.debug("Stopped background music.")
                    game_over_text = chess_utils.get_game_over_text(gs.board)
                    log.info("Game over detected: %s", game_over_text)
                    config.play_sound('game_over')
                    status_display.update_default_status(gs)

                # KI-Zug Logik
                is_ai_turn = config.AI_ENABLED and gs.board.turn == config.AI_PLAYER
                player_just_finished = game_gui_state.get('player_turn_finished', False)

                # Starte KI
                if is_ai_turn and player_just_finished and not game_gui_state['game_over'] and not game_gui_state['ai_thinking']:
                    game_gui_state['player_turn_finished'] = False # Flag zurücksetzen
                    log.debug("Conditions met to start AI move calculation.")
                    game_gui_state['ai_thinking'] = True
                    valid_moves = gs.get_valid_moves()
                    if valid_moves:
                        log.info("AI turn: Starting thinking process...")
                        status_display.display_message("KI denkt...", 'info')
                        # Übergebe eine Kopie von gs an den Thread
                        gs_copy_for_ai = gs.copy()
                        ai_thread = threading.Thread(target=ai_opponent.find_best_move, args=(gs_copy_for_ai, valid_moves, ai_move_queue), daemon=True, name="AI_Thread")
                        ai_thread.start()
                        log.debug("AI thread '%s' started with a copy of GameState.", ai_thread.name)
                    else:
                        log.warning("AI is turn, but no valid moves available. Game should be over?")
                        game_gui_state['ai_thinking'] = False
                        status_display.update_default_status(gs)

                # Verarbeite Ergebnis des KI-Threads
                if game_gui_state['ai_thinking']:
                    try:
                        if ai_thread and not ai_thread.is_alive() and ai_move_queue.empty():
                            log.warning("AI thread finished, but move queue is empty.")
                            game_gui_state['ai_thinking'] = False
                            status_display.update_default_status(gs)

                        ai_move = ai_move_queue.get_nowait()
                        log.info("AI finished. Received move: %s", ai_move.uci() if ai_move else 'None')

                        if ai_move:
                            # Wichtig: Prüfe Legalität im *aktuellen* GameState (gs), nicht in der Kopie!
                            current_valid_moves = gs.get_valid_moves()
                            if ai_move in current_valid_moves:
                                log.info("Executing AI move: %s", ai_move.uci())
                                # _execute_move modifiziert den Haupt-GameState (gs)
                                event_handler._execute_move(gs, game_gui_state, ai_move)
                            else:
                                log.error("AI returned move %s which is currently NOT legal in main GameState!", ai_move.uci())
                                status_display.display_message("KI Fehler (illegaler Zug)", 'error')
                                if current_valid_moves:
                                    fallback_move = current_valid_moves[0]
                                    log.warning("Executing first available legal move %s as fallback.", fallback_move.uci())
                                    event_handler._execute_move(gs, game_gui_state, fallback_move)
                                else: log.error("AI returned illegal move and no other valid moves exist!")
                        else: # ai_move is None
                            log.warning("AI returned None. Assuming no move possible/intended.")
                            status_display.update_default_status(gs)
                            if not game_gui_state['game_over'] and gs.is_game_over():
                                game_gui_state['game_over'] = True; timer_logic.stop_game_timer()
                                if config.mixer_initialized: pygame.mixer.music.stop()
                                config.play_sound('game_over')
                                log.info("Game over detected after AI returned None.")

                        game_gui_state['ai_thinking'] = False
                        log.debug("AI thinking finished.")

                    except queue.Empty: pass # KI rechnet noch
                    except Exception as e:
                        log.error("Exception while processing AI move queue: %s", e, exc_info=True)
                        status_display.display_message(f"KI Fehler: {e}", 'error')
                        game_gui_state['ai_thinking'] = False


            # --- Zeichnen im Spielzustand ---
            if is_animating_move:
                animations.update_animation(screen, gs, board_display)
            else:
                chess_gui.draw_game_state(
                    screen, gs, board_display,
                    selected_square_index=event_handler.get_selected_square(),
                    source_square_index=event_handler.get_source_square(),
                    last_move=game_gui_state.get('last_move'),
                    board_flipped=game_gui_state.get('board_flipped', False)
                )

            timer_logic.draw_game_timer(screen)
            status_display.draw_status_display(screen)

            if game_gui_state['menu_active']:
                current_highlight = menu_logic.get_highlighted_index()
                menu_logic.draw_menu(screen, current_highlight)
            elif game_gui_state['game_over']: # Zeichne Spielende-Text nur wenn kein Menü aktiv ist
                 game_over_text = chess_utils.get_game_over_text(gs.board)
                 if game_over_text:
                     chess_gui.draw_game_over_text(screen, game_over_text)


        # --- Allgemeines Update & Framerate ---
        pygame.display.flip() # Zeigt den neu gezeichneten Frame an
        clock.tick(config.TARGET_FPS) # Wartet, um FPS zu begrenzen

    # --- Aufräumen vor dem Beenden ---
    log.info("Main loop exited. Initiating shutdown sequence...")
    if config.mixer_initialized:
        pygame.mixer.music.stop()
        log.info("Stopped background music.")
        pygame.mixer.quit()
        log.info("Quit Pygame Mixer.")

    if ai_thread and ai_thread.is_alive():
         log.warning("AI thread is still alive during final shutdown, but set as daemon.")

    pygame.quit()
    log.info("Pygame quit successfully.")
    log.info(f"<--- ==================== Beende Hauptmodul '{__name__}' ==================== --->")
    sys.exit()

# --- Startpunkt des Programms ---
if __name__ == "__main__":
    # log.debug("Default save filename from file_io: %s", file_io.DEFAULT_SAVE_FILENAME) # file_io nicht mehr direkt importieren
    main()

