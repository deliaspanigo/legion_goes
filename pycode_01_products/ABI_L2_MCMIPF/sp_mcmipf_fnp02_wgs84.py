"""
MCMIPF FNP02 - WGS84 products.
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
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02_helpers import (
    apply_grayscale_transparency,
    apply_white_clouds_vibrant,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02_schema import (
    sp_mcmipf_fnp02_output_schema,
)


def sp_mcmipf_fnp02_wgs84(nc_path, output_dir):
    """
    Generate MCMIPF FNP02 colorized IR cloud products in global WGS84.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_mcmipf_fnp02_output_schema(file_path, output_dir)
    product_id = "colorized_ir_clouds"

    print("[MCMIPF FNP02 WGS84] Loading colorized IR clouds scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )
    scn.load([product_id])

    print("[MCMIPF FNP02 WGS84] Resampling to EPSG:4326...", flush=True)

    scn_wgs84 = scn.resample(
        area_wgs84(),
        resampler="kd_tree",
        **satpy_resample_kwargs(),
    )

    print("[MCMIPF FNP02 WGS84] Writing PNG and GeoTIFF outputs...", flush=True)

    scn_wgs84.save_dataset(
        product_id,
        filename=str(outputs["wgs84_ir_png"]),
        writer="simple_image",
    )
    scn_wgs84.save_dataset(
        product_id,
        filename=str(outputs["wgs84_ir_tif"]),
        writer="geotiff",
    )

    print("[MCMIPF FNP02 WGS84] Writing transparent cloud overlays...", flush=True)

    apply_grayscale_transparency(
        outputs["wgs84_ir_png"],
        outputs["wgs84_transparent_png"],
    )
    apply_white_clouds_vibrant(
        outputs["wgs84_transparent_png"],
        outputs["wgs84_selected_clouds_png"],
    )

    result = {
        "wgs84_ir_png": outputs["wgs84_ir_png"],
        "wgs84_transparent_png": outputs["wgs84_transparent_png"],
        "wgs84_selected_clouds_png": outputs["wgs84_selected_clouds_png"],
        "wgs84_ir_tif": outputs["wgs84_ir_tif"],
    }
    ensure_output_files(result)

    print(
        f"[MCMIPF FNP02 WGS84] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result
