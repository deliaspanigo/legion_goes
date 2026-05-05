# legion_goes/pycode_actions/pack01/zzz_run_pack01_01_download.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_01_download
# ==================================================================================

import os
import traceback
# Importaciones ABSOLUTAS (más seguras)
from legion_goes.pycode_actions.pack01.a01_init.action01_init import run_action01_init
from legion_goes.pycode_actions.pack01.a02_download_files.action02_download_files import run_action02_download_files

def run_pack01_01_download(position: str, year: str, day: str, hour: str):
    """
    Ejecuta el flujo completo del Pack 01:
    - Inicialización de carpetas y bienvenida (Task 01)
    - Descarga automatizada de archivos según fecha y posición (Task 02)
    """
    # 1. Inicialización
    run_action01_init(verbose=True)
    
    # 2. Descarga de productos específicos
    # Nota: Asegúrate de que los IDs coincidan con las carpetas (guion medio/bajo)
    products = ["ABI-L2-LSTF", "ABI-L2-MCMIPF", "ABI-L2-FDCF", "GLM-L2-LCFA"]
    
    for prod in products:
        print(f"--- Iniciando descarga de: {prod} ---")
        run_action02_download_files(
            position=position, 
            product=prod, 
            year=year, 
            day=day, 
            hour=hour
        )

# ===================================================================
# MAIN EXECUTION (Panel de Control dinámico)
# ===================================================================
if __name__ == "__main__":
    print("\n" + "=== LEGION GOES - PACK 01: FULL PROCESS ===".center(80, "="))
    
    # 1. CAPTURA DE PARÁMETROS DEL SISTEMA (Configurados en el .sh)
    # os.getenv("NOMBRE", "VALOR_POR_DEFECTO")
    ENV_POS  = os.getenv("POS", "WEST")
    ENV_YEAR = os.getenv("YEAR", "2026")
    ENV_DAY  = os.getenv("DAY", "003")
    ENV_HOUR = os.getenv("HOUR", "ALL")

    # Mostrar qué estamos por procesar para confirmación visual
    print(f"📍 Posición: {ENV_POS}")
    print(f"📅 Fecha:    {ENV_YEAR}-{ENV_DAY}")
    print(f"🕒 Hora:     {ENV_HOUR}")
    print("-" * 80)

    try:
        # 2. EJECUCIÓN USANDO LAS VARIABLES CAPTURADAS
        run_pack01_01_download(
            position = ENV_POS, 
            year     = ENV_YEAR, 
            day      = ENV_DAY, 
            hour     = ENV_HOUR
        )
        
        print("\n" + "=== PROCESO FINALIZADO EXITOSAMENTE ===".center(80, "="))
        print(f"Carpeta de trabajo: {os.getcwd()}")

    except Exception as e:
        print("\n" + "=== ERROR CRÍTICO EN PACK 01 ===".center(80, "="))
        print(f"Ocurrió un error: {e}")
        traceback.print_exc()
        
    print("=" * 80 + "\n")
