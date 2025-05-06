###
 #  Product:        Tolk
 #  File:           Tolk.py
 #  Description:    Python wrapper module.
 #  Copyright:      (c) 2014, Davy Kager <mail@davykager.nl>
 #  License:        LGPLv3
 ##
from ctypes import cdll, CFUNCTYPE, c_bool, c_wchar_p
import os
from ctypes import cdll, WinDLL # WinDLL hinzugefügt
import logger, logging

log = logger.setup_logger(
    name="Tolk",
    log_file='logs/PyChess.txt',
    level=logging.DEBUG,
    console=True,)
log.info("<--- Starte Module: 'Tolk.py' --->")

# Verzeichnis ermitteln, in dem Tolk.py liegt
_tolk_dir = os.path.dirname(os.path.abspath(__file__))
# Vollständigen Pfad zur DLL erstellen
_tolk_dll_path = os.path.join(_tolk_dir, "Tolk.dll")

print(f"DEBUG: Versuche Tolk.dll zu laden von: {_tolk_dll_path}") # Debug-Ausgabe hinzugefügt

# Versuche, die DLL mit dem vollen Pfad zu laden
try:
    # WinDLL ist oft für Windows-APIs nötig (__stdcall)
    _tolk = WinDLL(_tolk_dll_path)
    print("DEBUG: Tolk.dll erfolgreich mit WinDLL geladen.") # Debug-Ausgabe
except OSError as e1:
    print(f"WARNUNG: Laden von Tolk.dll via WinDLL fehlgeschlagen: {e1}")
    try:
         # Fallback auf cdll (__cdecl)
         print("DEBUG: Versuche Fallback mit cdll...")
         _tolk = cdll.LoadLibrary(_tolk_dll_path)
         print("DEBUG: Tolk.dll erfolgreich mit cdll.LoadLibrary geladen.") # Debug-Ausgabe
    except OSError as e2:
         print(f"FEHLER: Laden von Tolk.dll via cdll auch fehlgeschlagen: {e2}")
         # Fehler weitergeben, damit das Skript abbricht
         raise e2
except Exception as e:
     print(f"FEHLER: Unerwarteter Fehler beim Laden von Tolk.dll: {e}")
     raise e

# Der Rest der Tolk.py Datei bleibt unverändert...

_proto_load = CFUNCTYPE(None)
load = _proto_load(("Tolk_Load", _tolk))

_proto_is_loaded = CFUNCTYPE(c_bool)
is_loaded = _proto_is_loaded(("Tolk_IsLoaded", _tolk))

_proto_unload = CFUNCTYPE(None)
unload = _proto_unload(("Tolk_Unload", _tolk))

_proto_try_sapi = CFUNCTYPE(None, c_bool)
_param_try_sapi = (1, "try_sapi"),
try_sapi = _proto_try_sapi(("Tolk_TrySAPI", _tolk), _param_try_sapi)

_proto_prefer_sapi = CFUNCTYPE(None, c_bool)
_param_prefer_sapi = (1, "prefer_sapi"),
prefer_sapi = _proto_prefer_sapi(("Tolk_PreferSAPI", _tolk), _param_prefer_sapi)

_proto_detect_screen_reader = CFUNCTYPE(c_wchar_p)
detect_screen_reader = _proto_detect_screen_reader(("Tolk_DetectScreenReader", _tolk))

_proto_has_speech = CFUNCTYPE(c_bool)
has_speech = _proto_has_speech(("Tolk_HasSpeech", _tolk))

_proto_has_braille = CFUNCTYPE(c_bool)
has_braille = _proto_has_braille(("Tolk_HasBraille", _tolk))

_proto_output = CFUNCTYPE(c_bool, c_wchar_p, c_bool)
_param_output = (1, "str"), (1, "interrupt", False)
output = _proto_output(("Tolk_Output", _tolk), _param_output)

_proto_speak = CFUNCTYPE(c_bool, c_wchar_p, c_bool)
_param_speak = (1, "str"), (1, "interrupt", False)
speak = _proto_speak(("Tolk_Speak", _tolk), _param_speak)

_proto_braille = CFUNCTYPE(c_bool, c_wchar_p)
_param_braille = (1, "str"),
braille = _proto_braille(("Tolk_Braille", _tolk), _param_braille)

_proto_is_speaking = CFUNCTYPE(c_bool)
is_speaking = _proto_is_speaking(("Tolk_IsSpeaking", _tolk))

_proto_silence = CFUNCTYPE(c_bool)
silence = _proto_silence(("Tolk_Silence", _tolk))
