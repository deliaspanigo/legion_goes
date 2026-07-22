"""
MCMIPF FNP01 - WGS84 products.

This function writes the WGS84 True Color PNG, WGS84 day-only PNG, and a WGS84
GeoTIFF for GIS inspection.
"""

import time

from satpy import Scene

from legion_goes.pycode_01_products.common import (
    area_wgs84,
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


def sp_mcmipf_fnp01_wgs84(nc_path, output_dir):
    """
    Generate MCMIPF FNP01 True Color products in global WGS84.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_mcmipf_fnp01_output_schema(file_path, output_dir)

    print("[MCMIPF FNP01 WGS84] Loading True Color scene...", flush=True)

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

    print("[MCMIPF FNP01 WGS84] Resampling to EPSG:4326...", flush=True)

    scn_wgs84 = scn.resample(
        area_wgs84(),
        resampler="kd_tree",
        **satpy_resample_kwargs(),
    )
    scn_wgs84_day = scn_day.resample(
        area_wgs84(),
        resampler="kd_tree",
        **satpy_resample_kwargs(),
    )

    print("[MCMIPF FNP01 WGS84] Writing PNG and GeoTIFF outputs...", flush=True)

    scn_wgs84.save_dataset(
        "true_color",
        filename=str(outputs["wgs84_true_color_png"]),
        writer="simple_image",
    )
    scn_wgs84.save_dataset(
        "true_color",
        filename=str(outputs["wgs84_true_color_tif"]),
        writer="geotiff",
    )
    scn_wgs84_day.save_dataset(
        "true_color",
        filename=str(outputs["wgs84_true_color_day_only_png"]),
        writer="simple_image",
    )

    result = {
        "wgs84_true_color_png": outputs["wgs84_true_color_png"],
        "wgs84_true_color_day_only_png": outputs["wgs84_true_color_day_only_png"],
        "wgs84_true_color_tif": outputs["wgs84_true_color_tif"],
    }
    ensure_output_files(result)

    print(
        f"[MCMIPF FNP01 WGS84] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result

