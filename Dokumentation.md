# PyChess Projektübersicht
## 1. Einleitung
PyChess ist eine anspruchsvolle Schachapplikation, entwickelt in Python unter Verwendung der vielseitigen Pygame-Bibliothek. Es zeichnet sich durch eine intuitive grafische Benutzeroberfläche (GUI), einen optionalen, intelligenten KI-Gegner, die Funktionalität zum Speichern und Laden von Partien sowie eine integrierte Text-to-Speech (TTS)-Unterstützung aus, welche die Barrierefreiheit signifikant erhöht.

Diese Dokumentation dient als umfassender Leitfaden zur Projektarchitektur, den einzelnen Modulen und deren synergetischem Zusammenwirken.

## 2. Architektur des Projekts
Das Projekt ist konsequent modular strukturiert, um eine klare Code-Organisation, exzellente Lesbarkeit und effiziente Wartbarkeit zu gewährleisten. Es gliedert sich in Hauptmodule, ein spezialisiertes GUI-Paket sowie Verzeichnisse für externe Ressourcen.

PyChess/
├── assets/                     # Zentrales Verzeichnis für externe Ressourcen
│   ├── images/                 # Grafiken für Schachfiguren (.png, .svg)
│   ├── sounds/                 # Akustische Effekte (.wav, .ogg, .mp3)
│   ├── fonts/                  # Schriftartdateien (optional, .ttf, .otf)
│   └── books/                  # Eröffnungsbibliotheken (z.B. human.bin im Polyglot-Format)
│   └── syzygy/                 # Syzygy Endspieldatenbanken (optional)
├── gui/                        # Paket für sämtliche GUI-bezogenen Module
│   ├── __init__.py             # Initialisiert das Paket und konfiguriert den Paket-Logger
│   ├── board_display.py        # Klasse BoardDisplay: Darstellung von Brett, Feldern, Koordinaten, Hervorhebungen
│   ├── chess_gui.py            # Koordiniert die grafische Darstellung im Spielzustand (Brett, Figuren, HUD)
│   ├── fullscreen_logic.py     # Logik für die Umschaltung in den Vollbildmodus (F11)
│   ├── menu_logic.py           # Logik und Darstellung des In-Game-Pausenmenüs
│   ├── navigation_logic.py     # Schnittstelle für Undo/Redo-Funktionen
│   ├── save_load_logic.py      # Schnittstelle für Speicher- und Ladeaktionen aus der GUI
│   ├── startup_logic.py        # Logik und Darstellung des Hauptmenüs sowie des Spielstart-Untermenüs
│   ├── status_display.py       # Anzeige von Statusinformationen (Zugrecht, Fehler etc.)
│   ├── timer_logic.py          # Implementierung und Anzeige der Spielzeituhr
│   └── tts_integration.py      # Formatiert Spielinformationen für TTS und steuert tts_utils
├── logs/                       # Verzeichnis für Log-Dateien (automatisch erstellt durch logger.py)
├── saves/                      # Verzeichnis für gespeicherte Spielstände (automatisch erstellt)
├── __init__.py                 # Definiert PyChess als Paket (importiert gui)
├── ai_opponent.py            # Implementierung der KI (Minimax, Eröffnungsbuch, Syzygy)
├── animations.py             # Klasse Animation: Visuelle Animation von Schachzügen
├── chess_utils.py            # Schachspezifische Hilfsfunktionen (Notation, Bewertung etc.)
├── config.py                 # Zentrale Konfiguration (Konstanten, Pfade, Farben, Fonts, Ressourcen-Management)
├── event_handler.py          # Verarbeitung von Benutzereingaben im Spielzustand
├── file_io.py                # Physisches Speichern/Laden von Spieldateien (JSON, Tkinter-Dialoge)
├── game_state.py             # Klasse GameState: Kernlogik, Brettzustand, Zughistorie
├── logger.py                 # Konfiguration des Logging-Systems (python-json-logger)
├── main.py                     # Haupteinstiegspunkt, Hauptschleife, Zustandsautomaten-Logik
├── requirements.txt            # Auflistung der externen Python-Abhängigkeiten
├── Tolk.py                     # Python-Wrapper für die Tolk DLL (Screenreader-Anbindung)
└── tts_utils.py                # Kernfunktionen für die TTS-Ausgabe (Initialisierung, Sprachausgabe via Tolk)

