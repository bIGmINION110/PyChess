# PyChess (Projekt Dokumentation)

## 1. Einführung

PyChess ist ein Schachspiel, das mit Python und der Pygame-Bibliothek entwickelt wurde. Es bietet eine grafische Benutzeroberfläche (GUI), eine optionale Künstliche Intelligenz (KI) als Gegner, die Möglichkeit zum Speichern und Laden von Spielständen sowie Text-to-Speech (TTS)-Unterstützung zur Verbesserung der Barrierefreiheit.

Diese Dokumentation bietet eine detaillierte Beschreibung der Projektstruktur, der einzelnen Komponenten und ihrer Interaktionen.

## 2. Projektstruktur

Das Projekt ist modular aufgebaut, um Code-Organisation, Lesbarkeit und Wartbarkeit zu fördern. Es besteht aus Hauptmodulen, einem GUI-Paket und Verzeichnissen für externe Ressourcen.

PyChess/├── assets/                     # Verzeichnis für externe Ressourcen│   ├── images/                 # Figurenbilder (.png, .svg)│   ├── sounds/                 # Soundeffekte (.wav, .ogg, .mp3)│   ├── fonts/                  # Schriftartdateien (optional, .ttf, .otf)│   └── books/                  # Eröffnungsbücher (z.B. human.bin im Polyglot-Format)│   └── syzygy/                 # Syzygy Endspieldatenbanken (optional)├── gui/                        # Paket für alle GUI-bezogenen Module│   ├── init.py             # Initialisiert das Paket, konfiguriert den Paket-Logger│   ├── board_display.py        # Klasse BoardDisplay: Zeichnet Brett, Felder, Koordinaten, Highlights│   ├── chess_gui.py            # Koordiniert das Zeichnen im Spielzustand (Brett, Figuren, HUD)│   ├── fullscreen_logic.py     # Logik für Vollbildumschaltung (F11)│   ├── menu_logic.py           # Logik und Darstellung des In-Game-Pausemenüs│   ├── navigation_logic.py     # Schnittstelle für Undo/Redo-Aktionen│   ├── save_load_logic.py      # Schnittstelle für Speichern/Laden-Aktionen aus der GUI│   ├── startup_logic.py        # Logik und Darstellung des Hauptmenüs und des Spielstart-Untermenüs│   ├── status_display.py       # Anzeige von Statusmeldungen (wer am Zug, Fehler etc.)│   ├── timer_logic.py          # Implementierung und Anzeige des Spieltimers│   └── tts_integration.py      # Formatiert Spielinformationen für TTS und ruft tts_utils auf├── logs/                       # Verzeichnis für Log-Dateien (wird von logger.py erstellt)├── saves/                      # Verzeichnis für Speicherstände (wird von config.py/file_io.py erstellt)├── init.py                 # Macht PyChess zu einem Paket (importiert gui)├── ai_opponent.py            # Implementiert die KI-Logik (Minimax, Buch, Syzygy)├── animations.py             # Klasse Animation: Visuelle Animation von Zügen├── chess_utils.py            # Schachspezifische Hilfsfunktionen (Notation, Bewertung etc.)├── config.py                 # Zentrale Konfiguration (Konstanten, Pfade, Farben, Fonts, Ressourcenladen)├── event_handler.py          # Verarbeitet Benutzereingaben im Spielzustand├── file_io.py                # Verantwortlich für das physische Speichern/Laden (Pickle, Tkinter-Dialoge)├── game_state.py             # Klasse GameState: Kernlogik, Brettzustand, Zughistorie├── logger.py                 # Konfiguriert das Logging-System (python-json-logger)├── main.py                     # Haupteinstiegspunkt, Hauptschleife, Zustandsmaschine├── requirements.txt            # Liste der externen Python-Abhängigkeiten├── Tolk.py                     # Python-Wrapper für die Tolk DLL (Screenreader-Anbindung)└── tts_utils.py                # Kernfunktionen für TTS-Ausgabe (Initialisierung, Sprachausgabe über Tolk)
## 3. Kernkomponenten und ihre Funktion (Detailliert)

