"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f03_run_day_hour/ABI_L2_MCMIPF/day_hour_ABI_L2_MCMIPF_fnp01.py
Sentence: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_MCMIPF.day_hour_ABI_L2_MCMIPF_fnp01
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
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.gen_str_path_folder_raw_until_hour import gen_str_path_folder_raw_until_hour

from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_MCMIPF.runner_ABI_L2_MCMIPF_fnp01 import run_runner_ABI_L2_MCMIPF_fnp01

import re
from pathlib import Path


def run_day_hour_ABI_L2_MCMIPF_fnp01(position: str, year: str, day: str, hour: str):
    # 1. Obtener Satélite
    sat_id = get_sat_id_by_date(position=position, year=year, day=day)
    product_id = "ABI-L2-MCMIPF"  # Corregido a guion medio para coincidir con la carpeta
    
    # 2. Manejo de la lógica "ALL" vs Hora específica
    if hour.upper() == "ALL":
        # Genera lista ['00', '01', ..., '23']
        hours_to_process = [str(h).zfill(2) for h in range(24)]
        print(f"📅 PROCESANDO DÍA COMPLETO ({year}-{day}) - 24 Horas")
    else:
        hours_to_process = [hour.zfill(2)]

    # 3. Bucle principal de procesamiento por hora
    for h in hours_to_process:
        selected_folder_raw = gen_str_path_folder_raw_until_hour(position=position, product=product_id, year=year, day=day, hour=h)
        
        # 4. Buscar archivos .nc (usamos rglob para mayor seguridad)
        nc_candidates = sorted(list(selected_folder_raw.rglob("*MCMIPF*.nc")))
        
        if not nc_candidates:
            # Si es ALL, quizás algunas horas estén vacías, informamos y seguimos
            print(f"⚠️ Sin archivos en hora {h}: {selected_folder_raw}")
            continue

        print(f"\n--- 🕒 PROCESANDO HORA: {h} ({len(nc_candidates)} archivos) ---")
        
        # 5. Procesar cada archivo de la hora actual
        for nc_file in nc_candidates:
            print(f"🚀 Ejecutando: {nc_file.name}")
            try:
                run_runner_ABI_L2_MCMIPF_fnp01(nc_path=str(nc_file))
            except Exception as e:
                print(f"❌ Error procesando {nc_file.name}: {e}")
                continue # Que siga con el siguiente archivo aunque uno falle

# =============================================================================
# MAIN DE DIAGNÓSTICO
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP01: LSTF RUNNER (MULTI-HOUR) ".center(80, "="))
    
    try:
        # Ahora puedes pasar "ALL" y procesará las 24 carpetas
        run_day_hour_ABI_L2_MCMIPF_fnp01(
            position = "WEST", 
            year     = "2026", 
            day      = "003", 
            hour     = "ALL"
        )
        print("\n" + "="*80)
        print("✅ PROCESO GLOBAL FINALIZADO")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
    

# =============================================================================
# MAIN DE DIAGNÓSTICO
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP01: LSTF RUNNER ".center(80, "="))
    
    # Ejemplo de ejecución para un día/hora específico
    # Esto buscará automáticamente el satélite (16, 17, 18 o 19) según la fecha
    try:
        run_day_hour_ABI_L2_MCMIPF_fnp01(
            position = "WEST", 
            year     = "2026", 
            day      = "003", 
            hour     = "12"
        )
        print("-" * 80 + "\n✅ PROCESO COMPLETADO\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR EN EL RUNNER: {str(e)}")
        print("=" * 80)

    
