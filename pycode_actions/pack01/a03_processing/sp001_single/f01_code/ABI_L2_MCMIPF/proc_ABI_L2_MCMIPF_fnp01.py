"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_MCMIPF/proc_ABI_L2_MCMIPF_fnp01.py
Version: 0.0.3 (Simple & Robust Main)
Description: Core Processing Code - MCMIPF fnp01.
Last modification: 05-05-2026 20:30
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01
# =========================================================================================================================================

# --- Libraries
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
import re 

# --- Local  Libraries
from legion_goes.satpy_config.my_config_satpy import CACHE_DIR   # Cache Folder!
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id

# =============================================================================
# 1. OUTPUT SCHEMA DEFINITION
# =============================================================================
def gen_dict_output_file_name(nc_path): 

    nc_file_name = Path(nc_path).name
    match = re.search(r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})", nc_file_name)
    
    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    # Extract data from match
    str_prod = match.group("prod")
    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start") 
    str_position = get_position_by_sat_id(sat_id = str_sat_number)
    
    str_name = f"SP-01-simple_G{str_sat_number}-{str_position}-s{str_stimestamp}"
    
    dict_output_schema = {
        "png_CRSnative_true_color":          f"{str_name}_CRS-Goes{str_position}_MCMIPF-fnp01-TrueColor.png",
        "png_CRSnative_true_color_day_only": f"{str_name}_CRS-Goes{str_position}_MCMIPF-fnp01-TrueColor-DayOnly.png",
        "png_CRSwgs84_true_color":           f"{str_name}_CRS-WGS84_MCMIPF-fnp01-TrueColor.png",
        "png_CRSwgs84_true_color_day_only":  f"{str_name}_CRS-WGS84_MCMIPF-fnp01-TrueColor-DayOnly.png",
        "tif_CRSwgs84_true_color":           f"{str_name}_CRS-WGS84_MCMIPF-fnp01-TrueColor.tif"
    }

    
    return dict_output_schema
    


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
    file_path = Path(nc_path)
    
    # Cache path usando SOT
    path_cache = CACHE_DIR
    resample_kwargs = {
        'cache_dir': str(path_cache),
        'nprocs': 4,              # Usa más núcleos para el cálculo inicial
        'static_data': True       # Fuerza a tratar la geometría como fija
    }
    my_chunks = {'y': 1024, 'x': 1024}
    
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
        ####scn = Scene(filenames=[nc_path], reader='abi_l2_nc')
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc', reader_kwargs={'chunks': my_chunks})
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
        #area_def = AreaDefinition(
        #    'wgs84', 'LatLon', 'wgs84',
        #    {'proj': 'eqc', 'units': 'm', 'ellps': 'WGS84'},
        #    3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        #)
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        # Projecting the full scene to LatLon coordinate system
        print(f"      [Step 06/09] 🔄  Resampling Scene to WGS84...", end=" ", flush=True)
        #####scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
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
        #### scn_res_day = scn_day.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_day = scn_day.resample(area_def, resampler='kd_tree', **resample_kwargs)
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

        print(f"🎯 FILE  : {target_nc.name}")
        print(f"📂 OUTPUT: {test_output_base}")
        print("-" * 80)

        # Inject output paths
        dict_output_file_name = gen_dict_output_file_name(nc_path=str(target_nc))
        dict_output_file_path = {k: str(test_output_base / v) for k, v in dict_output_file_name.items()}

        
        # 4. Execute Core with the Splat Operator (**)
        success = run_proc_ABI_L2_MCMIPF_fnp01(nc_path=str(target_nc), **dict_output_file_path)



        if success:
            print("-" * 80)
            print(f"✅ TEST COMPLETED SUCCESSFULLY")
            print(f"📸 Check results in: {test_output_base}")
        else:
            print("-" * 80)
            print(f"❌ TEST FAILED. Check error messages above.")

    print("=" * 80 + "\n")
