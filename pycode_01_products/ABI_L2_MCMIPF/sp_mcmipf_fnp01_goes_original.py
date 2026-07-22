"""
MCMIPF FNP01 - GOES original projection.

This function writes the native True Color PNGs without creating WGS84 or
Mercator products.
"""

import time

from satpy import Scene

from legion_goes.pycode_01_products.common import (
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_helpers import (
    apply_dark_pixel_mask,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_schema import (
    sp_mcmipf_fnp01_output_schema,
)


def sp_mcmipf_fnp01_goes_original(nc_path, output_dir):
    """
    Generate MCMIPF FNP01 True Color PNGs in the original GOES projection.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_mcmipf_fnp01_output_schema(file_path, output_dir)

    print("[MCMIPF FNP01 GOES] Loading True Color scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )
    scn.load(["true_color"])

    print("[MCMIPF FNP01 GOES] Writing native True Color PNG...", flush=True)
    scn.save_dataset(
        "true_color",
        filename=str(outputs["goes_native_true_color_png"]),
        writer="simple_image",
    )

    print("[MCMIPF FNP01 GOES] Building day-only layer...", flush=True)
    scn_day = scn.copy()
    scn_day["true_color"] = apply_dark_pixel_mask(
        scn_day["true_color"],
        threshold=0.05,
    )

    scn_day.save_dataset(
        "true_color",
        filename=str(outputs["goes_native_true_color_day_only_png"]),
        writer="simple_image",
    )

    result = {
        "goes_native_true_color_png": outputs["goes_native_true_color_png"],
        "goes_native_true_color_day_only_png": outputs[
            "goes_native_true_color_day_only_png"
        ],
    }
    ensure_output_files(result)

    print(
        f"[MCMIPF FNP01 GOES] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result

