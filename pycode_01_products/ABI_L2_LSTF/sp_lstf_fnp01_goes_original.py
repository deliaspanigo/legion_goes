"""
LSTF FNP01 - GOES original projection.

This function writes the native GOES PNG products only. It is useful when a
viewer needs the satellite-native view and should not force WGS84 or Mercator
products to be created.
"""

import time

from satpy import Scene

from legion_goes.pycode_01_products.common import (
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_schema import (
    sp_lstf_fnp01_output_schema,
)


def sp_lstf_fnp01_goes_original(nc_path, output_dir):
    """
    Generate LSTF FNP01 PNGs in the original GOES projection.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_lstf_fnp01_output_schema(file_path, output_dir)

    print("[LSTF FNP01 GOES] Loading LSTF scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )

    scn.load(["LST"])
    scn["LST"] = scn["LST"] - 273.15
    scn["LST"].attrs["units"] = "Celsius"
    scn.load(["lst_celsius_color01"])

    print("[LSTF FNP01 GOES] Writing native PNGs...", flush=True)

    scn.save_dataset(
        "LST",
        filename=str(outputs["goes_native_grey_png"]),
        writer="simple_image",
    )
    scn.save_dataset(
        "lst_celsius_color01",
        filename=str(outputs["goes_native_color_png"]),
    )

    result = {
        "goes_native_grey_png": outputs["goes_native_grey_png"],
        "goes_native_color_png": outputs["goes_native_color_png"],
    }
    ensure_output_files(result)

    print(
        f"[LSTF FNP01 GOES] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result

