"""
Path: legion_goes/code/python_sp/f02_processing/sp001_single/f01_product_proc/ABI_L2_MCMIPF/fnp02/fn01_python_code.py
Version: 0.0.4 (Consolidated steps)
Description: Core Processing Code - MCMIPF fnp02.
Last modification: 05-05-2026 22:40
"""

# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02
# =========================================================================================================================================

# Libraries
import os
import sys
import time
import gc
import json
import warnings
import logging
import matplotlib
matplotlib.use('Agg') # Backend for servers
import numpy as np
from PIL import Image
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from satpy import Scene
from pyresample.geometry import AreaDefinition


# =============================================================================
# 1. OUTPUT DEFINITION DICTIONARY
# =============================================================================
dict_output_schema = {
    "png_CRSnative_ir": "CRS-GoesEast_IR_Colorized.png",
    "png_CRSnative_ir_transparent": "CRS-GoesEast_IR_Colorized_Transparent.png",
    "png_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.png",
    "png_CRSwgs84_ir_transparent": "CRS-WGS84_IR_Colorized_Transparent.png",
    "tif_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.tif"
}

# =============================================================================
# 2. INTERNAL UTILITIES
# =============================================================================

def apply_grayscale_transparency(input_path, output_path, saturation_threshold=20):
    """Converts grayscale pixels (clouds/background) to transparent for overlays."""
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    rgb = data[:, :, :3].astype(np.int16)
    
    # Calculate saturation to identify gray levels
    diff = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    gray_pixels = diff <= saturation_threshold
    
    # Set alpha channel to 0 for gray pixels
    data[gray_pixels, 3] = 0
    Image.fromarray(data).save(output_path)

# =============================================================================
# 3. PROCESSING FUNCTION
# =============================================================================

def run_proc_ABI_L2_MCMIPF_fnp02(nc_path, **kwargs):
    """
    Executes the FNP02 pipeline for Colorized IR.
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
        print(f"      [Step 01/09] 🛰️   Loading IR Product...", end=" ", flush=True)
        scn = Scene(filenames=[str(nc_path)], reader='abi_l2_nc')
        product_id = 'colorized_ir_clouds'
        scn.load([product_id])
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 02/09] 🖼️   Saving Native IR...", end=" ", flush=True)
        native_ir_path = kwargs.get("png_CRSnative_ir")
        scn.save_datasets(writer='simple_image', datasets=[product_id], filename=str(native_ir_path))
        print("Done.")
        
        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 03/09] 🖼️   Grey to Transparent (Native)...", end=" ", flush=True)
        apply_grayscale_transparency(native_ir_path, kwargs.get("png_CRSnative_ir_transparent"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 04/09] 🗺️   Defining WGS84 Area...", end=" ", flush=True)
        area_def = AreaDefinition(
            'wgs84', 'LatLon', 'wgs84',
            {'proj': 'eqc', 'units': 'm', 'ellps': 'WGS84'},
            3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )
        print("Done.")
        
        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 05/09] 🔄  Resampling Scene to WGS84...", end=" ", flush=True)
        scn_res = scn.resample(area_def)
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 06/09] 💾  Saving WGS84 PNG and GeoTIFF...", end=" ", flush=True)
        wgs84_png_path = kwargs.get("png_CRSwgs84_ir")
        scn_res.save_datasets(writer='simple_image', datasets=[product_id], filename=str(wgs84_png_path))
        scn_res.save_datasets(writer='geotiff', datasets=[product_id], filename=str(kwargs.get("tif_CRSwgs84_ir")))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 07/09] 🎭  Grey to Transparent (WGS84)...", end=" ", flush=True)
        apply_grayscale_transparency(wgs84_png_path, kwargs.get("png_CRSwgs84_ir_transparent"))
        print("Done.")

        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 08/09] ⏱️   Timing...", end=" ", flush=True)
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        print("Done.")
        
        # -----------------------------------------------------------------------------------------------------------------
        print(f"      [Step 09/09] 📸  End...")
        print(f"        [Summary] Total time: {duration}s")
        print(f"        [Status] Process finished successfully.")
        
        # -----------------------------------------------------------------------------------------------------------------
        # Explicit memory cleanup
        del scn
        if 'scn_res' in locals(): del scn_res
        gc.collect()
        
        return True

    except Exception as e:
        print(f"\n      ❌ [FNP02 ERROR] {str(e)}")
        return False

# =============================================================================
# DIAGNOSTIC MAIN (Local testing only)
# =============================================================================
if __name__ == "__main__":
    try:
        from legion_goes.satpy_config import my_config_satpy
        print("✅ Global Satpy Config loaded.")
    except ImportError:
        print("⚠️  Global config not found. Running with Satpy defaults.")

    print("\n" + " CODE MCMIPF FNP02: IN-SITU DIAGNOSTIC TEST ".center(80, "="))
    
    working_dir = Path.cwd() 
    current_dir = working_dir / "test_one_image"
    nc_candidates = sorted(list(current_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No .nc files found in {current_dir}")
    else:
        target_nc = nc_candidates[0]
        test_output_base = current_dir / "test_outputs" / target_nc.stem
        test_output_base.mkdir(parents=True, exist_ok=True)

        test_paths = {k: str(test_output_base / v) for k, v in dict_output_schema.items()}

        print(f"🎯 Target NC file: {target_nc.name}")
        print("-" * 80)

        success = run_proc_ABI_L2_MCMIPF_fnp02(nc_path=str(target_nc), **test_paths)

        if success:
            print("-" * 80)
            print(f"✅ TEST FINISHED SUCCESSFULLY")
            print(f"📸 Results available at: {test_output_base}")
        else:
            print("-" * 80)
            print(f"❌ TEST FAILED. Check error messages above.")

    print("=" * 80 + "\n")
