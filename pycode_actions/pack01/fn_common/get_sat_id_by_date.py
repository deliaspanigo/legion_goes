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
# CEREBRO DE SELECCIÓN DE SATÉLITE
# =============================================================================

def get_sat_id_by_date(position: str, year: str, day: str) -> str:
    """
    Determina el satélite operativo (Serie R) según fecha y posición.
    """
    pos = position.upper()
    try:
        date_query = datetime.strptime(f"{year}-{day}", "%Y-%j")
    except ValueError:
        raise ValueError(f"Fecha inválida: Año {year}, Día {day}. El día debe ser formato Juliano (001-366).")

    if pos == "EAST":
        # GOES-16 es el estándar East (75.2° W) desde finales de 2017.
        # El GOES-19 está planeado para reemplazarlo, pero el 16 sigue activo.
        return "16"
        
    elif pos == "WEST":
        # Cronología West (137.2° W):
        # GOES-17: Operativo desde Feb 2019.
        # GOES-18: Operativo desde Ene 2023 (reemplazó al 17 por fallas de enfriamiento).
        # GOES-19: Entrando en servicio/refuerzo en 2025/2026.
        if date_query >= datetime(2025, 1, 1):
            return "19"
        elif date_query >= datetime(2023, 1, 4):
            return "18"
        else:
            return "17"
    else:
        raise ValueError("La posición debe ser 'EAST' o 'WEST'.")


if __name__ == "__main__":
    # Test correcto (todos strings)
    sat_number = get_sat_id_by_date(position="WEST", year="2026", day="003")
    print(f"Resultado del Test: {sat_number}")
    # Esto lanzaría un TypeError por culpa del 2026 (int):
    # run_action02_download_files("19", "ABI-L2-LSTF", 2026, "003", "ALL")
