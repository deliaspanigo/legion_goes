"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_FDCF/proc_ABI_L2_FDCF_fnp01.py
Version: 0.0.4 (Explicit Linear Processing)
Description: Core Processing Code - FDCF fnp01 with explicit independent steps.
Last modification: 06-05-2026 21:00
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_FDCF.proc_ABI_L2_FDCF_fnp01
# =========================================================================================================================================

import os
import sys
import time
import gc
import re
from pathlib import Path
from satpy import Scene
from pyresample.geometry import AreaDefinition

# --- Local Libraries
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

    str_sat_number = match.group("sat")[1:]
    str_stimestamp = match.group("start") 
    str_position = get_position_by_sat_id(sat_id = str_sat_number)
    str_name = f"SP-01-simple_G{str_sat_number}-{str_position}-s{str_stimestamp}"
    
    return {
        "goes_native_color01_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color01.png",
        "wgs84_color01_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color01.tif",
        "wgs84_color01_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color01.png",
        
        "goes_native_color02_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color02.png",
        "wgs84_color02_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color02.tif",
        "wgs84_color02_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color02.png",
        
        "goes_native_color03_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color03.png",
        "wgs84_color03_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color03.tif",
        "wgs84_color03_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color03.png",
        
        "goes_native_color04_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color04.png",
        "wgs84_color04_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color04.tif",
        "wgs84_color04_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color04.png",
        
        "goes_native_color05_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color05.png",
        "wgs84_color05_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color05.tif",
        "wgs84_color05_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color05.png",
    }

# =============================================================================
# 3. CORE PROCESSING FUNCTION
# =============================================================================

