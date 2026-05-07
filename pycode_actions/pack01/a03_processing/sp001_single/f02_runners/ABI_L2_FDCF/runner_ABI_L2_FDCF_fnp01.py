"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f02_runners/ABI_L2_FDCF/runner_ABI_L2_FDCF.py
Version: 0.0.2
Description: Runner - Land Surface Temperature with Universal Path Detection.
Last modification: 05-05-2026 18:18
"""
# ========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_FDCF.runner_ABI_L2_FDCF_fnp01
# ========================================================================================================================================

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

# Local libraries
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_FDCF.proc_ABI_L2_FDCF_fnp01 import gen_dict_output_file_name 
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_FDCF.proc_ABI_L2_FDCF_fnp01 import run_proc_ABI_L2_FDCF_fnp01
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id
# =============================================================================
# PATH GENERATION & SATELLITE DETECTION ENGINE
# =============================================================================
def gen_str_folder_output(nc_path):
    """
    Parses the NC filename to generate a hierarchical output folder structure.
    """
    # Ensure nc_path is a Path object and get the filename
    nc_file_name = Path(nc_path).name
    
    # Regex to extract:
    # 1. Product (e.g., ABI-L2-FDCF)
    # 2. Satellite (e.g., G19)
    # 3. Start timestamp 's' (Year + Julian Day + Hour + Min + Sec)
    match = re.search(r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})", nc_file_name)
    
    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    # Extract data from match
    str_prod = match.group("prod")
    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start") 
    str_stimestamp_mod = f"s{str_stimestamp}"
    str_position = get_position_by_sat_id(sat_id = str_sat_number)
    
    # Slice the start timestamp (s)
    str_year = str_stimestamp[0:4]   # 2026
    str_day  = str_stimestamp[4:7]   # 003
    str_hour = str_stimestamp[7:9]   # 12
    
    str_bucket = "noaa-goes" + str_sat_number
    str_bucket_mod = f"{str_bucket}-{str_position}"
    str_prod_fnp = str_prod + "_fnp01"
    
    # Hierarchical path construction
    # Structure: data_proc / sp01_single / noaa-goesXX-position / ABI-L2-FDCF / YYYY / DDD / HH / TIMESTAMP_mod / fnp01
    str_output_folder = (
        Path("data_proc") / 
        "sp01_single" / 
        str_bucket_mod /
        str_prod / 
        str_year / 
        str_day / 
        str_hour / 
        str_stimestamp_mod / 
        str_prod_fnp
    )
    
    return str_output_folder

def gen_dict_path_output(nc_path):
    """
    Creates the output directory and maps schema filenames to full Path objects.
    """
    working_dir = Path.cwd() 
    str_folder = gen_str_folder_output(nc_path)
    
    str_output_folder_path = working_dir / str_folder
    str_output_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Map filenames to Path objects (instead of strings) for validation
    dict_output_file_name = gen_dict_output_file_name(nc_path=str(nc_path))
    dict_output_file_path = {k: (str_output_folder_path / v) for k, v in dict_output_file_name.items()}
    
    return dict_output_file_path
    
def is_processing_complete(output_dict: dict) -> bool:
    """
    Checks if all files in the output dictionary exist and are not empty.
    Returns True only if EVERY file is valid.
    """
    for p in output_dict.values():
        if not p.exists() or p.stat().st_size == 0:
            return False
            
    return True
    
def run_runner_ABI_L2_FDCF_fnp01(nc_path, overwrite=False):
    """
    Main runner logic: manages skip-logic, cleanup, and core execution.
    """
    nc_path = Path(nc_path)
    
    # 1. Get expected output paths as Path objects
    dict_path_output = gen_dict_path_output(nc_path=nc_path)
    
    # 2. Check current status
    exists_count = sum(1 for p in dict_path_output.values() if p.exists())
    total_expected = len(dict_path_output)
    all_exist = exists_count == total_expected

    # 3. Decision Logic & Specialized Printing
    if all_exist and not overwrite:
        print(f"  [SKIPPED]     {nc_path.name} (All {total_expected} outputs exist)")
        return

    # Determine the reason for processing
    if overwrite and all_exist:
        reason = "OVERWRITE (Forced by user)"
    elif exists_count > 0:
        reason = f"INCOMPLETE ({exists_count}/{total_expected} files found, fixing...)"
    else:
        reason = "NEW (No previous outputs found)"

    print(f"  [PROCESSING]  {nc_path.name}")
    print(f"                Reason: {reason}")

    # 4. Clean up before reprocessing
    for p in dict_path_output.values():
        if p.exists(): 
            p.unlink()
    
    # 5. Execute core processing
    dict_str_paths = {k: str(v) for k, v in dict_path_output.items()}
    run_proc_ABI_L2_FDCF_fnp01(nc_path=str(nc_path), **dict_str_paths)
    

# =============================================================================
# SIMPLE MAIN (Terminal & Diagnostic)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " Runner FDCF FNP01: DIAGNOSTIC TEST ".center(80, "="))
    
    # 1. Execution Path
    working_dir = Path.cwd() / "test_one_image"
    
    # 2. Look for the first .nc file containing 'FDCF'
    nc_candidates = sorted(list(working_dir.glob("*FDCF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No .nc files with 'FDCF' found in: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        
        # Start runner
        run_runner_ABI_L2_FDCF_fnp01(nc_path=target_nc, overwrite = True)
        print("-" * 80 + "\n✅ TEST COMPLETED\n" + "=" * 80)
