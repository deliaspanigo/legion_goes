"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f02_runners/ABI_L2_MCMIPF/runner_ABI_L2_MCMIPF_fnp02.py
Version: 0.0.4 (Surgical Silence & Auto-Mosaic)
Description: FNP02 - MCMIPF with advanced noise suppression and automatic comparison mosaic.
Last modification: 06-05-2026 16:15
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_MCMIPF.runner_ABI_L2_MCMIPF_fnp02
# =========================================================================================================================================

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
import matplotlib.pyplot as plt
from PIL import Image

# --- Local Libraries ---
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02 import gen_dict_output_file_name 
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp02 import run_proc_ABI_L2_MCMIPF_fnp02
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id

# =============================================================================
# SILENCING UTILITIES (Advanced Surgical Silence)
# =============================================================================

class SpecificMessageFilter:
    """Intersects stderr and filters out specific annoying messages."""
    def __init__(self, stream, message_part):
        self.stream = stream
        self.message_part = message_part

    def write(self, data):
        if self.message_part not in data:
            self.stream.write(data)
            self.stream.flush()

    def flush(self):
        self.stream.flush()

@contextmanager
def silence_runner_noise():
    """
    Surgically silences:
    1. HDF5 'No sensor name' via stderr.
    2. NumPy/Dask 'invalid value (sin/cos)' via errstate.
    3. RuntimeWarnings from Dask/Satpy.
    """
    original_stderr = sys.stderr
    sys.stderr = SpecificMessageFilter(original_stderr, "No sensor name specified")
    
    with np.errstate(all='ignore'):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            warnings.filterwarnings("ignore", category=UserWarning, module="satpy")
            try:
                yield
            finally:
                sys.stderr = original_stderr

# =============================================================================
# MOSAIC GENERATOR (Hardcoded)
# =============================================================================

def generate_comparison_mosaic(dict_paths):
    """Generates a vertical mosaic of PNGs found in the output dictionary."""
    MOSAIC_NAME = "MOSAIC_comparison.png"
    png_files = [Path(v) for v in dict_paths.values() if Path(v).suffix.lower() == '.png' and Path(v).exists()]
    png_files = [p for p in png_files if p.name != MOSAIC_NAME]

    if not png_files: return

    output_path = png_files[0].parent / MOSAIC_NAME
    if output_path.exists(): return

    n_images = len(png_files)
    fig, axes = plt.subplots(n_images, 1, figsize=(15, 8 * n_images))
    if n_images == 1: axes = [axes]

    for ax, img_path in zip(axes, png_files):
        try:
            img = Image.open(img_path)
            ax.imshow(img)
            ax.set_title(f"FILE: {img_path.name}", fontsize=14, fontweight='bold', pad=15)
            ax.axis('off')
        except: ax.axis('off')

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✅ Mosaic generated: {output_path.name}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def gen_str_folder_output(nc_path):
    nc_file_name = Path(nc_path).name
    match = re.search(r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})", nc_file_name)
    if not match: raise ValueError(f"Invalid format: {nc_file_name}")

    str_prod, str_sat, str_stimestamp = match.group("prod"), match.group("sat"), match.group("start")
    str_sat_num = str_sat[1:]
    str_pos = get_position_by_sat_id(sat_id = str_sat_num)
    
    str_output_folder = (
        Path("data_proc") / "sp01_single" / f"noaa-goes{str_sat_num}-{str_pos}" /
        str_prod / str_stimestamp[0:4] / str_stimestamp[4:7] / str_stimestamp[7:9] /
        f"s{str_stimestamp}" / f"{str_prod}_fnp02"
    )
    return str_output_folder

def gen_dict_path_output(nc_path):
    str_folder = gen_str_folder_output(nc_path)
    full_path = Path.cwd() / str_folder
    full_path.mkdir(parents=True, exist_ok=True)
    
    dict_names = gen_dict_output_file_name(nc_path=str(nc_path))
    return {k: (full_path / v) for k, v in dict_names.items()}

def is_processing_complete(output_dict: dict) -> bool:
    for p in output_dict.values():
        if not p.exists() or p.stat().st_size == 0: return False
    return True

# =============================================================================
# RUNNER CORE
# =============================================================================

def run_runner_ABI_L2_MCMIPF_fnp02(nc_path):
    nc_path = Path(nc_path)
    dict_path_output = gen_dict_path_output(nc_path=nc_path)
    
    if is_processing_complete(dict_path_output):
        print(f"  [SKIPPED] {nc_path.name} (Outputs OK)")
        return

    for p in dict_path_output.values():
        if p.exists(): p.unlink()

    print(f"  [PROCESSING] {nc_path.name}...")
    dict_str_paths = {k: str(v) for k, v in dict_path_output.items()}
    
    try:
        with silence_runner_noise():
            run_proc_ABI_L2_MCMIPF_fnp02(nc_path=str(nc_path), **dict_str_paths)
        
        # Generar mosaico al finalizar
        generate_comparison_mosaic(dict_path_output)
            
    except Exception as e:
        print(f"  ❌ Error processing {nc_path.name}: {e}")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP02: MCMIPF RUNNER ".center(80, "="))
    working_dir = Path.cwd() / "test_one_image"
    nc_candidates = sorted(list(working_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"❌ No .nc files found in: {working_dir}")
    else:
        run_runner_ABI_L2_MCMIPF_fnp02(nc_path=nc_candidates[0])
        print("-" * 80 + "\n✅ PROCESS FINISHED\n" + "=" * 80)
