"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_MCMIPF/proc_ABI_L2_MCMIPF_fnp01.py
Sentence: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01
Version: 1.8.9 (Simple & Robust Main)
Description: FNP01 - Land Surface Temperature with Universal Path Detection.
"""

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
import numpy as np # Asegúrate de tener este import arriba

# --- UTILIDAD PARA SILENCIAR STDERR ---


@contextmanager
def silence_stderr():
    """Silencia stderr, mensajes de HDF5 y RuntimeWarnings de NumPy/Python."""
    # 1. Silenciamos Warnings de Python y NumPy
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning) # Bloquea el 'Mean of empty slice'
        warnings.simplefilter("ignore")
        
        # 2. Silenciamos el stderr a nivel de sistema (C/C++ libs)
        new_target = open(os.devnull, "w")
        old_target = sys.stderr
        sys.stderr = new_target
        try:
            yield new_target
        finally:
            sys.stderr = old_target
            new_target.close()

# Desactivar logs de Python también por si acaso
logging.getLogger('satpy').setLevel(logging.ERROR)
logging.getLogger('pyresample').setLevel(logging.ERROR)

# =============================================================================
# 1. DICCIONARIO DE DEFINICIÓN DE SALIDAS
# =============================================================================
dict_output_schema = {
    "png_CRSnative_true_color": "CRS-GoesEast_TrueColor.png",
    "png_CRSnative_true_color_day_only": "CRS-GoesEast_TrueColor_DayOnly.png",
    "png_CRSwgs84_true_color": "CRS-WGS84_TrueColor.png",
    "png_CRSwgs84_true_color_day_only": "CRS-WGS84_TrueColor_DayOnly.png",
    "tif_CRSwgs84_true_color": "CRS-WGS84_TrueColor.tif",
    "json_meta": "meta.json",
    "gallery": "gallery.png"
}

# =============================================================================
# 2. FUNCIÓN DE MÁSCARA DE PÍXELES NEGROS
# =============================================================================
def apply_dark_pixel_mask(data_array, threshold=0.05):
    avg_intensity = data_array.mean(dim='bands')
    return data_array.where(avg_intensity > threshold)


# =============================================================================
# 4. FUNCIÓN DE PROCESAMIENTO
# =============================================================================


def run_proc_ABI_L2_MCMIPF_fnp01(nc_path, **kwargs):
    """
    Executes the Full Network Processing (FNP) pipeline.
    Steps include loading, masking, reprojecting, and metadata generation.
    """
    start_time = time.time()
    
    try:
        # Create output directory if it doesn't exist
        Path(kwargs.get("png_CRSnative_true_color")).parent.mkdir(parents=True, exist_ok=True)

        # --- STEP 1: LOAD ABI BANDS ---
        # Initializing the Scene and loading the True Color composite
        print(f"\n      [Step 01/10] 🛰️  Loading ABI bands...", end=" ", flush=True)
        with silence_stderr(), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            scn = Scene(filenames=[nc_path], reader='abi_l2_nc')
            scn.load(['true_color'])
        print("Done.")

        # --- STEP 2: SAVE NATIVE TRUE COLOR ---
        # Exporting the image in the original satellite projection
        print(f"      [Step 02/10] 🖼️  Saving Native True Color PNG...", end=" ", flush=True)
        scn.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSnative_true_color"))
        print("Done.")

        # --- STEP 3: CREATE DAY-ONLY MASK (NATIVE) ---
        # Applying luminance threshold to filter out night pixels
        print(f"      [Step 03/10] 🎭  Applying Dark Pixel Mask...", end=" ", flush=True)
        scn_day = scn.copy()
        scn_day['true_color'] = apply_dark_pixel_mask(scn_day['true_color'], threshold=0.05)
        print("Done.")

        # --- STEP 4: SAVE NATIVE DAY-ONLY ---
        # Exporting the masked image in native projection
        print(f"      [Step 04/10] ☀️  Saving Native Day-Only PNG...", end=" ", flush=True)
        scn_day.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSnative_true_color_day_only"))
        print("Done.")

        # --- STEP 5: DEFINE WGS84 AREA ---
        # Setting up the target geographic projection (Equirectangular)
        print(f"      [Step 05/10] 🗺️  Defining WGS84 Area Definition...", end=" ", flush=True)
        area_def = AreaDefinition(
            'wgs84', 'LatLon', 'wgs84',
            {'proj': 'eqc', 'units': 'm', 'ellps': 'WGS84'},
            3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )
        print("Done.")

        # --- STEP 6: RESAMPLE TO WGS84 ---
        # Projecting the full scene to LatLon coordinate system
        print(f"      [Step 06/10] 🔄  Resampling Scene to WGS84...", end=" ", flush=True)
        scn_res = scn.resample(area_def)
        print("Done.")

        # --- STEP 7: SAVE WGS84 OUTPUTS ---
        # Exporting both PNG and GeoTIFF for GIS compatibility
        print(f"      [Step 07/10] 💾  Saving WGS84 PNG and GeoTIFF...", end=" ", flush=True)
        scn_res.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSwgs84_true_color"))
        scn_res.save_datasets(writer='geotiff', datasets=['true_color'], filename=kwargs.get("tif_CRSwgs84_true_color"))
        print("Done.")

        # --- STEP 8: RESAMPLE & SAVE WGS84 DAY-ONLY ---
        # Projecting and saving the masked version in WGS84
        print(f"      [Step 08/10] 💾  Saving WGS84 Day-Only PNG...", end=" ", flush=True)
        scn_res_day = scn_day.resample(area_def)
        scn_res_day.save_datasets(writer='simple_image', datasets=['true_color'], filename=kwargs.get("png_CRSwgs84_true_color_day_only"))
        print("Done.")

        # --- STEP 9: METADATA ---
        # Saving process info
        print(f"      [Step 09/10] 📝  Generating Metadata...", end=" ", flush=True)
        duration = round(time.time() - start_time, 2)
        if kwargs.get("json_meta"):
            with open(kwargs.get("json_meta"), 'w') as f:
                json.dump({
                    "input_file": Path(nc_path).name, 
                    "duration_sec": duration,
                    "timestamp": datetime.now().isoformat(), 
                    "method": "luminance_mask_v1.7.0"
                }, f, indent=4)
        print("Done.") # <--- Añadido para cerrar la línea del Step 09

        # --- STEP 10: CLEANUP ---
        # Memory management: remove heavy objects from RAM
        print(f"      [Step 10/10] 🧹  Final Memory Cleanup...", end=" ", flush=True)
        del scn; del scn_res; del scn_day; del scn_res_day; gc.collect()
        print(f"Done.")
        print(f"Total time: {duration}s")
        return True

    except Exception as e:
        print(f"\n      ❌ [FNP01 ERROR] {str(e)}")
        return False




# =============================================================================
# MAIN DE DIAGNÓSTICO (Solo para testeo local)
# =============================================================================
if __name__ == "__main__":
    # --- INYECCIÓN DE CONTEXTO ---
    try:
        # Intentamos cargar tu config global para que el test use el CACHE
        from legion_goes.satpy_config import my_config_satpy
        print("✅ Global Satpy Config loaded for diagnostic test.")
    except ImportError:
        print("⚠️  Global config not found in path. Running with Satpy defaults.")

    print("\n" + " FNP01: IN-SITU DIAGNOSTIC TEST ".center(80, "="))
    # 1. Path de ejecución (Donde estás parado)
    working_dir = Path.cwd() 
    current_dir = working_dir / "test_one_image"
    nc_candidates = sorted(list(current_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No se encontró ningún archivo .nc en {current_dir}")
        print("💡 Coloca un archivo NetCDF de GOES en esta carpeta para probar.")
    else:
        target_nc = nc_candidates[0]
        
        # 2. Configurar Directorio de Salida
        # Usamos el nombre del NC para crear una subcarpeta de test
        test_output_base = current_dir / "test_outputs" / target_nc.stem
        test_output_base.mkdir(parents=True, exist_ok=True)

        # 3. Construir el Diccionario de Rutas Reales (Simulando al Executor)
        # Aquí es donde el 'kwargs' recibe las rutas finales
        test_paths = {
            k: str(test_output_base / v) 
            for k, v in dict_output_schema.items()
        }

        print(f"🎯 Archivo NC  : {target_nc.name}")
        print(f"📂 Salida Test : {test_output_base}")
        print("-" * 80)

        # 4. Ejecutar el Core con el "Splat Operator" (**)
        success = run_proc_ABI_L2_MCMIPF_fnp01(
            nc_path=str(target_nc),
            **test_paths
        )

        if success:
            print("-" * 80)
            print(f"✅ TEST FINALIZADO CON ÉXITO")
            print(f"📸 Revisa los resultados en: {test_output_base}")
        else:
            print("-" * 80)
            print(f"❌ EL TEST HA FALLADO. Revisa los mensajes de error arriba.")

    print("=" * 80 + "\n")
