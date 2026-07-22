"""
MCMIPF FNP02 - Web Mercator products.
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
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02_helpers import (
    apply_grayscale_transparency,
    apply_white_clouds_vibrant,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02_schema import (
    sp_mcmipf_fnp02_output_schema,
)


def sp_mcmipf_fnp02_mercator(nc_path, output_dir):
    """
    Generate MCMIPF FNP02 colorized IR cloud PNGs in Web Mercator.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_mcmipf_fnp02_output_schema(file_path, output_dir)
    product_id = "colorized_ir_clouds"

    print("[MCMIPF FNP02 Mercator] Loading colorized IR clouds scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )
    scn.load([product_id])

    print("[MCMIPF FNP02 Mercator] Resampling to EPSG:3857...", flush=True)

    scn_mercator = scn.resample(
        area_web_mercator(),
        resampler="kd_tree",
        **satpy_resample_kwargs(),
    )

    print("[MCMIPF FNP02 Mercator] Writing PNG outputs...", flush=True)

    scn_mercator.save_dataset(
        product_id,
        filename=str(outputs["mercator_ir_png"]),
        writer="simple_image",
    )

    print("[MCMIPF FNP02 Mercator] Writing transparent cloud overlays...", flush=True)

    apply_grayscale_transparency(
        outputs["mercator_ir_png"],
        outputs["mercator_transparent_png"],
    )
    apply_white_clouds_vibrant(
        outputs["mercator_transparent_png"],
        outputs["mercator_selected_clouds_png"],
    )

    result = {
        "mercator_ir_png": outputs["mercator_ir_png"],
        "mercator_transparent_png": outputs["mercator_transparent_png"],
        "mercator_selected_clouds_png": outputs["mercator_selected_clouds_png"],
    }
    ensure_output_files(result)

    print(
        f"[MCMIPF FNP02 Mercator] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result
