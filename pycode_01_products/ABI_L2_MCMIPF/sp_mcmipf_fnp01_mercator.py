"""
MCMIPF FNP01 - Web Mercator products.
"""

import time

from satpy import Scene

from legion_goes.pycode_01_products.common import (
    area_web_mercator,
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
    satpy_resample_kwargs,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_helpers import (
    apply_dark_pixel_mask,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_schema import (
    sp_mcmipf_fnp01_output_schema,
)


def sp_mcmipf_fnp01_mercator(nc_path, output_dir):
    """
    Generate MCMIPF FNP01 True Color PNGs in Web Mercator.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_mcmipf_fnp01_output_schema(file_path, output_dir)

    print("[MCMIPF FNP01 Mercator] Loading True Color scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )
    scn.load(["true_color"])

    scn_day = scn.copy()
    scn_day["true_color"] = apply_dark_pixel_mask(
        scn_day["true_color"],
        threshold=0.05,
    )

    print("[MCMIPF FNP01 Mercator] Resampling to EPSG:3857...", flush=True)

    scn_mercator = scn.resample(
        area_web_mercator(),
        resampler="kd_tree",
        **satpy_resample_kwargs(),
    )
    scn_mercator_day = scn_day.resample(
        area_web_mercator(),
        resampler="kd_tree",
        **satpy_resample_kwargs(),
    )

    print("[MCMIPF FNP01 Mercator] Writing PNG outputs...", flush=True)

    scn_mercator.save_dataset(
        "true_color",
        filename=str(outputs["mercator_true_color_png"]),
        writer="simple_image",
    )
    scn_mercator_day.save_dataset(
        "true_color",
        filename=str(outputs["mercator_true_color_day_only_png"]),
        writer="simple_image",
    )

    result = {
        "mercator_true_color_png": outputs["mercator_true_color_png"],
        "mercator_true_color_day_only_png": outputs[
            "mercator_true_color_day_only_png"
        ],
    }
    ensure_output_files(result)

    print(
        f"[MCMIPF FNP01 Mercator] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result

