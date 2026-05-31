# legion_goes/pycode_actions/pack01/zzz_run_pack01_01_download.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_01_download
# ==================================================================================

import os
import traceback
# Importaciones ABSOLUTAS (mas seguras)
from legion_goes.pycode_actions.pack01.a01_init.action01_init import run_action01_init
from legion_goes.pycode_actions.pack01.a02_download_files.action02_download_files import run_action02_download_files

def run_pack01_01_download(position: str, year: str, day: str, hour: str):
    """
    Runs the complete Pack 01 workflow:
    - Folder initialization and welcome step (Task 01)
    - Automated file download by date and position (Task 02)
    """
    # 1. Initialization
    run_action01_init(verbose=True)
    
    # 2. Download of specific products
    # Nota: Make sure the IDs match the folders (hyphen/underscore)
    products = ["ABI-L2-LSTF", "ABI-L2-MCMIPF", "ABI-L2-FDCF", "GLM-L2-LCFA"]
    
    for prod in products:
        print(f"--- Starting download for: {prod} ---")
        run_action02_download_files(
            position=position, 
            product=prod, 
            year=year, 
            day=day, 
            hour=hour
        )

# ===================================================================
# MAIN EXECUTION (Panel de Control dinamico)
# ===================================================================
if __name__ == "__main__":
    print("\n" + "=== LEGION GOES - PACK 01: FULL PROCESS ===".center(80, "="))
    
    # 1. CAPTURA DE PARAMETROS DEL SISTEMA (Configurados en el .sh)
    # os.getenv("NOMBRE", "VALOR_POR_DEFECTO")
    ENV_POS  = os.getenv("POS", "WEST")
    ENV_YEAR = os.getenv("YEAR", "2026")
    ENV_DAY  = os.getenv("DAY", "003")
    ENV_HOUR = os.getenv("HOUR", "ALL")

    # Show what will be processed for visual confirmation
    print(f" Posicion: {ENV_POS}")
    print(f" Fecha:    {ENV_YEAR}-{ENV_DAY}")
    print(f" Hora:     {ENV_HOUR}")
    print("-" * 80)

    try:
        # 2. EJECUCION USANDO LAS VARIABLES CAPTURADAS
        run_pack01_01_download(
            position = ENV_POS, 
            year     = ENV_YEAR, 
            day      = ENV_DAY, 
            hour     = ENV_HOUR
        )
        
        print("\n" + "=== PROCESO FINALIZADO EXITOSAMENTE ===".center(80, "="))
        print(f"Carpeta de trabajo: {os.getcwd()}")

    except Exception as e:
        print("\n" + "=== ERROR CRITICO EN PACK 01 ===".center(80, "="))
        print(f"An error occurred: {e}")
        traceback.print_exc()
        
    print("=" * 80 + "\n")