### 3.1. Hauptmodule

* **`main.py`**:
    * **Aufgabe:** Orchestrierung der gesamten Anwendung.
    * **Details:** Initialisiert Pygame und seine Module (Font, Mixer). Ruft `config.load_images()` und `config.load_sounds()` auf. Erstellt Instanzen von `GameState` und `BoardDisplay`. Startet die Hauptschleife, die durch verschiedene Anwendungszustände (`app_state`) navigiert:
        * `MAIN_MENU`: Zeigt das Hauptmenü an (über `startup_logic.py`).
        * `NEW_GAME_SUBMENU`: Zeigt das Untermenü zur Spielauswahl an.
        * `ANIMATING_TO_SUB`/`ANIMATING_TO_MAIN`: Übergangsanimationen zwischen Menüs.
        * `ANIMATING_BOARD_SLIDE`: Animation für das Einfliegen des Bretts.
        * `ANIMATING_PIECE_SETUP`: Animation für das Aufstellen der Figuren.
        * `GAME`: Der eigentliche Spielzustand, in dem `event_handler.py` und `chess_gui.py` aktiv sind.
    * Verarbeitet globale Events wie `QUIT` und `VIDEORESIZE`. Startet und verwaltet den KI-Thread (`ai_opponent.py`). Koordiniert den Wechsel zwischen Zuständen basierend auf Benutzeraktionen oder Spielereignissen.

* **`config.py`**:
    * **Aufgabe:** Zentraler Speicherort für alle Konfigurationseinstellungen und Ressourcenverwaltung.
    * **Details:** Definiert Konstanten (Fenster-/Brettmaße, Farben, Schriftgrößen, Pfade, KI-Parameter, Animationsgeschwindigkeiten). Initialisiert Pygame-Fonts. Enthält Funktionen `load_images()` und `load_sounds()`, die die entsprechenden Dateien aus den `assets`-Unterordnern laden und in Dictionaries (`IMAGES`, `SOUNDS`) speichern. Definiert `play_sound()` als Hilfsfunktion. Enthält auch die `PIECE_VALUES` für die KI-Bewertung.

* **`game_state.py` (`GameState` Klasse)**:
    * **Aufgabe:** Verwaltung des logischen Kernzustands des Spiels.
    * **Details:** Nutzt intern ein `chess.Board`-Objekt. Die Methode `make_move()` führt einen Zug aus (validiert ihn implizit durch `board.push()`), aktualisiert die Liste der geschlagenen Figuren (`captured_by_white`/`captured_by_black`) und löscht den `redo_stack`. `undo_move()` macht einen Zug rückgängig, stellt ggf. eine geschlagene Figur aus der Capture-Liste wieder her und fügt den rückgängig gemachten Zug zum `redo_stack` hinzu. `redo_move()` führt einen Zug vom `redo_stack` wieder aus. Bietet Methoden zur Zustandsprüfung (`is_game_over`, `get_valid_moves`, `get_fen`, etc.).

* **`event_handler.py`**:
    * **Aufgabe:** Verarbeitung von Maus- und Tastatureingaben im `GAME`-Zustand.
    * **Details:** Unterscheidet zwischen Klicks/Tastatureingaben im Spiel und im aktiven In-Game-Menü. Verwaltet den Cursor (`selected_square_index`) und die aufgenommene Figur (`source_square_selected`). Bei Brettinteraktion (Klick/Enter/Leertaste): Prüft, ob eine Figur aufgenommen/abgesetzt/bewegt werden soll. Ruft `try_create_move()` zur Validierung auf. Wenn ein gültiger Zug erkannt wird, ruft es `_execute_move()` auf, welches `GameState.make_move()`, `animations.start_move_animation()`, `play_move_sounds()` und `tts_integration.speak_move_after()` auslöst. Handhabt Tastenkürzel wie Z/Y (Undo/Redo via `navigation_logic`), ESC (Menü via `menu_logic`), Strg+S/L (Speichern/Laden via `save_load_logic`), F11 (Vollbild via `fullscreen_logic`), und diverse TTS/Sound-Toggles.

