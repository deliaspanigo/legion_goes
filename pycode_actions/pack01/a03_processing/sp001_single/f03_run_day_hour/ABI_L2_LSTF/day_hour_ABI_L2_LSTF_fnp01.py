"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f03_run_day_hour/ABI_L2_LSTF/day_hour_ABI_L2_LSTF_fnp01.py
Version: 0.0.2 (Simple & Robust Main)
Description: Run Day-Hour - FNP01 - Land Surface Temperature with Universal Path Detection.
Last modification: 05-05-2026 18:18
"""
# ================================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_run_day_hour.ABI_L2_LSTF.day_hour_ABI_L2_LSTF_fnp01
# ================================================================================================================================================

# Libraries
import os
import sys
import time
import gc
import json
import warnings
import logging
import re
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from satpy import Scene
from pyresample.geometry import AreaDefinition

# Local Libraries Fixed
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.gen_str_path_folder_raw_until_hour import gen_str_path_folder_raw_until_hour

# Local Libraries Special
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_LSTF.runner_ABI_L2_LSTF_fnp01 import run_runner_ABI_L2_LSTF_fnp01

def run_day_hour_ABI_L2_LSTF_fnp01(position: str, year: str, day: str, hour: str):
    """
    Processes all LSTF files for a specific day/hour or an entire day.
    """
    # 1. Identify Satellite and Product
    sat_id = get_sat_id_by_date(position=position, year=year, day=day)
    product_id = "ABI-L2-LSTF" 
    
    # 2. Logic for "ALL" vs Specific Hour
    if hour.upper() == "ALL":
        # Generates list ['00', '01', ..., '23']
        hours_to_process = [str(h).zfill(2) for h in range(24)]
        print(f"📅 PROCESSING FULL DAY ({year}-{day}) - 24 Hours")
    else:
        hours_to_process = [hour.zfill(2)]

    # 3. Main processing loop per hour
    for h in hours_to_process:
        selected_folder_raw = gen_str_path_folder_raw_until_hour(
            position=position, product=product_id, year=year, day=day, hour=h
        )
        
        # 4. Search for .nc files (using rglob for safety)
        nc_candidates = sorted(list(selected_folder_raw.rglob("*LSTF*.nc")))
        
        if not nc_candidates:
            # Inform and skip if the hour folder is empty
            print(f"⚠️ No files found for hour {h}: {selected_folder_raw}")
            continue

        print(f"\n--- 🕒 PROCESSING HOUR: {h} ({len(nc_candidates)} files) ---")
        
        # 5. Process each file in the current hour
        for nc_file in nc_candidates:
            print(f"🚀 Executing: {nc_file.name}")
            try:
                run_runner_ABI_L2_LSTF_fnp01(nc_path=str(nc_file))
            except Exception as e:
                print(f"❌ Error processing {nc_file.name}: {e}")
                continue # Continue with the next file even if one fails

# =============================================================================
# DIAGNOSTIC MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n" + " Run  Day-Hour FNP01: LSTF RUNNER (MULTI-HOUR) ".center(80, "="))
    
    try:
        # Configuration for processing
        # Use "ALL" to process all 24 hour-folders or a specific hour string (e.g., "12")
        run_day_hour_ABI_L2_LSTF_fnp01(
            position = "WEST", 
            year     = "2026", 
            day      = "003", 
            hour     = "ALL"
        )
        print("\n" + "="*80)
        print("✅ GLOBAL PROCESSING FINISHED")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        print("="*80 + "\n")