def run_proc_ABI_L2_FDCF_fnp01(nc_path, **kwargs):
    
    start_time = time.time()
    file_path = Path(nc_path)
    
    # Cache path usando SOT
    path_cache = CACHE_DIR
    resample_kwargs = {
        'cache_dir': str(path_cache),
        'nprocs': 4,              # Usa ms ncleos para el clculo inicial
        'static_data': True       # Fuerza a tratar la geometra como fija
    }
    my_chunks = {'y': 1024, 'x': 1024}

    try:
        # 0. Set up output folder and WGS84 area
        first_path = list(kwargs.values())[0]
        Path(first_path).parent.mkdir(parents=True, exist_ok=True)
        
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])

        # 1. Inicializar Scene
        ####scn = Scene(filenames=[nc_path], reader='abi_l2_nc')
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc', reader_kwargs={'chunks': my_chunks})
        
        
        # --- BLOQUE INDEPENDIENTE: COLOR 01 ---
        print(f"\n      [Step 01/05]   Processing Color 01 (my_fdc_fn01)...", flush=True)
        prod_01 = 'my_fdc_fn01'
        scn.load([prod_01])
        
        # Guardar Native
        scn.save_dataset(prod_01, filename=kwargs.get("goes_native_color01_png"), writer='simple_image')
        
        # Resample y guardar WGS84 (Tif y Png)
        ##### scn_res_01 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_01 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_01.save_dataset(prod_01, filename=kwargs.get("wgs84_color01_tif"), writer='geotiff')
        scn_res_01.save_dataset(prod_01, filename=kwargs.get("wgs84_color01_png"), writer='simple_image')
        
        # Limpieza Bloque 01
        del scn_res_01
        scn.unload(prod_01)
        gc.collect()
        print("      Done and Cleared.")

        # --- BLOQUE INDEPENDIENTE: COLOR 02 ---
        print(f"      [Step 02/05]   Processing Color 02 (my_fdc_fn02)...", flush=True)
        prod_02 = 'my_fdc_fn02'
        scn.load([prod_02])
        
        scn.save_dataset(prod_02, filename=kwargs.get("goes_native_color02_png"), writer='simple_image')
        
        
        ####scn_res_02 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_02 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_02.save_dataset(prod_02, filename=kwargs.get("wgs84_color02_tif"), writer='geotiff')
        scn_res_02.save_dataset(prod_02, filename=kwargs.get("wgs84_color02_png"), writer='simple_image')
        
        del scn_res_02
        scn.unload(prod_02)
        gc.collect()
        print("      Done and Cleared.")

        # --- BLOQUE INDEPENDIENTE: COLOR 03 ---
        print(f"      [Step 03/05]   Processing Color 03 (my_fdc_fn03)...", flush=True)
        prod_03 = 'my_fdc_fn03'
        scn.load([prod_03])
        
        scn.save_dataset(prod_03, filename=kwargs.get("goes_native_color03_png"), writer='simple_image')
        
        ######scn_res_03 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_03 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_03.save_dataset(prod_03, filename=kwargs.get("wgs84_color03_tif"), writer='geotiff')
        scn_res_03.save_dataset(prod_03, filename=kwargs.get("wgs84_color03_png"), writer='simple_image')
        
        del scn_res_03
        scn.unload(prod_03)
        gc.collect()
        print("      Done and Cleared.")

        # --- BLOQUE INDEPENDIENTE: COLOR 04 ---
        print(f"      [Step 04/05]   Processing Color 04 (my_fdc_fn04)...", flush=True)
        prod_04 = 'my_fdc_fn04'
        scn.load([prod_04])
        
        scn.save_dataset(prod_04, filename=kwargs.get("goes_native_color04_png"), writer='simple_image')
        
        ######scn_res_04 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_04 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_04.save_dataset(prod_04, filename=kwargs.get("wgs84_color04_tif"), writer='geotiff')
        scn_res_04.save_dataset(prod_04, filename=kwargs.get("wgs84_color04_png"), writer='simple_image')
        
        del scn_res_04
        scn.unload(prod_04)
        gc.collect()
        print("      Done and Cleared.")
        
        # --- BLOQUE INDEPENDIENTE: COLOR 05 ---
        print(f"      [Step 05/05]   Processing Color 05 (my_fdc_fn05)...", flush=True)
        prod_05 = 'my_fdc_fn05'
        scn.load([prod_05])
        
        scn.save_dataset(prod_05, filename=kwargs.get("goes_native_color05_png"), writer='simple_image')
        
        ######scn_res_05 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_05 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_05.save_dataset(prod_05, filename=kwargs.get("wgs84_color05_tif"), writer='geotiff')
        scn_res_05.save_dataset(prod_05, filename=kwargs.get("wgs84_color05_png"), writer='simple_image')
        
        del scn_res_05
        scn.unload(prod_05)
        gc.collect()
        print("      Done and Cleared.")
        
        # --- FINALIZACIN ---
        duration = round(time.time() - start_time, 2)
        print(f"\n      [Summary] Total time: {duration}s | Status: Success")
        return True

    except Exception as e:
        print(f"\n       [FNP01 ERROR] {str(e)}")
        return False
        
# =============================================================================
# 3. DIAGNOSTIC MAIN (Local testing)
# =============================================================================
if __name__ == "__main__":
    # Intentar cargar configuracin global de Satpy
    try:
        from legion_goes.satpy_config import my_config_satpy
        print(" Global Satpy Config loaded.")
    except ImportError:
        print("  Global config not found. Using defaults.")

    print("\n" + " ABI L2 FDCF: LINEAR PROCESSING ".center(80, "="))
    
    # Test paths
    working_dir = Path.cwd() 
    test_dir = working_dir / "test_one_image"
    nc_candidates = sorted(list(test_dir.glob("*FDCF*.nc")))

    if not nc_candidates:
        print(f" Error: No .nc files found in {test_dir}")
    else:
        target_nc = nc_candidates[0]
        output_base = test_dir / "test_outputs" / target_nc.stem
        output_base.mkdir(parents=True, exist_ok=True)

        print(f" INPUT : {target_nc.name}")
        print(f" OUTPUT: {output_base}")
        print("-" * 80)

        # Generate names and full paths
        dict_names = gen_dict_output_file_name(nc_path=str(target_nc))
        dict_paths = {k: str(output_base / v) for k, v in dict_names.items()}

        # Ejecucin
        success = run_proc_ABI_L2_FDCF_fnp01(nc_path=str(target_nc), **dict_paths)

        if success:
            print("-" * 80)
            print(f" PROCESS COMPLETED SUCCESSFULLY")
        else:
            print("-" * 80)
            print(f" PROCESS FAILED.")

    print("=" * 80 + "\n")
