"""
FDCF FNP01 - WGS84 products.
"""

import gc
import time

from satpy import Scene

from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_schema import (
    FDCF_COLOR_VARIANTS,
    sp_fdcf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.common import (
    area_wgs84,
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
    satpy_resample_kwargs,
)


def sp_fdcf_fnp01_wgs84(nc_path, output_dir):
    """
    Generate FDCF FNP01 visual PNGs and GeoTIFFs in global WGS84.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_fdcf_fnp01_output_schema(file_path, output_dir)
    result = {}

    print("[FDCF FNP01 WGS84] Loading FDCF scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )

    for color_name, satpy_product in FDCF_COLOR_VARIANTS.items():
        print(
            f"[FDCF FNP01 WGS84] Resampling {color_name} ({satpy_product})...",
            flush=True,
        )
        scn.load([satpy_product])
        scn_wgs84 = scn.resample(
            area_wgs84(),
            resampler="kd_tree",
            **satpy_resample_kwargs(),
        )

        tif_key = f"wgs84_{color_name}_tif"
        png_key = f"wgs84_{color_name}_png"

        print(f"[FDCF FNP01 WGS84] Writing {color_name}...", flush=True)
        scn_wgs84.save_dataset(
            satpy_product,
            filename=str(outputs[tif_key]),
            writer="geotiff",
        )
        scn_wgs84.save_dataset(
            satpy_product,
            filename=str(outputs[png_key]),
            writer="simple_image",
        )

        result[tif_key] = outputs[tif_key]
        result[png_key] = outputs[png_key]

        del scn_wgs84
        scn.unload(satpy_product)
        gc.collect()

    ensure_output_files(result)

    print(
        f"[FDCF FNP01 WGS84] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result

