"""Type Striker - a typing vertical shooter by Shouku Games."""
__version__ = "0.1.1"

# True when running in a web browser (pygbag / WebAssembly).
import sys as _sys
WEB = _sys.platform == "emscripten"
