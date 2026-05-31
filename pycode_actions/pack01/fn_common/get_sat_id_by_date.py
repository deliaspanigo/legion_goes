# legion_goes/pycode_actions/pack01/fn_common/get_sat_id_by_date.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date
# ==================================================================================

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path


import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path
from datetime import datetime

# =============================================================================
# CEREBRO DE SELECCION DE SATELITE
# =============================================================================

def get_sat_id_by_date(position: str, year: str, day: str) -> str:
    pos = position.upper()
    date_query = datetime.strptime(f"{year}-{day}", "%Y-%j")

    if pos == "EAST":
        # A partir de 2025, el 19 reemplaza al 16 en el este
        if date_query >= datetime(2025, 2, 1): # Fecha estimada de fin de pruebas
            return "19"
        else:
            return "16"
        
    elif pos == "WEST":
        # El 18 es el actual titular del oeste. 
        # El 17 ya quedo como reserva/backup.
        if date_query >= datetime(2023, 1, 1):
            return "18"
        else:
            return "17"


if __name__ == "__main__":
    # Test correcto (todos strings)
    sat_number = get_sat_id_by_date(position="EAST", year="2026", day="003")
    print(f"Resultado del Test: {sat_number}")
    # Esto lanzaria un TypeError por culpa del 2026 (int):
    # run_action02_download_files("19", "ABI-L2-LSTF", 2026, "003", "ALL")
