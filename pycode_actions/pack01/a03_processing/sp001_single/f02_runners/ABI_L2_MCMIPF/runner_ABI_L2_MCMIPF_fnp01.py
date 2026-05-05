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
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01 import dict_output_schema
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01 import run_proc_ABI_L2_MCMIPF_fnp01

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

    str_prod = match.group("prod")
    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start")
    
    str_year = str_stimestamp[0:4]
    str_day  = str_stimestamp[4:7]
    str_hour = str_stimestamp[7:9]
    
    str_bucket = "noaa-goes" + str_sat_number
    str_prod_fnp = str_prod + "_fnp01"
    
    return (
        Path("data_proc") / 
        "sp01_single" / 
        str_bucket /
        str_prod / 
        str_year / 
        str_day / 
        str_hour / 
        str_stimestamp / 
        str_prod_fnp
    )

def gen_dict_path_output(nc_path):
    working_dir = Path.cwd() 
    str_folder = gen_str_folder_output(nc_path)
    str_output_folder_path = working_dir / str_folder
    str_output_folder_path.mkdir(parents=True, exist_ok=True)
    
    dict_path_output = {k: (str_output_folder_path / v) for k, v in dict_output_schema.items()}
    return dict_path_output

def is_processing_complete(output_dict: dict) -> bool:
    for p in output_dict.values():
        if not p.exists() or p.stat().st_size == 0:
            return False
    return True

# =============================================================================
# RUNNER CORE
# =============================================================================

def run_runner_ABI_L2_MCMIPF_fnp01(nc_path):
    nc_path = Path(nc_path)
    dict_path_output = gen_dict_path_output(nc_path=nc_path)
    
    if is_processing_complete(dict_path_output):
        print(f"  [SKIPPED] {nc_path.name} (Outputs Size OK)")
        return

    for p in dict_path_output.values():
        if p.exists(): p.unlink()

    print(f"  [PROCESSING] {nc_path.name}...")

    dict_str_paths = {k: str(v) for k, v in dict_path_output.items()}
    
    # --- EXECUTION WITH SURGICAL SILENCING ---
    try:
        with silence_runner_noise():
            run_proc_ABI_L2_MCMIPF_fnp01(nc_path=str(nc_path), **dict_str_paths)
    except Exception as e:
        print(f"  ❌ Error processing {nc_path.name}: {e}")

# =============================================================================
# MAIN SIMPLE
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP01: MCMIPF DIAGNOSTIC TEST ".center(80, "="))
    
    working_dir = Path.cwd() / "test_one_image"
    nc_candidates = sorted(list(working_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No .nc files with 'MCMIPF' found in: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        run_runner_ABI_L2_MCMIPF_fnp01(nc_path=target_nc)
        print("-" * 80 + "\n✅ TEST FINISHED\n" + "=" * 80)
