"""
FDCF FNP01 - Web Mercator products.
"""

import gc
import time

from satpy import Scene

from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_schema import (
    FDCF_COLOR_VARIANTS,
    sp_fdcf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.common import (
    area_web_mercator,
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
    satpy_resample_kwargs,
)


def sp_fdcf_fnp01_mercator(nc_path, output_dir):
    """
    Generate FDCF FNP01 visual PNGs in global Web Mercator.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_fdcf_fnp01_output_schema(file_path, output_dir)
    result = {}

    print("[FDCF FNP01 Mercator] Loading FDCF scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )

    for color_name, satpy_product in FDCF_COLOR_VARIANTS.items():
        print(
            f"[FDCF FNP01 Mercator] Resampling {color_name} ({satpy_product})...",
            flush=True,
        )
        scn.load([satpy_product])
        scn_mercator = scn.resample(
            area_web_mercator(),
            resampler="kd_tree",
            **satpy_resample_kwargs(),
        )

        key = f"mercator_{color_name}_png"
        scn_mercator.save_dataset(
            satpy_product,
            filename=str(outputs[key]),
            writer="simple_image",
        )
        result[key] = outputs[key]

        del scn_mercator
        scn.unload(satpy_product)
        gc.collect()

    ensure_output_files(result)

    print(
        f"[FDCF FNP01 Mercator] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result

