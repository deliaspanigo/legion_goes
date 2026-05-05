"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_LSTF/run_proc_ABI_L2_LSTF_fnp01.py
Version: 0.0.2 (Simple & Robust Main)
Description: Original Code - LSTF fnp01.
Last modification: 05-05-2026 18:18
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_LSTF.proc_ABI_L2_LSTF_fnp01
# =========================================================================================================================================


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
from satpy import Scene
from pyresample.geometry import AreaDefinition




# --- SOT LIBRARIES (Para el core de procesamiento) ---
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder   # Cache Folder!



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

    """
    Executes the Full Network Processing (FNP) pipeline.
    Steps include loading, masking, reprojecting.
    """
    
    # Basics
    start_time = time.time()
    file_path = Path(nc_path)
    
    # Cache path usando SOT
    try:
        path_cache = get_SOT_specific_folder("proc_core01") / ".cache_pyresample"
    except:
        path_cache = Path.cwd() / ".cache_pyresample"
    
    try:
        # -----------------------------------------------------------------------------------------------------------------
        # Output folder
        first_output_file_path = list(kwargs.values())[0]
        the_output_folder = Path(first_output_file_path).parent
        the_output_folder.mkdir(parents=True, exist_ok=True)
        print(f"output_folder = {the_output_folder}")
        
        # -----------------------------------------------------------------------------------------------------------------
        print(f"\n      [Step 01/06] 🛰️   Loading LST Scene...", end=" ", flush=True)
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        prod_raw  = 'LST'
        prod_color = 'lst_celsius_color01'  #Special processing created by me.
        scn.load([prod_raw])
        scn[prod_raw] = scn[prod_raw] - 273.15
        scn[prod_raw].attrs['units'] = 'Celsius'
        try:
            scn.load([prod_color])
        except:
            prod_color = None
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 02/06] 📸  Saving Native PNGs...", end=" ", flush=True)
        scn.save_dataset(prod_raw, filename=kwargs.get("goes_native_grey_png"), writer='simple_image')
        if prod_color and kwargs.get("goes_native_color_png"):
            scn.save_dataset(prod_color, filename=kwargs.get("goes_native_color_png"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 03/06] 🔄  Resampling GOES projection to WGS84...", end=" ", flush=True)
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 04/06] 💾  Saving WGS84 GeoTIFFs...", end=" ", flush=True)
        scn_res.save_dataset(prod_raw, filename=kwargs.get("wgs84_grey_tif"), writer='geotiff')
        if prod_color and kwargs.get("wgs84_color_tif"):
            scn_res.save_dataset(prod_color, filename=kwargs.get("wgs84_color_tif"), writer='geotiff')
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 05/06] 📸  Saving WGS84 PNGs...", end=" ", flush=True)
        scn_res.save_dataset(prod_raw, filename=kwargs.get("wgs84_grey_png"), writer='simple_image')
        if prod_color and kwargs.get("wgs84_color_png"):
            scn_res.save_dataset(prod_color, filename=kwargs.get("wgs84_color_png"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 06/06] 📸  End...")
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        print(f"        [Summary] Total time: {duration}s")
        print(f"        [Status] Process finished successfully.")
        print(f"        Done.")
        
        # -----------------------------------------------------------------------------------------------------------------
        # Free memory explicit
        del scn
        if 'scn_res' in locals(): del scn_res
        gc.collect()
        
        # -----------------------------------------------------------------------------------------------------------------
        return True
        
    except Exception as e:
        print(f"\n      ❌ [FNP01 ERROR] {str(e)}")
        return False

# =============================================================================
# SIMPLE MAIN (Jupyter & Terminal)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP01: LSTF DIAGNOSTIC TEST ".center(80, "="))
    
    # 1. Working Directory (Current location)
    working_dir = Path.cwd() / "test_one_image"
    
    # 2. Search for the first .nc file containing 'LSTF'
    nc_candidates = sorted(list(working_dir.glob("*LSTF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No .nc files with 'LSTF' found in: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        test_out = working_dir / "test_outputs" / target_nc.stem
        test_out.mkdir(parents=True, exist_ok=True)

        print(f"🎯 FILE  : {target_nc.name}")
        print(f"📂 OUTPUT: {test_out}")
        print("-" * 80)

        # Inject output paths
        test_paths = {k: str(test_out / v) for k, v in dict_output_schema.items()}
        
        # Execute processing
        success = run_proc_ABI_L2_LSTF_fnp01(nc_path=str(target_nc), **test_paths)
        
        if success:
            print("-" * 80 + "\n✅ TEST COMPLETED SUCCESSFULLY\n" + "=" * 80)
        else:
            print("-" * 80 + "\n❌ TEST FAILED\n" + "=" * 80)