* **`ai_opponent.py`**:
    * **Aufgabe:** Berechnung des nächsten Zugs für den Computergegner.
    * **Details:** Die Hauptfunktion `find_best_move()` wird von `main.py` in einem separaten Thread gestartet. Sie prüft zuerst, ob ein Zug aus dem Eröffnungsbuch (`config.POLYGLOT_BOOK_PATH`) verfügbar ist (`chess.polyglot`). Danach prüft sie optional Syzygy-Endspieldatenbanken (`config.SYZYGY_PATH`, `chess.syzygy`), falls konfiguriert und die Figurenanzahl passt. Wenn keine dieser Quellen einen Zug liefert, startet sie die Minimax-Suche (`find_best_move_minimax`) mit Alpha-Beta-Pruning bis zur Tiefe `config.AI_DEPTH`. Die Suche verwendet eine *Kopie* des `GameState`, um das Original nicht zu verändern. Die Bewertung erfolgt durch `evaluate_board()`, die Material (`score_material`) und Spielende-Zustände berücksichtigt. Der gefundene Zug wird über eine `queue.Queue` an den Hauptthread zurückgegeben.

* **`file_io.py` & `gui/save_load_logic.py`**:
    * **Aufgabe:** Persistenz von Spielständen.
    * **Details:** `file_io.py` nutzt `pickle.dump()` zum Serialisieren des `GameState`-Objekts und `pickle.load()` zum Deserialisieren. Es verwendet `tkinter.filedialog` (`asksaveasfilename`, `askopenfilename`), um native Datei-Dialoge anzuzeigen. `gui/save_load_logic.py` wird von `event_handler.py` oder `menu_logic.py` aufgerufen und delegiert die eigentliche Arbeit an `file_io.py`. Beim Laden überschreibt `save_load_logic.load_game()` die Attribute des aktuellen `GameState`-Objekts mit den geladenen Daten.

* **`tts_utils.py` & `Tolk.py`**:
    * **Aufgabe:** Bereitstellung der Text-to-Speech-Funktionalität.
    * **Details:** `Tolk.py` ist ein ctypes-Wrapper, der die Funktionen der `Tolk.dll` (muss vorhanden sein) für Python zugänglich macht. `tts_utils.py` initialisiert Tolk (`_initialize_tolk`), stellt die `speak()`-Funktion bereit (die intern `Tolk.speak()` aufruft) und kümmert sich um das saubere Herunterfahren (`_shutdown_tolk` via `atexit`). Es implementiert auch Interrupt-Logik (`_stop_speaking` via `Tolk.silence()`) mit Debouncing.

* **`logger.py`**:
    * **Aufgabe:** Zentralisierte Konfiguration des Loggings.
    * **Details:** Die Funktion `setup_logger()` erstellt und konfiguriert einen Logger mit einem `JsonFormatter`. Sie kann so konfiguriert werden, dass sie in eine Datei (`logs/Chess.log`) und/oder die Konsole schreibt. Die meisten anderen Module importieren diese Funktion und erstellen ihren eigenen Logger mit ihrem Modulnamen (`__name__`).

* **`animations.py`**:
    * **Aufgabe:** Visuelle Darstellung von Figurenzügen.
    * **Details:** Die `Animation`-Klasse speichert Start-/Endfeld, die Figur und berechnet die Bewegung pro Frame. `start_move_animation()` erstellt eine Instanz dieser Klasse. `update_animation()` wird in der Hauptschleife aufgerufen, zeichnet das Brett ohne die animierte Figur am Startfeld, zeichnet die Figur an ihrer interpolierten Position und aktualisiert den Animationsfortschritt. `is_animating()` prüft, ob eine Animation läuft.

