# ==================================================================================
# legion_goes/pycode_actions/pack01/zzz_run_pack01_02_processing.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_02_processing
# ==================================================================================

import os
import traceback
# Importaciones ABSOLUTAS (mas seguras)
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_LSTF.day_hour_ABI_L2_LSTF_fnp01     import run_day_hour_ABI_L2_LSTF_fnp01
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_MCMIPF.day_hour_ABI_L2_MCMIPF_fnp01 import run_day_hour_ABI_L2_MCMIPF_fnp01
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_MCMIPF.day_hour_ABI_L2_MCMIPF_fnp02 import run_day_hour_ABI_L2_MCMIPF_fnp02
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_FDCF.day_hour_ABI_L2_FDCF_fnp01     import run_day_hour_ABI_L2_FDCF_fnp01
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.GLM_L2_LCFA.day_hour_GLM_L2_LCFA_fnp01     import run_day_hour_GLM_L2_LCFA_fnp01

def run_pack01_02_processing(position: str, year: str, day: str, hour: str):
    """
    Runs the Pack 01 processing workflow:
    - Processes LSTF (Land Surface Temperature)
    - Processes MCMIPF (True Color / Reflectances) with FNP01 and FNP02
    """
    
    print(f"--- Starting Processing: LSTF (FNP01) ---")
    run_day_hour_ABI_L2_LSTF_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)

    print(f"--- Starting Processing: MCMIPF (FNP01) ---")
    run_day_hour_ABI_L2_MCMIPF_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)
    
    print(f"--- Starting Processing: MCMIPF (FNP02) ---")
    run_day_hour_ABI_L2_MCMIPF_fnp02(position=position, year=year, day=day, hour=hour, overwrite=False)
    
    print(f"--- Starting Processing: FDCF (FNP01) ---")
    run_day_hour_ABI_L2_FDCF_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)
    
    print(f"--- Starting Processing: GLM_L2_LCFA (FNP01) ---")
    run_day_hour_GLM_L2_LCFA_fnp01(position=position, year=year, day=day, hour=hour, overwrite=False)
# ===================================================================
# MAIN EXECUTION (Vinculo con fabricar.sh)
# ===================================================================
if __name__ == "__main__":
    print("\n" + "=== LEGION GOES - PACK 01: PROCESSING PROCESS ===".center(80, "="))
    
    # Environment variable capture (the same ones used by the download script)
    ENV_POS  = os.getenv("POS", "WEST")
    ENV_YEAR = os.getenv("YEAR", "2026")
    ENV_DAY  = os.getenv("DAY", "003")
    ENV_HOUR = os.getenv("HOUR", "ALL")

    print(f" Posicion: {ENV_POS}")
    print(f" Fecha:    {ENV_YEAR}-{ENV_DAY}")
    print(f" Hora:     {ENV_HOUR}")
    print("-" * 80)

    try:
        # IMPORTANT: call the processing function
        run_pack01_02_processing(
            position = ENV_POS, 
            year     = ENV_YEAR, 
            day      = ENV_DAY, 
            hour     = ENV_HOUR
        )
        
        print("\n" + "=== PROCESO DE PROCESAMIENTO COMPLETADO ===".center(80, "="))
        print(f"Carpeta de trabajo: {os.getcwd()}")

    except Exception as e:
        print("\n" + "=== ERROR CRITICO EN PROCESAMIENTO ===".center(80, "="))
        print(f"An error occurred: {e}")
        traceback.print_exc()
        
    print("=" * 80 + "\n")
