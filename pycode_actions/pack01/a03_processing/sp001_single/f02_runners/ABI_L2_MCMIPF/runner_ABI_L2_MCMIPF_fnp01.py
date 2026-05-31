"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f02_runners/ABI_L2_MCMIPF/runner_ABI_L2_MCMIPF_fnp01.py
Version: 0.0.3 (Simple & Robust Main)
Description: FNP01 - MCMIPF with specific HDF5 and RuntimeWarning suppression.
Last modification: 05-05-2026 20:30
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_MCMIPF.runner_ABI_L2_MCMIPF_fnp01
# =========================================================================================================================================

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
import numpy as np
import re

# --- Local Libraries ---
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01 import gen_dict_output_file_name 
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01 import run_proc_ABI_L2_MCMIPF_fnp01
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id

# =============================================================================
# SILENCING UTILITIES (Surgical)
# =============================================================================

class SpecificMessageFilter:
    """Intersects stderr and filters out a specific annoying message."""
    def __init__(self, stream, message_part):
        self.stream = stream
        self.message_part = message_part

    def write(self, data):
        # If the specific noise is present, we drop it
        if self.message_part not in data:
            self.stream.write(data)
            self.stream.flush()

    def flush(self):
        self.stream.flush()

@contextmanager
def silence_runner_noise():
    """
    Surgically silences:
    1. HDF5 'No sensor name' messages via stderr redirection.
    2. NumPy 'Mean of empty slice' via warnings filter.
    """
    # 1. Setup Stream Filter for HDF5
    original_stderr = sys.stderr
    sys.stderr = SpecificMessageFilter(original_stderr, "No sensor name specified")
    
    # 2. Setup Warning Filter for NumPy/Satpy
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning, message="Mean of empty slice")
        warnings.filterwarnings("ignore", category=UserWarning, module="satpy")
        try:
            yield
        finally:
            # Restore stderr
            sys.stderr = original_stderr

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def gen_str_folder_output(nc_path):
    nc_file_name = Path(nc_path).name
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
    
    str_year = str_stimestamp[0:4]
    str_day  = str_stimestamp[4:7]
    str_hour = str_stimestamp[7:9]
    
    str_bucket = "noaa-goes" + str_sat_number
    str_bucket_mod = f"{str_bucket}-{str_position}"
    str_prod_fnp = str_prod + "_fnp01"
    
    
    str_output_folder = (
        Path("sp01_single") / 
        str_bucket_mod /
        str_prod / 
        str_year / 
        str_day / 
        str_hour / 
        str_stimestamp_mod / 
        str_prod_fnp
    )
    
    return str_output_folder

def gen_dict_path_output(nc_path, str_folder_path_data_proc=None):
    """
    Creates the output directory and maps schema filenames to full Path objects.

    Parameters
    ----------
    nc_path : str or Path
        Input NetCDF file.

    str_folder_path_data_proc : str or Path
        Root data_proc folder. Required.

    Returns
    -------
    dict
        Dictionary where keys are logical output names and values are full Path objects.
    """

    if str_folder_path_data_proc is None:
        raise ValueError("str_folder_path_data_proc is required")

    nc_path = Path(nc_path)

    data_proc_dir = Path(str_folder_path_data_proc).expanduser().resolve()

    if data_proc_dir.exists() and not data_proc_dir.is_dir():
        raise ValueError(f"str_folder_path_data_proc exists but is not a folder: {data_proc_dir}")

    data_proc_dir.mkdir(parents=True, exist_ok=True)

    relative_output_folder = gen_str_folder_output(nc_path)
    output_folder_path = data_proc_dir / relative_output_folder
    output_folder_path.mkdir(parents=True, exist_ok=True)

    dict_output_file_name = gen_dict_output_file_name(
        nc_path=str(nc_path)
    )

    dict_output_file_path = {
        key: output_folder_path / file_name
        for key, file_name in dict_output_file_name.items()
    }

    return dict_output_file_path


def is_processing_complete(output_dict: dict) -> bool:
    for p in output_dict.values():
        if not p.exists() or p.stat().st_size == 0:
            return False
    return True

# =============================================================================
# RUNNER CORE
# =============================================================================

def run_runner_ABI_L2_MCMIPF_fnp01(nc_path, str_folder_path_data_proc=None, overwrite=False):
    """
    Main runner logic for MCMIPF: manages skip-logic with detailed daygnostics,
    surgical silencing, and core execution.
    """
    nc_path = Path(nc_path)
    
    # 1. Get expected output paths as Path objects
    dict_path_output = gen_dict_path_output(
        nc_path=nc_path,
        str_folder_path_data_proc=str_folder_path_data_proc
    )
    
    # 2. Diagnostic: Check current status
    exists_count = sum(1 for p in dict_path_output.values() if p.exists())
    total_expected = len(dict_path_output)
    all_exist = exists_count == total_expected

    # 3. Decision Logic & Specialized Printing
    if all_exist and not overwrite:
        print(f"  [SKIPPED]     {nc_path.name} (All {total_expected} outputs exist)")
        return True

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

    # 5. Execute core processing with Surgical Silencing
    dict_str_paths = {k: str(v) for k, v in dict_path_output.items()}
    
    try:
        with silence_runner_noise():
            success = run_proc_ABI_L2_MCMIPF_fnp01(nc_path=str(nc_path), **dict_str_paths)
    except Exception as e:
        print(f"  [ERROR] Error processing {nc_path.name}: {e}")
        return False

    if not success:
        print(f"  [FAILED]      {nc_path.name}")
        print("                Core function returned False.")
        return False

    if not is_processing_complete(dict_path_output):
        print(f"  [INCOMPLETE]  {nc_path.name}")
        return False
    print(f"  [COMPLETED]   {nc_path.name}")
    return True

# =============================================================================
# MAIN SIMPLE
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP01: MCMIPF DIAGNOSTIC TEST ".center(80, "="))
    
    working_dir = Path.cwd() / "test_one_image"
    nc_candidates = sorted(list(working_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"[ERROR] No .nc files with 'MCMIPF' found in: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        run_runner_ABI_L2_MCMIPF_fnp01(nc_path=target_nc, overwrite = True)
        print("-" * 80 + "\nx TEST FINISHED\n" + "=" * 80)