* **`chess_utils.py`**:
    * **Aufgabe:** Sammlung schachspezifischer Hilfsfunktionen.
    * **Details:** Bietet Funktionen wie `get_move_notation()` (wandelt `chess.Move` in SAN um), `get_game_over_text()` (ermittelt den Text für Matt, Patt etc.), `is_capture()`, `is_check()`, `get_piece_value()`, `square_to_algebraic()`, `algebraic_to_square()`, `get_square_color()`, `get_piece_color_char()`, `get_piece_symbol_upper()`. Diese Funktionen kapseln Logik der `python-chess`-Bibliothek oder greifen auf `config.py` zu.

### 3.2. GUI-Paket (`gui/`)

* **`__init__.py`**: Stellt sicher, dass `gui` als Paket erkannt wird und importiert ggf. Submodule oder richtet Paket-Logging ein.
* **`board_display.py` (`BoardDisplay` Klasse)**: Zeichnet das statische Brett (Felder, Farben), die Koordinaten (`draw_coordinates`) und bietet Methoden zum Hervorheben einzelner Felder (`highlight_square`), des letzten Zugs (`highlight_last_move`), legaler Züge (`highlight_legal_moves`) und des Königs im Schach (`highlight_check`). Zeichnet auch die Figuren (`draw_pieces`), wobei optional ein Feld ausgelassen werden kann (während der Animation).
* **`chess_gui.py`**: Ruft im `GAME`-Zustand die Methoden von `BoardDisplay` in der richtigen Reihenfolge auf, um das Brett, die Figuren und die Hervorhebungen darzustellen. Zeichnet zusätzlich die geschlagenen Figuren neben dem Brett (`draw_captured_pieces`) und den Spielende-Text (`draw_game_over_text`).
* **`startup_logic.py`**: Verantwortlich für die Darstellung und Interaktion im `MAIN_MENU` und `NEW_GAME_SUBMENU`. Zeichnet die Menü-Panels mit Titeln und Buttons. Handhabt Maus- und Tastaturnavigation innerhalb der Menüs. Startet und aktualisiert das zufällige KI-vs-KI-Spiel im Hintergrund des Hauptmenüs.
* **`menu_logic.py`**: Ähnlich wie `startup_logic`, aber für das In-Game-Pausemenü (wenn ESC gedrückt wird). Zeichnet das Menü und verarbeitet Klicks/Tastatureingaben, um Aktionen wie "Fortsetzen", "Speichern", "Laden", "Hauptmenü" oder "Beenden" auszulösen.
* **`status_display.py`**: Verwaltet eine Textzeile am oberen Bildschirmrand. Zeigt standardmäßig an, wer am Zug ist oder das Spielergebnis. Kann temporäre Nachrichten (letzter Zug, Fehler, Info) mit optionaler Anzeigedauer anzeigen (`display_message`).
* **`timer_logic.py`**: Implementiert einen einfachen Spielzeit-Timer, der hochzählt. Bietet Funktionen zum Starten, Stoppen und Zurücksetzen. `draw_game_timer()` zeigt die formatierte Zeit an.
* **`fullscreen_logic.py`**: Enthält die Funktion `toggle_fullscreen()`, die zwischen Fenster- und Vollbildmodus wechselt, indem sie `pygame.display.set_mode()` mit den entsprechenden Flags aufruft. Speichert die ursprüngliche Fenstergröße für die Rückkehr.
* **`navigation_logic.py`**: Bietet einfache Wrapper-Funktionen `undo_move()` und `redo_move()`, die die entsprechenden Methoden des `GameState`-Objekts aufrufen. Wird von `event_handler.py` genutzt.
* **`tts_integration.py`**: Dient als Brücke zwischen der Spiellogik/-GUI und `tts_utils`. Formatiert Zuginformationen (`format_move_for_speech_post_move`), Figurenauswahlen (`speak_selection`) und andere Statusmeldungen in natürlich klingende deutsche Sätze und ruft dann `tts_utils.speak()` auf.

