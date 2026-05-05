"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f02_runners/ABI_L2_MCMIPF/runner_ABI_L2_MCMIPF_fnp02.py
Sentence: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_MCMIPF.runner_ABI_L2_MCMIPF_fnp02
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
import numpy as np

# --- Satpy & Resampling ---
from satpy import Scene
from pyresample.geometry import AreaDefinition

# --- SOT LIBRARIES (Para el core de procesamiento) ---
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder

from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02 import dict_output_schema
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02 import run_proc_ABI_L2_MCMIPF_fnp02


import re
from pathlib import Path

def gen_str_folder_output(nc_path):
    # Aseguramos que nc_path sea un objeto Path y extraemos solo el nombre del archivo
    nc_file_name = Path(nc_path).name
    
    # Expresión regular para extraer:
    # 1. El producto (ej: ABI-L2-MCMIPF)
    # 2. El satélite (ej: G19)
    # 3. El timestamp 's' (Año + Día Juliano + Hora + Min + Seg)
    # Patrón: Busca lo que está entre 'OR_' y el modo '-M', el satélite y el bloque 's'
    match = re.search(r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})", nc_file_name)
    
    if not match:
        raise ValueError(f"No se pudo parsear el formato del archivo: {nc_file_name}")

    # Extraemos los datos del match
    str_prod = match.group("prod")
    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start") # Ejemplo: 2026003120023
    
    # Troceamos el timestamp de inicio (s)
    str_year = str_stimestamp[0:4]   # 2026
    str_day  = str_stimestamp[4:7]   # 003
    str_hour = str_stimestamp[7:9]   # 12
    
    str_bucket = "noaa-goes" + str_sat_number
    str_prod_fnp = str_prod + "_fnp02"
    
    # Construcción de la ruta jerárquica
    # Estructura: data_proc / sp01_single / ABI-L2-MCMIPF / 2026 / 003 / 12 / 2026003120023 / ABI-L2-MCMIPF_fnp01
    str_output_folder = (
        Path("data_proc") / 
        "sp01_single" / 
        str_bucket /
        str_prod / 
        str_year / 
        str_day / 
        str_hour / 
        str_stimestamp / 
        str_prod_fnp
    )
    
    return str_output_folder

def gen_dict_path_output(nc_path):

    # 1. Path de ejecución (Donde estás parado)
    working_dir = Path.cwd() 
    str_folder = gen_str_folder_output(nc_path)
    
    str_output_folder_path = working_dir / str_folder
    str_output_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Inyectar rutas
    dict_path_output = {k: str(str_output_folder_path / v) for k, v in dict_output_schema.items()}
    
    # Ejecutar
    return dict_path_output
    


def run_runner_ABI_L2_MCMIPF_fnp02(nc_path):
    
    # Inyectar rutas
    dict_path_output = gen_dict_path_output(nc_path=nc_path)
       
    # --- SILENCIADOR DE WARNINGS DESDE EL RUNNER ---
    # np.errstate silencia los avisos de NumPy (C-level)
    # warnings.catch_warnings silencia los avisos de Python (Satpy/Dask)
    with np.errstate(all='ignore'):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*empty slice.*")
            warnings.filterwarnings("ignore", category=UserWarning)
            
            # Ejecutar la función "caja negra"
            run_proc_ABI_L2_MCMIPF_fnp02(nc_path=nc_path, **dict_path_output)
    

# =============================================================================
# MAIN SIMPLE (Jupyter & Terminal)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP02: MCMIPF DIAGNOSTIC TEST ".center(80, "="))
    
    # 1. Path de ejecución (Donde estás parado)
    working_dir = Path.cwd() / "test_one_image"
    
    # 2. Buscar primer .nc que contenga 'MCMIPF'
    nc_candidates = sorted(list(working_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No se encontró ningún archivo .nc con 'MCMIPF' en: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        
        # Ejecutar
        run_runner_ABI_L2_MCMIPF_fnp02(nc_path=str(target_nc))
        print("-" * 80 + "\n✅ TEST FINALIZADO\n" + "=" * 80)
