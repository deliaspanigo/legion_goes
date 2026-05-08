# ==================================================================================
# legion_goes/pycode_actions/pack01/zzz_run_pack01_02_processing.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_02_processing
# ==================================================================================

import os
import traceback
# Importaciones ABSOLUTAS (más seguras)
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_LSTF.day_hour_ABI_L2_LSTF_fnp01     import run_day_hour_ABI_L2_LSTF_fnp01
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_MCMIPF.day_hour_ABI_L2_MCMIPF_fnp01 import run_day_hour_ABI_L2_MCMIPF_fnp01
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_MCMIPF.day_hour_ABI_L2_MCMIPF_fnp02 import run_day_hour_ABI_L2_MCMIPF_fnp02
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_FDCF.day_hour_ABI_L2_FDCF_fnp01     import run_day_hour_ABI_L2_FDCF_fnp01
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.GLM_L2_LCFA.day_hour_GLM_L2_LCFA_fnp01     import run_day_hour_GLM_L2_LCFA_fnp01

def run_pack01_02_processing(position: str, year: str, day: str, hour: str):
    """
    Ejecuta el flujo de procesamiento del Pack 01:
    - Procesa LSTF (Land Surface Temperature)
    - Procesa MCMIPF (True Color / Reflectancias) con FNP01 y FNP02
    """
    
    print(f"--- Iniciando Procesamiento: LSTF (FNP01) ---")
    run_day_hour_ABI_L2_LSTF_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)

    print(f"--- Iniciando Procesamiento: MCMIPF (FNP01) ---")
    run_day_hour_ABI_L2_MCMIPF_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)
    
    print(f"--- Iniciando Procesamiento: MCMIPF (FNP02) ---")
    run_day_hour_ABI_L2_MCMIPF_fnp02(position=position, year=year, day=day, hour=hour, overwrite=False)
    
    print(f"--- Iniciando Procesamiento: FDCF (FNP01) ---")
    run_day_hour_ABI_L2_FDCF_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)
    
    print(f"--- Iniciando Procesamiento: GLM_L2_LCFA (FNP01) ---")
    run_day_hour_GLM_L2_LCFA_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)
# ===================================================================
# MAIN EXECUTION (Vínculo con fabricar.sh)
# ===================================================================
if __name__ == "__main__":
    print("\n" + "=== LEGION GOES - PACK 01: PROCESSING PROCESS ===".center(80, "="))
    
    # Captura de variables de entorno (las mismas que el script de descarga)
    ENV_POS  = os.getenv("POS", "WEST")
    ENV_YEAR = os.getenv("YEAR", "2026")
    ENV_DAY  = os.getenv("DAY", "003")
    ENV_HOUR = os.getenv("HOUR", "ALL")

    print(f"📍 Posición: {ENV_POS}")
    print(f"📅 Fecha:    {ENV_YEAR}-{ENV_DAY}")
    print(f"🕒 Hora:     {ENV_HOUR}")
    print("-" * 80)

    try:
        # IMPORTANTE: Llamamos a la función de PROCESAMIENTO
        run_pack01_02_processing(
            position = ENV_POS, 
            year     = ENV_YEAR, 
            day      = ENV_DAY, 
            hour     = ENV_HOUR
        )
        
        print("\n" + "=== PROCESO DE PROCESAMIENTO COMPLETADO ===".center(80, "="))
        print(f"Carpeta de trabajo: {os.getcwd()}")

    except Exception as e:
        print("\n" + "=== ERROR CRÍTICO EN PROCESAMIENTO ===".center(80, "="))
        print(f"Ocurrió un error: {e}")
        traceback.print_exc()
        
    print("=" * 80 + "\n")
