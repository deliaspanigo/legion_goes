# legion_goes/pycode_actions/pack01/a02_download_files/action01_init.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.a02_download_files.action02_download_files
# ==================================================================================

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path


import os  # <-- No te olvides de importar os, que lo usas en el print final
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date

from legion_goes.pycode_actions.pack01.a02_download_files.fn01_download_goes_files import download_goes_files
#from .step02_create_folder_structure import run_action as action02_create_folder_structure

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path
from datetime import datetime

# =============================================================================
# CEREBRO DE SELECCIÓN DE SATÉLITE
# =============================================================================


# =============================================================================
# MOTOR DE DESCARGA S3
# =============================================================================

def run_action02_download_files(position: str, product: str, year: str, day: str, hour: str):
    """
    Descarga archivos de GOES. 
    REQUISITO: Todos los argumentos deben ser strings.
    """
    # 1. Validación de tipos (Asegura que todos sean strings)
    args = {"position": position, "product": product, "year": year, "day": day, "hour": hour}
    for name, value in args.items():
        if not isinstance(value, str):
            raise TypeError(f"El argumento '{name}' debe ser string, se recibió {type(value).__name__}")

    # Sat
    selected_sat = get_sat_id_by_date(position = position, year = year, day = day)
    
    # Download action
    download_goes_files(position = position, product = product, year = year, day = day, hour = hour)

if __name__ == "__main__":
    # Test correcto (todos strings)
    run_action02_download_files(position="WEST", product="ABI-L2-LSTF", year="2026", day="003", hour="12")
    
    # Esto lanzaría un TypeError por culpa del 2026 (int):
    # run_action02_download_files("WEST", "ABI-L2-LSTF", 2026, "003", "ALL")
