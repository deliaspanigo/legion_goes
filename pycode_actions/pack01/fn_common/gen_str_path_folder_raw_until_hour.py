# legion_goes/pycode_actions/pack01/fn_common/gen_str_path_folder_raw_until_hour.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.fn_common.gen_str_path_folder_raw_until_hour
# ==================================================================================


import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path
import os

from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date

# =============================================================================
# 1. GESTION DE RUTAS (CENTRALIZADA)
# =============================================================================

def gen_str_path_folder_raw_until_hour(position: str, product: str, year: str, day: str, hour: str = None):
    """
    Generates the absolute path for raw data in the local system.
    If hour is None or "ALL", returns the day-level folder.
    """
    sat_id = get_sat_id_by_date(position=position, year=year, day=day)
    
    str_bucket = f"noaa-goes{sat_id}"
    # Definimos la base: /home/user/.../data_raw/noaa-goes19/PRODUCT/YEAR/DAY
    base_path = Path.cwd() / "data_raw" / str_bucket / product / year / day
    
    # If a specific hour is provided (and it is not the "ALL" wildcard)
    if hour and hour.upper() != "ALL":
        base_path = base_path / str(hour).zfill(2)
        
    return base_path
if __name__ == "__main__":
    # Test correcto (todos strings)
    str_folder = gen_str_path_folder_raw_until_hour(position="WEST", product = "ABI-L2-LSTF", year="2026", day="003", hour = "12")
    print(f"Test result - folder up to the hour: {str_folder}")