## 4. Abhängigkeiten

* **`pygame` (>= 2.0.0 empfohlen)**: Für Grafik, Sound, Events, Fenster.
* **`python-chess` (>= 1.0)**: Für die gesamte Schachlogik und Brettmanipulation.
* **`python-json-logger`**: Für das Logging im JSON-Format.
* **`tkinter`**: Teil der Python-Standardbibliothek, wird für Dateidialoge benötigt.
* **(Optional) `Tolk.dll`**: Für die TTS-Funktion unter Windows mit Screenreadern (muss manuell bereitgestellt werden).

## 5. Funktionsweise (Detaillierter Ablauf)

1.  **Start (`main.py`)**:
    * Pygame, Mixer, Font werden initialisiert.
    * Logger wird konfiguriert.
    * Ressourcen (Bilder, Sounds) werden via `config.py` geladen.
    * `GameState` und `BoardDisplay` werden erstellt.
    * `startup_logic.initialize_main_menu()` wird aufgerufen.
    * Anfangszustand ist `MAIN_MENU`. TTS gibt Willkommensnachricht aus.
2.  **Hauptmenü-Phase (`main.py` -> `startup_logic.py`)**:
    * `startup_logic.run_main_menu_frame()` zeichnet das Menü und das Hintergrundspiel.
    * Events werden verarbeitet (Mausklick, Tastatur).
    * Bei Auswahl "Neues Spiel" -> Zustand `ANIMATING_TO_SUB`.
    * Bei Auswahl "Laden" -> `save_load_logic.load_game()` wird aufgerufen. Bei Erfolg -> Zustand `GAME`.
    * Bei Auswahl "Beenden" -> `running = False`.
3.  **Spielstart-Phase (`main.py` -> `startup_logic.py` -> `animations.py`)**:
    * Nach Auswahl "Lokales Spiel" oder "Gegen KI" im Untermenü:
        * `GameState` wird zurückgesetzt (`gs.reset_game()`).
        * KI wird ggf. konfiguriert (`config.AI_ENABLED`, `config.AI_PLAYER`).
        * Zustand wechselt zu `ANIMATING_BOARD_SLIDE`.
        * Das leere Brett wird animiert eingeschoben.
        * Zustand wechselt zu `ANIMATING_PIECE_SETUP`.
        * Figuren werden nacheinander mit Sound auf das Brett gesetzt.
        * Nach Abschluss -> Zustand `GAME`, Timer startet, Hintergrundmusik startet.
4.  **Spiel-Phase (`main.py` -> `event_handler.py`, `chess_gui.py`, `ai_opponent.py` etc.)**:
    * Hauptschleife prüft Events.
    * `event_handler.handle_events()` verarbeitet Inputs:
        * **Maus/Tastatur (Brett)**: Wählt Felder aus (`selected_square_index`), nimmt Figuren auf (`source_square_selected`), versucht Züge (`try_create_move`). Bei gültigem Zug -> `_execute_move()`.
        * `_execute_move()`: Ruft `gs.make_move()`, startet Animation (`animations.start_move_animation`), spielt Sounds (`play_move_sounds`), gibt TTS aus (`tts_integration.speak_move_after`), aktualisiert Status/Timer, setzt `player_turn_finished = True`.
        * **Tastenkürzel**: Löst Undo/Redo, Speichern/Laden, Menü, Toggles etc. aus.
    * **KI-Logik**: Wenn `player_turn_finished` und KI am Zug:
        * `ai_opponent.find_best_move()` wird in neuem Thread gestartet.
        * Hauptschleife prüft `ai_move_queue`.
        * Wenn Zug verfügbar: `_execute_move()` wird für den KI-Zug aufgerufen.
    * **Zeichnen**:
        * Wenn `animations.is_animating()`: `animations.update_animation()` zeichnet Brett + animierte Figur.
        * Sonst: `chess_gui.draw_game_state()` zeichnet statischen Zustand (Brett, Figuren, Highlights).
        * `timer_logic.draw_game_timer()` und `status_display.draw_status_display()` werden aufgerufen.
        * Wenn `menu_active`: `menu_logic.draw_menu()` wird aufgerufen.
        * Wenn `game_over`: `chess_gui.draw_game_over_text()` wird aufgerufen.
    * **Spielende-Prüfung**: `gs.is_game_over()` wird geprüft, ggf. wird `game_over`-Flag gesetzt, Timer/Musik gestoppt.