## 3. Detaillierte Beschreibung der Kernkomponenten
### 3.1. Hauptmodule
main.py:

Verantwortlichkeit: Orchestrierung der gesamten Applikation.
Details: Übernimmt die Initialisierung von Pygame und dessen Subsystemen (Font, Mixer). Ruft config.load_images() und config.load_sounds() zur Ressourcenladung auf. Erstellt Instanzen von GameState und BoardDisplay. Implementiert die zentrale Programmschleife, welche die verschiedenen Anwendungszustände (app_state) steuert:
MAIN_MENU: Präsentation des Hauptmenüs (mittels startup_logic.py).
NEW_GAME_SUBMENU: Anzeige des Untermenüs zur Spielkonfiguration.
ANIMATING_TO_SUB/ANIMATING_TO_MAIN: Visuelle Übergänge zwischen Menüebenen.
ANIMATING_BOARD_SLIDE: Animation für das dynamische Einblenden des Schachbretts.
ANIMATING_PIECE_SETUP: Animation für das initiale Aufstellen der Figuren.
GAME: Der eigentliche Spielzustand, in dem event_handler.py und chess_gui.py die Regie führen.
Verarbeitet globale Ereignisse wie QUIT und VIDEORESIZE. Initiiert und verwaltet den KI-Thread (ai_opponent.py). Koordiniert Zustandswechsel basierend auf Benutzerinteraktionen oder Spielereignissen.
config.py:

Verantwortlichkeit: Zentralisierte Verwaltung aller Konfigurationseinstellungen und Ressourcen.
Details: Definiert Konstanten (Fenster- und Brettdimensionen, Farbpaletten, Schriftgrößen, Dateipfade, KI-Parameter, Animationsgeschwindigkeiten). Initialisiert Pygame-Schriftarten. Beinhaltet die Funktionen load_images() und load_sounds(), welche die entsprechenden Mediendateien aus den assets-Unterverzeichnissen laden und in Dictionaries (IMAGES, SOUNDS) für den schnellen Zugriff bereitstellen. Stellt play_sound() als Hilfsfunktion zur Verfügung und definiert PIECE_VALUES für die Bewertungsfunktion der KI.
game_state.py (GameState Klasse):

Verantwortlichkeit: Kapselung und Management des logischen Kernzustands der Schachpartie.
Details: Basiert intern auf einem chess.Board-Objekt der python-chess Bibliothek. Die Methode make_move() führt einen Zug aus, validiert diesen implizit durch board.push(), aktualisiert die Listen der geschlagenen Figuren (captured_by_white/captured_by_black) und invalidiert den redo_stack. undo_move() revidiert einen Zug, stellt gegebenenfalls eine geschlagene Figur wieder her und fügt den rückgängig gemachten Zug zum redo_stack hinzu. redo_move() führt einen Zug aus dem redo_stack erneut aus. Bietet diverse Methoden zur Abfrage des Spielzustands (is_game_over, get_valid_moves, get_fen, etc.).
event_handler.py:

Verantwortlichkeit: Verarbeitung von Maus- und Tastatureingaben im GAME-Zustand.
Details: Differenziert zwischen Interaktionen im Spielgeschehen und im aktiven In-Game-Menü. Verwaltet den Cursor (selected_square_index) und die selektierte Figur (source_square_selected). Bei Brettinteraktionen (Klick/Enter/Leertaste) wird geprüft, ob eine Figur aufgenommen, abgesetzt oder gezogen werden soll. try_create_move() validiert den potenziellen Zug. Bei einem gültigen Zug wird _execute_move() aufgerufen, was wiederum GameState.make_move(), animations.start_move_animation(), play_move_sounds() und tts_integration.speak_move_after() anstößt. Handhabt Tastenkürzel wie Z/Y (Undo/Redo via navigation_logic), ESC (Menü via menu_logic), Strg+S/L (Speichern/Laden via save_load_logic), F11 (Vollbild via fullscreen_logic) sowie diverse TTS/Sound-Umschaltungen.
ai_opponent.py:

