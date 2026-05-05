"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_MCMIPF/proc_ABI_L2_MCMIPF_fnp01.py
Version: 0.0.3 (Simple & Robust Main)
Description: Core Processing Code - MCMIPF fnp01.
Last modification: 05-05-2026 20:30
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01
# =========================================================================================================================================

# Libraries
import os
import sys
import time
import gc
import json
import inspect
import warnings
import logging
from contextlib import contextmanager, redirect_stderr
from pathlib import Path
from datetime import datetime
from satpy import Scene
from pyresample.geometry import AreaDefinition
import numpy as np 


# =============================================================================
# 1. OUTPUT SCHEMA DEFINITION
# =============================================================================
dict_output_schema = {
    "png_CRSnative_true_color": "CRS-GoesEast_TrueColor.png",
    "png_CRSnative_true_color_day_only": "CRS-GoesEast_TrueColor_DayOnly.png",
    "png_CRSwgs84_true_color": "CRS-WGS84_TrueColor.png",
    "png_CRSwgs84_true_color_day_only": "CRS-WGS84_TrueColor_DayOnly.png",
    "tif_CRSwgs84_true_color": "CRS-WGS84_TrueColor.tif"
}

# =============================================================================
# 2. DARK PIXEL MASK FUNCTION
# =============================================================================
def apply_dark_pixel_mask(data_array, threshold=0.05):
    """Filters out pixels with intensity below the threshold."""
    avg_intensity = data_array.mean(dim='bands')
    return data_array.where(avg_intensity > threshold)


# =============================================================================
# 3. CORE PROCESSING FUNCTION
# =============================================================================

def run_proc_ABI_L2_MCMIPF_fnp01(nc_path, **kwargs):
    """
    Executes the Full Network Processing (FNP) pipeline.
    Steps include loading, masking, reprojecting, and metadata generation.
    """
    start_time = time.time()
    
    try:
        # -----------------------------------------------------------------------------------------------------------------
        # Output folder
        first_output_file_path = list(kwargs.values())[0]
        the_output_folder = Path(first_output_file_path).parent
        the_output_folder.mkdir(parents=True, exist_ok=True)
        print(f"output_folder = {the_output_folder}")

        # -----------------------------------------------------------------------------------------------------------------
        # Initializing the Scene and loading the True Color composite
        print(f"\n      [Step 01/09] 🛰️   Loading ABI bands...", end=" ", flush=True)
        scn = Scene(filenames=[nc_path], reader='abi_l2_nc')
        scn.load(['true_color'])
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Exporting the image in the original satellite projection
        print(f"      [Step 02/09] 🖼️   Saving Native True Color PNG...", end=" ", flush=True)
        scn.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSnative_true_color"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Applying luminance threshold to filter out night pixels
        print(f"      [Step 03/09] 🎭  Applying Dark Pixel Mask...", end=" ", flush=True)
        scn_day = scn.copy()
        scn_day['true_color'] = apply_dark_pixel_mask(scn_day['true_color'], threshold=0.05)
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Exporting the masked image in native projection
        print(f"      [Step 04/09] ☀️   Saving Native Day-Only PNG...", end=" ", flush=True)
        scn_day.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSnative_true_color_day_only"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Setting up the target geographic projection (Equirectangular)
        print(f"      [Step 05/09] 🗺️   Defining WGS84 Area Definition...", end=" ", flush=True)
        area_def = AreaDefinition(
            'wgs84', 'LatLon', 'wgs84',
            {'proj': 'eqc', 'units': 'm', 'ellps': 'WGS84'},
            3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Projecting the full scene to LatLon coordinate system
        print(f"      [Step 06/09] 🔄  Resampling Scene to WGS84...", end=" ", flush=True)
        scn_res = scn.resample(area_def)
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Exporting both PNG and GeoTIFF for GIS compatibility
        print(f"      [Step 07/09] 💾  Saving WGS84 PNG and GeoTIFF...", end=" ", flush=True)
        scn_res.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSwgs84_true_color"))
        scn_res.save_datasets(writer='geotiff', datasets=['true_color'], filename=kwargs.get("tif_CRSwgs84_true_color"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Projecting and saving the masked version in WGS84
        print(f"      [Step 08/09] 💾  Saving WGS84 Day-Only PNG...", end=" ", flush=True)
        scn_res_day = scn_day.resample(area_def)
        scn_res_day.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSwgs84_true_color_day_only"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 09/09] 📸  End...")
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
        
        return True

    except Exception as e:
        print(f"\n      ❌ [FNP01 ERROR] {str(e)}")
        return False


# =============================================================================
# DIAGNOSTIC MAIN (Local testing only)
# =============================================================================
if __name__ == "__main__":
    # --- CONTEXT INJECTION ---
    try:
        from legion_goes.satpy_config import my_config_satpy
        print("✅ Global Satpy Config loaded for diagnostic test.")
    except ImportError:
        print("⚠️  Global config not found. Running with Satpy defaults.")

    print("\n" + " FNP01: IN-SITU DIAGNOSTIC TEST ".center(80, "="))
    
    # 1. Execution Path
    working_dir = Path.cwd() 
    current_dir = working_dir / "test_one_image"
    nc_candidates = sorted(list(current_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No .nc files found in {current_dir}")
        print("💡 Place a GOES NetCDF file in this folder to test.")
    else:
        target_nc = nc_candidates[0]
        
        # 2. Configure Output Directory
        test_output_base = current_dir / "test_outputs" / target_nc.stem
        test_output_base.mkdir(parents=True, exist_ok=True)

        # 3. Build Real Path Dictionary (Simulating the Executor)
        test_paths = {
            k: str(test_output_base / v) 
            for k, v in dict_output_schema.items()
        }

        print(f"🎯 NC File   : {target_nc.name}")
        print(f"📂 Test Out  : {test_output_base}")
        print("-" * 80)

        # 4. Execute Core with the Splat Operator (**)
        success = run_proc_ABI_L2_MCMIPF_fnp01(
            nc_path=str(target_nc),
            **test_paths
        )

        if success:
            print("-" * 80)
            print(f"✅ TEST COMPLETED SUCCESSFULLY")
            print(f"📸 Check results in: {test_output_base}")
        else:
            print("-" * 80)
            print(f"❌ TEST FAILED. Check error messages above.")

    print("=" * 80 + "\n")
