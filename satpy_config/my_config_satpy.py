# =============================================================================
# FILE PATH: legion_goes/satpy_config/my_config_satpy.py
# Version: 1.8.6
# Description: Custom Satpy configuration loader for Legion GOES.
# =============================================================================
import satpy
from pathlib import Path
import os

# 1. Absolute paths based on the file location (satpy_config/)
BASE_DIR = Path(__file__).resolve().parent
PROJ_DIR = BASE_DIR.parent  # Sube a legion_goes/

_cache_from_env = (
    os.environ.get("LEGIONGOES_SATPY_CACHE_DIR")
    or os.environ.get("LEGION_CACHE_DIR")
)

if _cache_from_env:
    CACHE_DIR = Path(_cache_from_env).expanduser().resolve()
else:
    CACHE_DIR = (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        / "LegionGOES_LAB"
        / "cache"
        / "satpy"
    ).resolve()

# Crea el cache si no existe
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 2. Recommended configuration (required list)
satpy.config.set(
    config_path=[str(BASE_DIR)],  # Lista, incluye tus composites y enhancements
    cache_dir=str(CACHE_DIR),
    log_level="ERROR",  # Cleaner than WARNING
    default_resampler="kd_tree"
)

# 3. Variable de entorno para Pyresample
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

# 4. Audit message (for thesis work and debugging)
print("--- SatPy Configuration Loaded (Legion GOES v0.3.1) ---")
print(f"  Cache directory: {CACHE_DIR}")
print(f"  Config paths added: {BASE_DIR}")
print(f"  Current config paths: {satpy.config.get('config_path')}")
print("---------------------------------------")
