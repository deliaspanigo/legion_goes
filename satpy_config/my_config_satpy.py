# =============================================================================
# FILE PATH: legion_goes/satpy_config/my_config_satpy.py
# Version: 1.8.6
# Description: Custom Satpy configuration loader for Legion GOES.
# =============================================================================
import satpy
from pathlib import Path
import os

# 1. Rutas absolutas basadas en la ubicación del archivo (satpy_config/)
BASE_DIR = Path(__file__).resolve().parent
PROJ_DIR = BASE_DIR.parent  # Sube a legion_goes/
CACHE_DIR = PROJ_DIR / "satpy_cache"

# Crea el cache si no existe
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 2. Configuración recomendada (lista obligatoria)
satpy.config.set(
    config_path=[str(BASE_DIR)],  # Lista, incluye tus composites y enhancements
    cache_dir=str(CACHE_DIR),
    log_level="ERROR",  # Más limpio que WARNING
    default_resampler="kd_tree"
)

# 3. Variable de entorno para Pyresample
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

# 4. Mensaje de auditoría (para tu tesis y debug)
print("--- SatPy Configuration Loaded (Legion GOES v0.3.1) ---")
print(f"  Cache directory: {CACHE_DIR}")
print(f"  Config paths added: {BASE_DIR}")
print(f"  Current config paths: {satpy.config.get('config_path')}")
print("---------------------------------------")