Verantwortlichkeit: Berechnung des optimalen Zugs für den computergesteuerten Gegner.
Details: Die zentrale Funktion find_best_move() wird von main.py in einem separaten Thread ausgeführt. Sie konsultiert zunächst ein Eröffnungsbuch (config.POLYGLOT_BOOK_PATH via chess.polyglot). Anschließend werden optional Syzygy-Endspieldatenbanken (config.SYZYGY_PATH via chess.syzygy) geprüft, falls konfiguriert und die Figurenanzahl dies zulässt. Findet sich hier kein Zug, initiiert die Funktion die Minimax-Suche (find_best_move_minimax) mit Alpha-Beta-Pruning bis zur in config.AI_DEPTH definierten Tiefe. Diese Suche operiert auf einer Kopie des GameState, um Seiteneffekte auf den Hauptspielzustand zu vermeiden. Die Stellungsbewertung erfolgt durch evaluate_board(), welche Material (score_material) und Spielende-Szenarien berücksichtigt. Der ermittelte Zug wird mittels einer queue.Queue an den Hauptthread übermittelt.
file_io.py & gui/save_load_logic.py:

Verantwortlichkeit: Persistenz von Spielständen.
Details: file_io.py verwendet json.dump() zur Serialisierung des GameState-Objekts und relevanter Metadaten sowie json.load() zur Deserialisierung. Es greift auf tkinter.filedialog (asksaveasfilename, askopenfilename) zurück, um systemnative Datei-Dialoge anzuzeigen. gui/save_load_logic.py dient als Schnittstelle, die von event_handler.py oder menu_logic.py genutzt wird und die Operationen an file_io.py delegiert. Beim Laden einer Partie aktualisiert save_load_logic.load_game() die Attribute des aktuellen GameState-Objekts mit den geladenen Daten.
tts_utils.py & Tolk.py:

Verantwortlichkeit: Bereitstellung der Text-to-Speech-Funktionalität.
Details: Tolk.py fungiert als ctypes-Wrapper, der die Funktionen der Tolk.dll (externe Abhängigkeit, muss bereitgestellt werden) für Python verfügbar macht. tts_utils.py initialisiert die Tolk-Schnittstelle (_initialize_tolk), exponiert die speak()-Funktion (welche intern Tolk.speak() aufruft) und gewährleistet ein ordnungsgemäßes Herunterfahren (_shutdown_tolk via atexit). Es implementiert zudem eine Interrupt-Logik (_stop_speaking via Tolk.silence()) inklusive Debouncing.
logger.py:

Verantwortlichkeit: Zentralisierte Konfiguration des Logging-Mechanismus.
Details: Die Funktion setup_logger() erstellt und konfiguriert einen Logger mit einem JsonFormatter. Dieser kann so eingestellt werden, dass er Ausgaben in eine Datei (logs/PyChess.txt) und/oder die Konsole schreibt. Die meisten anderen Module importieren diese Funktion und instanziieren ihren eigenen Logger unter Verwendung ihres Modulnamens (__name__).
animations.py:

Verantwortlichkeit: Visuelle Repräsentation von Figurenbewegungen.
Details: Die Animation-Klasse speichert Start- und Zielfeld sowie die bewegte Figur und berechnet die Bewegung pro Frame. start_move_animation() erzeugt eine Instanz dieser Klasse. update_animation() wird in der Hauptschleife aufgerufen, zeichnet das Brett ohne die animierte Figur auf ihrem Ursprungsfeld, stellt die Figur an ihrer interpolierten Position dar und aktualisiert den Animationsfortschritt. is_animating() prüft den Status der Animation.
chess_utils.py:

