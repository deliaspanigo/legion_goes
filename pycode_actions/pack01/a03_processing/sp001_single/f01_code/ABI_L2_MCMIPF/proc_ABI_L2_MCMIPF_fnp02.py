"""
Path: legion_goes/code/python_sp/f02_processing/sp001_single/f01_product_proc/ABI_L2_MCMIPF/fnp02/fn01_python_code.py
Version: 0.0.6 (Fixed function naming & alpha-based cloud selection)
Description: Core Processing Code - MCMIPF fnp02.
Last modification: 07-05-2026 18:15
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02
# =========================================================================================================================================

import os
import sys
import time
import gc
import re
import warnings
import matplotlib
matplotlib.use('Agg') 
import numpy as np
from PIL import Image
from pathlib import Path
from satpy import Scene
from pyresample.geometry import AreaDefinition

# --- Local Libraries
from legion_goes.satpy_config.my_config_satpy import CACHE_DIR
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id

# =============================================================================
# 1. OUTPUT DEFINITION DICTIONARY
# =============================================================================

def gen_dict_output_file_name(nc_path): 
    nc_file_name = Path(nc_path).name
    match = re.search(r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})", nc_file_name)
    
    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start") 
    str_position = get_position_by_sat_id(sat_id=str_sat_number)
    
    str_name = f"SP-01-simple_G{str_sat_number}-{str_position}-s{str_stimestamp}"
    
    return {
        "png_native_ir":            f"{str_name}_CRS-Goes{str_position}_MCMIPF-fnp02-IR_Colorized.png",
        "png_native_transparent":   f"{str_name}_CRS-Goes{str_position}_MCMIPF-fnp02-IR_Colorized_Transparent.png",
        "png_native_white_clouds":  f"{str_name}_CRS-Goes{str_position}_MCMIPF-fnp02-IR-selected_clouds.png",
        "png_wgs84_ir":             f"{str_name}_CRS-WGS84_MCMIPF-fnp02-IR-Colorized.png",
        "png_wgs84_transparent":    f"{str_name}_CRS-WGS84_MCMIPF-fnp02-IR-Colorized-Transparent.png",
        "png_wgs84_white_clouds":   f"{str_name}_CRS-WGS84_MCMIPF-fnp02-IR-selected_clouds.png",
        "tif_wgs84_ir":             f"{str_name}_CRS-WGS84_MCMIPF-fnp02-IR-Colorized.tif"
    }

# =============================================================================
# 2. INTERNAL UTILITIES
# =============================================================================

def apply_grayscale_transparency(input_path, output_path, saturation_threshold=20):
    """Convierte píxeles en escala de grises a transparentes."""
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    rgb = data[:, :, :3].astype(np.int16)
    diff = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    gray_pixels = diff <= saturation_threshold
    data[gray_pixels, 3] = 0
    Image.fromarray(data).save(output_path)
    
def apply_white_clouds_vibrant(input_path, output_path):
    """
    Convierte a blanco vibrante con texturas.
    Mapea los tonos oscuros a un rango más claro para evitar grises,
    pero mantiene el degradado para el relieve.
    """
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img).astype(np.float32)
    
    # 1. Extraer luminancia (Brillo original)
    # Usamos los pesos perceptuales para mayor fidelidad
    luminance = (data[:, :, 0] * 0.299 + 
                 data[:, :, 1] * 0.587 + 
                 data[:, :, 2] * 0.114)
    
    # 2. Máscara de visibilidad
    visible_pixels = data[:, :, 3] > 0
    
    # 3. REMAPEO DINÁMICO FIJO (Para evitar el gris)
    # Queremos que incluso lo que antes era "gris" ahora sea un "blanco suave".
    # Aplicamos un aumento de exposición y un desplazamiento (offset).
    # Ajusta el offset (50-100) si quieres que las partes oscuras sean aún más blancas.
    offset = 60 
    scale = 1.2
    
    vibrant_white = (luminance * scale) + offset
    
    # Capamos a 255 para que el blanco puro sea el límite
    vibrant_white = np.clip(vibrant_white, 0, 255)
    
    # 4. Asignar a los tres canales para que el color sea Blanco/Blanco-Hueso
    for i in range(3):
        data[visible_pixels, i] = vibrant_white[visible_pixels]
    
    # Guardar manteniendo el Alfa (transparencia) intacto
    final_img = data.astype(np.uint8)
    Image.fromarray(final_img).save(output_path)

# =============================================================================
# 3. PROCESSING FUNCTION
# =============================================================================

def run_proc_ABI_L2_MCMIPF_fnp02(nc_path, **kwargs):
    start_time = time.time()
    file_path = Path(nc_path)
    my_chunks = {'y': 1024, 'x': 1024}
    
    resample_kwargs = {
        'cache_dir': str(CACHE_DIR),
        'nprocs': 4,
        'static_data': True
    }
    
    try:
        # 0. Folder Setup
        out_folder = Path(list(kwargs.values())[0]).parent
        out_folder.mkdir(parents=True, exist_ok=True)
        print(f"Target folder: {out_folder}")

        # --- NATIVE PROCESSING ---
        print(f"      [Step 01/10] 🛰️  Loading IR Product...", end=" ", flush=True)
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc', reader_kwargs={'chunks': my_chunks})
        product_id = 'colorized_ir_clouds'
        scn.load([product_id])
        print("Done.")

        print(f"      [Step 02/10] 🖼️  Saving Native IR...", end=" ", flush=True)
        native_path = kwargs.get("png_native_ir")
        scn.save_datasets(writer='simple_image', datasets=[product_id], filename=str(native_path))
        print("Done.")

        print(f"      [Step 03/10] 🎭  Applying Transparency (Native)...", end=" ", flush=True)
        native_transp = kwargs.get("png_native_transparent")
        apply_grayscale_transparency(native_path, native_transp)
        print("Done.")

        print(f"      [Step 04/10] ☁️  Generating White Clouds (Native)...", end=" ", flush=True)
        # Aquí usamos la función que pediste basada en el Alfa del paso anterior
        apply_white_clouds_vibrant(native_transp, kwargs.get("png_native_white_clouds"))
        print("Done.")

        # --- REPROJECTION ---
        print(f"      [Step 05/10] 🗺️  Defining WGS84 Area...", end=" ", flush=True)
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        print("Done.")
        
        print(f"      [Step 06/10] 🔄  Resampling to WGS84...", end=" ", flush=True)
        scn_res = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        print("Done.")

        # --- WGS84 OUTPUTS ---
        print(f"      [Step 07/10] 💾  Saving WGS84 Files (PNG/TIF)...", end=" ", flush=True)
        wgs84_png = kwargs.get("png_wgs84_ir")
        scn_res.save_datasets(writer='simple_image', datasets=[product_id], filename=str(wgs84_png))
        scn_res.save_datasets(writer='geotiff', datasets=[product_id], filename=str(kwargs.get("tif_wgs84_ir")))
        print("Done.")

        print(f"      [Step 08/10] 🎭  Applying Transparency (WGS84)...", end=" ", flush=True)
        wgs84_transp = kwargs.get("png_wgs84_transparent")
        apply_grayscale_transparency(wgs84_png, wgs84_transp)
        print("Done.")

        print(f"      [Step 09/10] ☁️  Generating White Clouds (WGS84)...", end=" ", flush=True)
        apply_white_clouds_vibrant(wgs84_transp, kwargs.get("png_wgs84_white_clouds"))
        print("Done.")

        # --- FINISH ---
        duration = round(time.time() - start_time, 2)
        print(f"      [Step 10/10] 📸  Finalizing... Total time: {duration}s")
        
        del scn
        if 'scn_res' in locals(): del scn_res
        gc.collect()
        return True

    except Exception as e:
        print(f"\n      ❌ [FNP02 ERROR] {str(e)}")
        return False

# =============================================================================
# DIAGNOSTIC MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP02: IN-SITU DIAGNOSTIC TEST ".center(80, "="))
    
    current_dir = Path.cwd() / "test_one_image"
    nc_candidates = sorted(list(current_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No .nc files found in {current_dir}")
    else:
        target_nc = nc_candidates[0]
        test_out = current_dir / "test_outputs" / target_nc.stem
        test_out.mkdir(parents=True, exist_ok=True)

        print(f"🎯 TARGET: {target_nc.name}")
        output_paths = {k: str(test_out / v) for k, v in gen_dict_output_file_name(str(target_nc)).items()}

        if run_proc_ABI_L2_MCMIPF_fnp02(str(target_nc), **output_paths):
            print("-" * 80 + f"\n✅ SUCCESS. Results in: {test_out}")
        else:
            print("-" * 80 + f"\n❌ FAILED.")
    print("=" * 80 + "\n")