5.  **Beenden**: Wenn `running = False` gesetzt wird (durch `QUIT`-Event oder Menüauswahl), wird die Hauptschleife verlassen, Mixer und Pygame werden heruntergefahren.

## 6. Schlüsselfunktionen (Erweitert)

* **Grafik & Darstellung**: Detaillierte Brett-/Figurenanzeige (`board_display`), Animationen (`animations`), Menüs (`startup_logic`, `menu_logic`), HUD (`timer_logic`, `status_display`).
* **Schachlogik**: Nutzung von `python-chess` für Zuglegalität, Spielende-Bedingungen, FEN/SAN, Buch/Endspiel-Lookup (`game_state`, `chess_utils`, `ai_opponent`).
* **Benutzerinteraktion**: Umfassende Maus- und Tastatursteuerung inkl. Cursor, Aufnahme/Absetzen, Shortcuts (`event_handler`).
* **KI**: Minimax-Suche mit Alpha-Beta, Materialbewertung, optionale Nutzung von Eröffnungsbüchern und Endspieldatenbanken, Threading (`ai_opponent`).
* **Persistenz**: Speichern/Laden des gesamten `GameState` via `pickle`, benutzerfreundliche Dateidialoge via `tkinter` (`file_io`, `save_load_logic`).
* **Verlauf**: Undo/Redo-Funktion mit korrekter Verwaltung des `redo_stack` und der geschlagenen Figuren (`game_state`, `navigation_logic`).
* **Feedback**: Visuelle Hervorhebungen, Soundeffekte für Aktionen (`config`, `event_handler`), Statusmeldungen (`status_display`).
* **Barrierefreiheit**: TTS-Ausgabe für alle wichtigen Spielaktionen und Zustände über Tolk-Integration (`tts_utils`, `Tolk`, `tts_integration`).
* **Konfiguration & Modularität**: Zentrale `config.py`, klare Trennung der Verantwortlichkeiten in Module und ein GUI-Paket.
* **Logging**: Detailliertes Logging aller wichtigen Vorgänge und Fehler in eine Datei (`logger`).

## 7. Setup und Ausführung

1.  **Python**: Stelle sicher, dass eine kompatible Python-Version (z.B. 3.8+) installiert ist.
2.  **Abhängigkeiten**: Navigiere im Terminal zum `PyChess`-Verzeichnis und führe aus: `pip install -r requirements.txt`
3.  **(Optional) Tolk**: Lade die Tolk-Bibliothek herunter und platziere `Tolk.dll` im `PyChess`-Verzeichnis (oder passe den Pfad in `config.py` an).
4.  **Ausführen**: Starte das Spiel vom `PyChess`-Verzeichnis aus: `python main.py`

## 8. Fazit

PyChess demonstriert eine solide Architektur für ein Schachspiel mit Pygame. Die Trennung von Logik, GUI und Konfiguration sowie die Nutzung externer Bibliotheken wie `python-chess` ermöglichen eine funktionsreiche und erweiterbare Anwendung. Besonderes Augenmerk wurde auf Benutzerfeedback durch Animationen, Sounds und TTS gelegt.
