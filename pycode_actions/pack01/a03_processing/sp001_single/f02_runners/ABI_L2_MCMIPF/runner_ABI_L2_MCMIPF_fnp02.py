"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f02_runners/ABI_L2_MCMIPF/runner_ABI_L2_MCMIPF_fnp02.py
Version: 0.0.4 (With Runtime Silence)
Description: FNP02 - MCMIPF with specific HDF5 and RuntimeWarning suppression.
Last modification: 05-05-2026 23:25
"""

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
import numpy as np
from satpy import Scene
from pyresample.geometry import AreaDefinition

# --- Local Libraries ---
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02 import dict_output_schema
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02 import run_proc_ABI_L2_MCMIPF_fnp02


def gen_str_folder_output(nc_path):
    """
    Generates the hierarchical output folder structure based on the NC filename.
    """
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
    str_prod_fnp = str_prod + "_fnp02"
    
    str_output_folder = (
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
    return str_output_folder

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

def run_runner_ABI_L2_MCMIPF_fnp02(nc_path):
    nc_path = Path(nc_path)
    dict_path_output = gen_dict_path_output(nc_path=nc_path)
    
    if is_processing_complete(dict_path_output):
        print(f"  [SKIPPED] {nc_path.name} (Outputs Size OK)")
        return

    for p in dict_path_output.values():
        if p.exists(): p.unlink()

    print(f"  [PROCESSING] {nc_path.name}...")

    dict_str_paths = {k: str(v) for k, v in dict_path_output.items()}
    
    # --- SURGICAL SILENCING BLOCK ---
    # np.errstate silences NumPy C-level warnings (sin/cos/invalid)
    # warnings.catch_warnings silences Python-level Dask/Satpy messages
    with np.errstate(all='ignore'):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            try:
                run_proc_ABI_L2_MCMIPF_fnp02(nc_path=str(nc_path), **dict_str_paths)
            except Exception as e:
                print(f"  ❌ Error processing {nc_path.name}: {e}")

# =============================================================================
# MAIN SIMPLE
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP02: MCMIPF DIAGNOSTIC TEST ".center(80, "="))
    
    working_dir = Path.cwd() / "test_one_image"
    nc_candidates = sorted(list(working_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ Error: No .nc files with 'MCMIPF' found in: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        run_runner_ABI_L2_MCMIPF_fnp02(nc_path=target_nc)
        print("-" * 80 + "\n✅ TEST FINISHED\n" + "=" * 80)
