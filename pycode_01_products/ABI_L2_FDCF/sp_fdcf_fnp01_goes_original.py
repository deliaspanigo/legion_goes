"""
FDCF FNP01 - GOES original products.
"""

import gc
import time

from satpy import Scene

from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_schema import (
    FDCF_COLOR_VARIANTS,
    sp_fdcf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.common import (
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
)


def sp_fdcf_fnp01_goes_original(nc_path, output_dir):
    """
    Generate FDCF FNP01 visual PNGs in the native GOES fixed-grid projection.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_fdcf_fnp01_output_schema(file_path, output_dir)
    result = {}

    print("[FDCF FNP01 GOES] Loading FDCF scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )

    for color_name, satpy_product in FDCF_COLOR_VARIANTS.items():
        print(
            f"[FDCF FNP01 GOES] Writing {color_name} ({satpy_product})...",
            flush=True,
        )
        scn.load([satpy_product])
        key = f"goes_native_{color_name}_png"
        scn.save_dataset(
            satpy_product,
            filename=str(outputs[key]),
            writer="simple_image",
        )
        result[key] = outputs[key]
        scn.unload(satpy_product)
        gc.collect()

    ensure_output_files(result)

    print(
        f"[FDCF FNP01 GOES] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result

