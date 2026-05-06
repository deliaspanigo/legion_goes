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
import re



# --- SOT LIBRARIES (Para el core de procesamiento) ---
from legion_goes.satpy_config.my_config_satpy import CACHE_DIR   # Cache Folder!
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id

# =============================================================================
# 1. DICCIONARIO DE DEFINICIÓN DE SALIDAS
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
        "goes_native_grey_png":  f"{str_name}_CRS-Goes{str_position}_LSTF-fnp01-Celsius-Grey.png",
        "goes_native_color_png": f"{str_name}_CRS-Goes{str_position}_LSTF-fnp01-Celsius-Color.png",
        "wgs84_grey_png":        f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Grey.png",
        "wgs84_color_png":       f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Color.png",
        "wgs84_grey_tif":        f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Grey.tif",
        "wgs84_color_tif":       f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Color.tif"
    }
    
    return dict_output_schema
    
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
        print(f"\n      [Step 01/06] 🛰️   Loading LST Scene...", end=" ", flush=True)
        #########scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc', reader_kwargs={'chunks': my_chunks})
        prod_raw  = 'LST' # IS NOT LSTF THE NAME INSIDE .nc files!!!!!!!!!!!! ##########################
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
        #####scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
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
        dict_output_file_name = gen_dict_output_file_name(nc_path=str(target_nc))
        dict_output_file_path = {k: str(test_out / v) for k, v in dict_output_file_name.items()}

        
        # Execute processing
        success = run_proc_ABI_L2_LSTF_fnp01(nc_path=str(target_nc), **dict_output_file_path)
        
        if success:
            print("-" * 80 + "\n✅ TEST COMPLETED SUCCESSFULLY\n" + "=" * 80)
        else:
            print("-" * 80 + "\n❌ TEST FAILED\n" + "=" * 80)
