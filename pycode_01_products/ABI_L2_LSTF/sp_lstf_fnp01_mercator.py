"""
LSTF FNP01 - Web Mercator products.

This function writes only the Mercator PNG products needed by map viewers.
"""

import time

import numpy as np
from satpy import Scene

from legion_goes.pycode_01_products.common import (
    area_web_mercator,
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
    satpy_resample_kwargs,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_schema import (
    sp_lstf_fnp01_output_schema,
)


def sp_lstf_fnp01_mercator(nc_path, output_dir):
    """
    Generate LSTF FNP01 PNGs in Web Mercator.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_lstf_fnp01_output_schema(file_path, output_dir)

    print("[LSTF FNP01 Mercator] Loading LSTF scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )

    scn.load(["LST"])
    scn["LST"] = scn["LST"] - 273.15
    scn["LST"].attrs["units"] = "Celsius"
    scn.load(["lst_celsius_color01"])

    print("[LSTF FNP01 Mercator] Resampling to EPSG:3857...", flush=True)

    scn_mercator = scn.resample(
        area_web_mercator(),
        resampler="kd_tree",
        fill_value=np.nan,
        **satpy_resample_kwargs(),
    )

    print("[LSTF FNP01 Mercator] Writing PNGs...", flush=True)

    scn_mercator.save_dataset(
        "LST",
        filename=str(outputs["mercator_grey_png"]),
        writer="simple_image",
    )
    scn_mercator.save_dataset(
        "lst_celsius_color01",
        filename=str(outputs["mercator_color_png"]),
    )

    result = {
        "mercator_grey_png": outputs["mercator_grey_png"],
        "mercator_color_png": outputs["mercator_color_png"],
    }
    ensure_output_files(result)

    print(
        f"[LSTF FNP01 Mercator] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result
