"""
MCMIPF FNP02 - GOES original projection.
"""

import time

from satpy import Scene

from legion_goes.pycode_01_products.common import (
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02_helpers import (
    apply_grayscale_transparency,
    apply_white_clouds_vibrant,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02_schema import (
    sp_mcmipf_fnp02_output_schema,
)


def sp_mcmipf_fnp02_goes_original(nc_path, output_dir):
    """
    Generate MCMIPF FNP02 colorized IR cloud PNGs in the original GOES grid.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_mcmipf_fnp02_output_schema(file_path, output_dir)
    product_id = "colorized_ir_clouds"

    print("[MCMIPF FNP02 GOES] Loading colorized IR clouds scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )
    scn.load([product_id])

    print("[MCMIPF FNP02 GOES] Writing native colorized IR PNG...", flush=True)

    scn.save_dataset(
        product_id,
        filename=str(outputs["goes_native_ir_png"]),
        writer="simple_image",
    )

    print("[MCMIPF FNP02 GOES] Writing transparent cloud overlays...", flush=True)

    apply_grayscale_transparency(
        outputs["goes_native_ir_png"],
        outputs["goes_native_transparent_png"],
    )
    apply_white_clouds_vibrant(
        outputs["goes_native_transparent_png"],
        outputs["goes_native_selected_clouds_png"],
    )

    result = {
        "goes_native_ir_png": outputs["goes_native_ir_png"],
        "goes_native_transparent_png": outputs["goes_native_transparent_png"],
        "goes_native_selected_clouds_png": outputs["goes_native_selected_clouds_png"],
    }
    ensure_output_files(result)

    print(
        f"[MCMIPF FNP02 GOES] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result
