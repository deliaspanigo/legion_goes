# legion_goes/pycode_actions/pack01/fn_common/get_position_by_sat_id.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id
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

def get_position_by_sat_id(sat_id: str) -> str:
    s_id = str(sat_id).upper().replace("G", "")

    if s_id in ["16", "19"]:
        return "EAST"
    
    elif s_id in ["17", "18"]:
        return "WEST"
    
    else:
        raise ValueError(f"Satélite {s_id} no reconocido en la flota GOES-R.")

if __name__ == "__main__":
    # Test correcto (todos strings)
    position = get_position_by_sat_id(sat_id="19")
    print(f"Resultado del Test: {position}")
    # Esto lanzaría un TypeError por culpa del 2026 (int):
    # run_action02_download_files("19", "ABI-L2-LSTF", 2026, "003", "ALL")