Verantwortlichkeit: Sammlung schachspezifischer Hilfsroutinen.
Details: Stellt Funktionen bereit wie get_move_notation() (konvertiert chess.Move in SAN), get_game_over_text() (ermittelt Text für Matt, Patt etc.), is_capture(), is_check(), get_piece_value(), square_to_algebraic(), algebraic_to_square(), get_square_color(), get_piece_color_char(), get_piece_symbol_upper(). Diese Funktionen kapseln Logik der python-chess-Bibliothek oder greifen auf Definitionen in config.py zu.
### 3.2. GUI-Paket (gui/)
__init__.py: Gewährleistet, dass gui als Paket behandelt wird und kann Submodule importieren oder paketweites Logging einrichten.
board_display.py (BoardDisplay Klasse): Zeichnet das statische Schachbrett (Felder, Farben), die Koordinaten (draw_coordinates) und stellt Methoden zur dynamischen Hervorhebung einzelner Felder (highlight_square), des letzten Zugs (highlight_last_move), legaler Züge (highlight_legal_moves) und des im Schach stehenden Königs (highlight_check) bereit. Übernimmt auch das Zeichnen der Figuren (draw_pieces), wobei optional ein Feld von der Darstellung ausgenommen werden kann (relevant während Animationen).
chess_gui.py: Ruft im GAME-Zustand die Methoden von BoardDisplay in der korrekten Sequenz auf, um Brett, Figuren und Hervorhebungen darzustellen. Zeichnet zusätzlich die geschlagenen Figuren an den Bretträndern (draw_captured_pieces) und den Text bei Spielende (draw_game_over_text).
startup_logic.py: Ist zuständig für die Darstellung und Interaktion im MAIN_MENU und NEW_GAME_SUBMENU. Zeichnet die Menü-Paneele inklusive Titel und Schaltflächen. Handhabt Maus- und Tastaturnavigation innerhalb dieser Menüs. Startet und aktualisiert zudem das im Hintergrund des Hauptmenüs ablaufende, zufällige KI-gegen-KI-Spiel.
menu_logic.py: Analog zu startup_logic, jedoch für das In-Game-Pausenmenü (ausgelöst durch ESC). Zeichnet das Menü und verarbeitet Eingaben zur Auswahl von Aktionen wie "Fortsetzen", "Speichern", "Laden", "Hauptmenü" oder "Beenden".
status_display.py: Verwaltet eine Textzeile am oberen Bildschirmrand. Zeigt standardmäßig das Zugrecht oder das Spielergebnis an. Kann temporäre Nachrichten (letzter Zug, Fehler, Informationen) mit optionaler Anzeigedauer einblenden (display_message).
timer_logic.py: Implementiert einen einfachen, vorwärtszählenden Spieltimer. Bietet Funktionen zum Starten, Stoppen und Zurücksetzen. draw_game_timer() visualisiert die formatierte Zeit.
fullscreen_logic.py: Beinhaltet die Funktion toggle_fullscreen(), welche zwischen Fenster- und Vollbildmodus wechselt, indem pygame.display.set_mode() mit den entsprechenden Flags aufgerufen wird. Merkt sich die ursprüngliche Fenstergröße für die Rückkehr zum Fenstermodus.
navigation_logic.py: Stellt einfache Wrapper-Funktionen undo_move() und redo_move() zur Verfügung, die die korrespondierenden Methoden des GameState-Objekts aufrufen. Wird von event_handler.py verwendet.
tts_integration.py: Dient als Brücke zwischen der Spiellogik/-GUI und tts_utils. Formatiert Zuginformationen (format_move_for_speech_post_move), Figurenauswahlen (speak_selection) und andere Statusmeldungen in natürlich klingende deutsche Sätze und ruft anschließend tts_utils.speak() zur Ausgabe auf.
## 4. Externe Abhängigkeiten
pygame (Version >= 2.0.0 empfohlen): Essentiell für Grafikdarstellung, Soundausgabe, Ereignisbehandlung und Fensterverwaltung.
python-chess (Version >= 1.0): Unverzichtbar für die gesamte Schachlogik, Brettmanipulationen und -analysen.
python-json-logger: Ermöglicht strukturiertes Logging im JSON-Format.
tkinter: Bestandteil der Python-Standardbibliothek; wird für die Anzeige nativer Dateidialoge benötigt.
(Optional) Tolk.dll: Für die TTS-Funktionalität unter Windows in Verbindung mit Screenreadern (muss extern bezogen und im Projektverzeichnis platziert werden).
## 5. Detaillierter Funktionsablauf
Initialisierung (main.py):
Pygame, dessen Mixer und Font-Subsysteme werden initialisiert.
Das Logging-System wird konfiguriert.
Ressourcen (Bilder, Sounds) werden über config.py geladen.
Instanzen von GameState und BoardDisplay werden erzeugt.
startup_logic.initialize_main_menu() wird aufgerufen.
Der initiale Zustand ist MAIN_MENU. Eine TTS-Willkommensnachricht wird ausgegeben.
Hauptmenü-Phase (main.py -> startup_logic.py):
startup_logic.run_main_menu_frame() zeichnet das Menü und das im Hintergrund laufende Spiel.
Benutzereingaben (Mausklicks, Tastatur) werden verarbeitet.
Auswahl "Neues Spiel" führt zum Zustand ANIMATING_TO_SUB.
Auswahl "Laden" ruft save_load_logic.load_game() auf. Bei Erfolg Übergang zum Zustand GAME.
Auswahl "Beenden" setzt running = False.
Spielstart-Phase (main.py -> startup_logic.py -> animations.py):
Nach Auswahl von "Lokales Spiel" oder "Gegen KI" im Untermenü:
GameState wird zurückgesetzt (gs.reset_game()).
Gegebenenfalls wird die KI konfiguriert (config.AI_ENABLED, config.AI_PLAYER).
Zustandswechsel zu ANIMATING_BOARD_SLIDE.
Das leere Schachbrett wird animiert eingeblendet.
Zustandswechsel zu ANIMATING_PIECE_SETUP.
Die Figuren werden sequenziell und mit Soundeffekten auf dem Brett platziert.
Nach Abschluss erfolgt der Übergang zum Zustand GAME; der Timer und die Hintergrundmusik starten.
Spiel-Phase (main.py -> event_handler.py, chess_gui.py, ai_opponent.py etc.):
Die Hauptschleife prüft auf neue Ereignisse.
event_handler.handle_events() verarbeitet die Eingaben:
Maus/Tastatur (Brett): Selektiert Felder (selected_square_index), nimmt Figuren auf (source_square_selected), versucht Züge zu erstellen (try_create_move). Bei einem gültigen Zug -> _execute_move().
_execute_move(): Ruft gs.make_move() auf, startet die Zuganimation (animations.start_move_animation), spielt Sounds ab (play_move_sounds), gibt eine TTS-Meldung aus (tts_integration.speak_move_after), aktualisiert Statusanzeigen/Timer und setzt player_turn_finished = True.
Tastenkürzel: Lösen Aktionen wie Undo/Redo, Speichern/Laden, Menüaufruf, Umschalten von Optionen etc. aus.
KI-Logik: Wenn player_turn_finished und die KI am Zug ist:
ai_opponent.find_best_move() wird in einem neuen Thread gestartet.
Die Hauptschleife überwacht die ai_move_queue.
Sobald ein Zug verfügbar ist, wird _execute_move() für den KI-Zug aufgerufen.
Grafische Darstellung:
Falls animations.is_animating(): animations.update_animation() zeichnet das Brett und die animierte Figur.
Andernfalls: chess_gui.draw_game_state() zeichnet den statischen Spielzustand (Brett, Figuren, Hervorhebungen).
timer_logic.draw_game_timer() und status_display.draw_status_display() werden aufgerufen.
Bei aktivem Menü (menu_active): menu_logic.draw_menu() wird aufgerufen.
Bei Spielende (game_over): chess_gui.draw_game_over_text() wird aufgerufen.
Spielende-Prüfung: gs.is_game_over() wird evaluiert; bei Bedarf wird das game_over-Flag gesetzt und Timer/Musik gestoppt.
Beendigung: Wenn running = False gesetzt wird (durch ein QUIT-Ereignis oder eine Menüauswahl), wird die Hauptschleife verlassen, und Mixer sowie Pygame werden ordnungsgemäß heruntergefahren.
## 6. Erweiterte Schlüsselfunktionalitäten
Grafik & Darstellung: Detaillierte Brett- und Figurenanzeige (board_display), flüssige Animationen (animations), intuitive Menüführung (startup_logic, menu_logic), informatives HUD (timer_logic, status_display).
Schachlogik: Umfassende Nutzung von python-chess für Zuglegalität, Erkennung von Spielende-Bedingungen, FEN/SAN-Konvertierung, sowie Unterstützung für Eröffnungsbücher und Endspieldatenbanken (game_state, chess_utils, ai_opponent).
Benutzerinteraktion: Durchdachte Maus- und Tastatursteuerung inklusive Cursor-Navigation, Aufnahme/Absetzen von Figuren und hilfreichen Shortcuts (event_handler).
Künstliche Intelligenz: Implementierung einer Minimax-Suche mit Alpha-Beta-Pruning, Materialbewertung, optionaler Nutzung von Eröffnungsbüchern und Endspieldatenbanken, sowie Threading zur Vermeidung von GUI-Blockaden (ai_opponent).
Persistenz: Zuverlässiges Speichern und Laden des gesamten GameState mittels JSON-Serialisierung, ergänzt durch benutzerfreundliche Dateidialoge über tkinter (file_io, save_load_logic).
Partieverlauf: Undo/Redo-Funktionalität mit korrekter Verwaltung des redo_stack und der geschlagenen Figuren (game_state, navigation_logic).
Akustisches & Visuelles Feedback: Aussagekräftige visuelle Hervorhebungen, passende Soundeffekte für diverse Spielaktionen (config, event_handler), sowie klare Statusmeldungen (status_display).
Barrierefreiheit: Umfassende TTS-Ausgabe für alle relevanten Spielaktionen und Zustandsänderungen durch eine nahtlose Tolk-Integration (tts_utils, Tolk, tts_integration).
Konfiguration & Modularität: Eine zentrale config.py für alle Einstellungen, strikte Trennung der Verantwortlichkeiten in einzelne Module und ein dediziertes GUI-Paket fördern Übersichtlichkeit und Wartbarkeit.
Logging: Detaillierte Protokollierung aller wichtigen Vorgänge und potenzieller Fehler in eine Log-Datei zur einfacheren Fehlersuche und Nachvollziehbarkeit (logger).
## 7. Setup und Inbetriebnahme
Python-Installation: Stellen Sie sicher, dass eine kompatible Python-Version (z.B. 3.8 oder neuer) auf Ihrem System installiert ist.
Installation der Abhängigkeiten: Navigieren Sie im Terminal zum Wurzelverzeichnis des PyChess-Projekts und führen Sie den Befehl pip install -r requirements.txt aus.
(Optional) Tolk-Einrichtung: Laden Sie die Tolk-Bibliothek herunter. Platzieren Sie die Tolk.dll-Datei direkt im PyChess-Hauptverzeichnis (oder passen Sie den Pfad bei Bedarf in der config.py-Datei an).
Spielstart: Starten Sie die Anwendung aus dem PyChess-Verzeichnis mit dem Befehl: python main.py.
## 8. Schlussbetrachtung
PyChess repräsentiert eine robuste und durchdachte Implementierung eines Schachspiels mittels Pygame. Die klare Abgrenzung von Spiellogik, grafischer Benutzeroberfläche und Konfigurationsmanagement, in Verbindung mit der Nutzung leistungsfähiger externer Bibliotheken wie python-chess, ermöglicht eine funktionsreiche und flexible Anwendung. Ein besonderer Fokus lag auf der Bereitstellung eines ansprechenden Benutzererlebnisses durch visuelle Animationen, akustische Rückmeldungen und umfassende Text-to-Speech-Unterstützung, was die Zugänglichkeit und den Spielspaß gleichermaßen erhöht.