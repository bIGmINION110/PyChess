# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# --- ANPASSBARE VARIABLEN ---

# Der absolute Pfad zum Hauptverzeichnis deines Projekts (wo main.py liegt)
# Passe diesen Pfad an deine Verzeichnisstruktur an!
project_base_path = os.path.abspath(os.path.dirname(__name__))

# Der Name für deine ausführbare Datei
app_name = 'Schach'

# Der Pfad zur Icon-Datei (.ico für Windows)
# icon_path = os.path.join(project_base_path, 'bK.ico')

# Der Pfad zur Tolk DLL
# Annahme: Sie liegt im selben Verzeichnis wie main.py
tolk_dll_path = os.path.join(project_base_path, 'Tolk.dll')

# Der Pfad zum Assets-Ordner
assets_folder_path = os.path.join(project_base_path, 'assets')

# Soll die Konsole angezeigt werden (True zum Debuggen, False für finales Release)?
show_console = False

# Soll eine einzelne .exe-Datei erstellt werden?
create_one_file = True

# --- ENDE ANPASSBARE VARIABLEN ---

# --- PyInstaller Konfiguration ---

block_cipher = None

# Liste der Binärdateien (DLLs, SOs etc.)
# Format: ('Pfad/zur/Quelldatei', 'Zielverzeichnis im Bundle')
# '.' bedeutet das Hauptverzeichnis des Bundles
binaries_list = []
if os.path.exists(tolk_dll_path):
    binaries_list.append((tolk_dll_path, '.'))
else:
    print(f"WARNUNG: Tolk.dll nicht gefunden unter {tolk_dll_path}. Sie wird nicht eingebunden.")

# Liste der Datendateien und Ordner
# Format: ('Pfad/zur/Quelldatei_oder_Ordner', 'Zielverzeichnis_oder_Datei_im_Bundle')
datas_list = []
if os.path.exists(assets_folder_path):
    datas_list.append((assets_folder_path, 'assets'))
else:
    print(f"WARNUNG: Assets-Ordner nicht gefunden unter {assets_folder_path}. Er wird nicht eingebunden.")

# Liste der explizit anzugebenden (versteckten) Imports
# Füge hier Module hinzu, die PyInstaller möglicherweise nicht automatisch findet.
hidden_imports_list = [
    'pygame',
    'Tolk',
    'tts_utils',
    'gui',
    'file_io',
    'config',
    'ai_opponent',
    'game_state',
    'animations',
    'chess_utils',
    'event_handler',
    'logger',
    'pythonjsonlogger', # Abhängigkeit von logger.py
    'pickle',
    'tkinter',
    'tkinter.filedialog',
    'traceback',
    'atexit',
    'ctypes',
    'random',
    'queue',
    'threading',
    'chess.polyglot', # Für Eröffnungsbücher
    'chess.syzygy',   # Für Endspieldatenbanken (falls genutzt)
    # Eventuell GUI-Submodule, falls der 'gui'-Import nicht reicht:
    'gui.board_display',
    'gui.chess_gui',
    'gui.fullscreen_logic',
    'gui.menu_logic',
    'gui.navigation_logic',
    'gui.save_load_logic',
    'gui.startup_logic',
    'gui.status_display',
    'gui.timer_logic',
    'gui.tts_integration',
]

a = Analysis(
    ['main.py'],  # Dein Hauptskript
    pathex=[project_base_path],  # Fügt dein Projektverzeichnis zum Suchpfad hinzu
    binaries=binaries_list,
    datas=datas_list,
    hiddenimports=hidden_imports_list,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if create_one_file:
    # --- Konfiguration für --onefile ---
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True, # Binaries werden separat gesammelt
        name=app_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=show_console,
        #icon=icon_path
    )
    # Sammle alle Abhängigkeiten in einem BUNDLE für onefile
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=app_name # Der Name des temporären Ordners beim Ausführen
    )
else:
    # --- Konfiguration für --onedir ---
    exe = EXE(
        pyz,
        a.scripts,
        [], # Leere Liste, da COLLECT verwendet wird
        exclude_binaries=True,
        name=app_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=show_console,
        #icon=icon_path
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=app_name # Name des Ausgabeordners in dist/
    )