"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_LSTF/run_proc_ABI_L2_LSTF_fnp01.py
Sentence: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_LSTF.proc_ABI_L2_LSTF_fnp01
Version: 1.8.9 (Simple & Robust Main)
Description: FNP01 - Land Surface Temperature with Universal Path Detection.
"""

import os
import sys
import time
import gc
import json
import warnings
import logging
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime

# --- Satpy & Resampling ---
from satpy import Scene
from pyresample.geometry import AreaDefinition

# --- SOT LIBRARIES (Para el core de procesamiento) ---
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder

# --- UTILIDAD PARA SILENCIAR STDERR ---
@contextmanager
def silence_stderr():
    new_target = open(os.devnull, "w")
    old_target = sys.stderr
    sys.stderr = new_target
    try:
        yield new_target
    finally:
        sys.stderr = old_target
        new_target.close()

logging.getLogger('satpy').setLevel(logging.ERROR)
logging.getLogger('pyresample').setLevel(logging.ERROR)

# =============================================================================
# 1. DICCIONARIO DE DEFINICIÓN DE SALIDAS
# =============================================================================
dict_output_schema = {
    "goes_native_grey_png":  "CRS-GoesEast_LST_Grey.png",
    "goes_native_color_png": "CRS-GoesEast_LST_Color.png",
    "wgs84_grey_png":        "CRS-WGS84_LST_Grey.png",
    "wgs84_color_png":       "CRS-WGS84_LST_Color.png",
    "wgs84_grey_tif":        "CRS-WGS84_LST_Grey.tif",
    "wgs84_color_tif":       "CRS-WGS84_LST_Color.tif"
}

# =============================================================================
# 2. FUNCIÓN DE PROCESAMIENTO (Core Logic)
# =============================================================================

def run_proc_ABI_L2_LSTF_fnp01(nc_path, **kwargs):
    file_path = Path(nc_path)
    
    # Cache path usando SOT
    try:
        path_cache = get_SOT_specific_folder("proc_core01") / ".cache_pyresample"
    except:
        path_cache = Path.cwd() / ".cache_pyresample"
    
    try:
        first_output = list(kwargs.values())[0]
        Path(first_output).parent.mkdir(parents=True, exist_ok=True)

        print(f"\n      [Step 01/06] 🛰️  Loading LST Scene...", end=" ", flush=True)
        with silence_stderr(), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
            prod_raw  = 'LST'
            prod_color = 'lst_celsius_color01'
            scn.load([prod_raw])
            scn[prod_raw] = scn[prod_raw] - 273.15
            scn[prod_raw].attrs['units'] = 'Celsius'
            try:
                scn.load([prod_color])
            except:
                prod_color = None
        print("Done.")

        print(f"      [Step 02/06] 📸  Saving Native PNGs...", end=" ", flush=True)
        scn.save_dataset(prod_raw, filename=kwargs.get("goes_native_grey_png"), writer='simple_image')
        if prod_color and kwargs.get("goes_native_color_png"):
            scn.save_dataset(prod_color, filename=kwargs.get("goes_native_color_png"))
        print("Done.")

        print(f"      [Step 03/06] 🔄  Resampling to WGS84 Area...", end=" ", flush=True)
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        print("Done.")

        print(f"      [Step 04/06] 💾  Saving WGS84 GeoTIFFs...", end=" ", flush=True)
        scn_res.save_dataset(prod_raw, filename=kwargs.get("wgs84_grey_tif"), writer='geotiff')
        if prod_color and kwargs.get("wgs84_color_tif"):
            scn_res.save_dataset(prod_color, filename=kwargs.get("wgs84_color_tif"), writer='geotiff')
        print("Done.")

        print(f"      [Step 05/06] 📸  Saving WGS84 PNGs...", end=" ", flush=True)
        scn_res.save_dataset(prod_raw, filename=kwargs.get("wgs84_grey_png"), writer='simple_image')
        if prod_color and kwargs.get("wgs84_color_png"):
            scn_res.save_dataset(prod_color, filename=kwargs.get("wgs84_color_png"))
        print("Done.")

        print(f"      [Step 06/06] 📝  Cleaning...", end=" ", flush=True)        
        del scn; del scn_res; gc.collect()
        print("Done.")
        return True
    except Exception as e:
        print(f"\n      ❌ [FNP01 ERROR] {str(e)}")
        return False

# =============================================================================
# MAIN SIMPLE (Jupyter & Terminal)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP01: LSTF DIAGNOSTIC TEST ".center(80, "="))
    
    # 1. Path de ejecución (Donde estás parado)
    working_dir = Path.cwd() / "test_one_image"
    
    # 2. Buscar primer .nc que contenga 'LSTF'
    nc_candidates = sorted(list(working_dir.glob("*LSTF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No se encontró ningún archivo .nc con 'LSTF' en: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        test_out = working_dir / "test_outputs" / target_nc.stem
        test_out.mkdir(parents=True, exist_ok=True)

        print(f"🎯 ARCHIVO: {target_nc.name}")
        print(f"📂 SALIDA : {test_out}")
        print("-" * 80)

        # Inyectar rutas
        test_paths = {k: str(test_out / v) for k, v in dict_output_schema.items()}
        
        # Ejecutar
        run_proc_ABI_L2_LSTF_fnp01(nc_path=str(target_nc), **test_paths)
        print("-" * 80 + "\n✅ TEST FINALIZADO\n" + "=" * 80)
