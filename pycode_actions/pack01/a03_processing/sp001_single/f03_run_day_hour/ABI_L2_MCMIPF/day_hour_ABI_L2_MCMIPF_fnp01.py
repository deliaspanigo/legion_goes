"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f03_run_day_hour/ABI_L2_MCMIPF/day_hour_ABI_L2_MCMIPF_fnp01.py
Version: 0.0.2 (Simple & Robust Main)
Description: FNP01 - MCMIPF with Universal Path Detection.
Last modification: 05-05-2026 22:45
"""
# ================================================================================================================================================
#  Execution: python3 -m legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_MCMIPF.day_hour_ABI_L2_MCMIPF_fnp01
# ================================================================================================================================================

# Libraries
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
import re
from satpy import Scene
from pyresample.geometry import AreaDefinition

# Local Libraries Fixed
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.gen_str_path_folder_raw_until_hour import gen_str_path_folder_raw_until_hour

# Local Libraries Special
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_MCMIPF.runner_ABI_L2_MCMIPF_fnp01 import run_runner_ABI_L2_MCMIPF_fnp01


def run_day_hour_ABI_L2_MCMIPF_fnp01(position: str, year: str, day: str, hour: str, overwrite = False):
    """
    Orchestrates the processing of a specific hour or an entire day (ALL).
    """
    # 1. Retrieve Satellite ID
    sat_id = get_sat_id_by_date(position=position, year=year, day=day)
    product_id = "ABI-L2-MCMIPF"  # Hyphenated to match folder structure
    
    # 2. Handle "ALL" logic vs specific Hour
    if hour.upper() == "ALL":
        # Generates list ['00', '01', ..., '23']
        hours_to_process = [str(h).zfill(2) for h in range(24)]
        print(f" PROCESSING FULL DAY ({year}-{day}) - 24 Hours")
    else:
        hours_to_process = [hour.zfill(2)]

    # 3. Main processing loop per hour
    for h in hours_to_process:
        selected_folder_raw = gen_str_path_folder_raw_until_hour(
            position=position, product=product_id, year=year, day=day, hour=h
        )
        
        # 4. Search for .nc files (using rglob for safety)
        nc_candidates = sorted(list(selected_folder_raw.rglob("*MCMIPF*.nc")))
        
        if not nc_candidates:
            # If processing ALL, some hours might be empty; log and continue
            print(f" No files found for hour {h}: {selected_folder_raw}")
            continue

        print(f"\n---  PROCESSING HOUR: {h} ({len(nc_candidates)} files) ---")
        
        # 5. Process each file in the current hour
        for nc_file in nc_candidates:
            print(f" Executing: {nc_file.name}")
            try:
                run_runner_ABI_L2_MCMIPF_fnp01(nc_path=str(nc_file), overwrite = overwrite)
            except Exception as e:
                print(f" Error processing {nc_file.name}: {e}")
                continue # Continue with next file even if one fails

# =============================================================================
# DIAGNOSTIC MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP01: MCMIPF DAY-HOUR RUNNER ".center(80, "="))
    
    # Example execution: processing a specific day and hour
    # This automatically detects the satellite (16, 17, 18, or 19) based on the date
    try:
        # Toggle between "ALL" or a specific hour like "12"
        run_day_hour_ABI_L2_MCMIPF_fnp01(
            position = "EAST", 
            year     = "2026", 
            day      = "003", 
            hour     = "ALL"
        )
        print("\n" + "="*80)
        print(" GLOBAL PROCESS FINISHED")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n CRITICAL ERROR: {str(e)}")
        print("=" * 80)
