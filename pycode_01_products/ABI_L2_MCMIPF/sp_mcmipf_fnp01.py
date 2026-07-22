"""
MCMIPF FNP01 simple processing orchestrator.

FNP01 is the True Color background used by the Temperature activity.
"""

import time

from legion_goes.pycode_01_products.common import processing_checkpoint
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_goes_original import (
    sp_mcmipf_fnp01_goes_original,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_mercator import (
    sp_mcmipf_fnp01_mercator,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_schema import (
    sp_mcmipf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01_wgs84 import (
    sp_mcmipf_fnp01_wgs84,
)


def _expected_mcmipf_fnp01_outputs(nc_path, output_dir, proc_mode):
    schema = sp_mcmipf_fnp01_output_schema(nc_path, output_dir)
    expected = {}

    if proc_mode in {"viewer", "full"}:
        expected.update({key: value for key, value in schema.items() if key.startswith("goes_native_")})

    expected.update({key: value for key, value in schema.items() if key.startswith("wgs84_")})

    if proc_mode in {"viewer", "full"}:
        expected.update({key: value for key, value in schema.items() if key.startswith("mercator_")})

    return expected


def sp_mcmipf_fnp01(nc_path, output_dir, proc_mode="viewer", overwrite=False):
    """
    Run MCMIPF FNP01 according to a processing mode.
    """

    start_time = time.time()
    proc_mode = str(proc_mode).strip().lower()
    outputs = {}

    print(f"[MCMIPF FNP01] Processing mode: {proc_mode}", flush=True)

    if proc_mode not in {"operative", "viewer", "full"}:
        raise ValueError(
            "Unsupported proc_mode for MCMIPF FNP01: "
            f"{proc_mode}. Use 'operative', 'viewer', or 'full'."
        )

    expected_outputs = _expected_mcmipf_fnp01_outputs(nc_path, output_dir, proc_mode)
    checkpoint = processing_checkpoint(
        "MCMIPF FNP01",
        expected_outputs=expected_outputs,
        overwrite=overwrite,
    )

    if checkpoint["action"] == "skip":
        result = {
            "product": "ABI-L2-MCMIPF",
            "fnp": "fnp01",
            "proc_mode": proc_mode,
            "outputs": expected_outputs,
            "checkpoint": checkpoint,
            "duration_seconds": round(time.time() - start_time, 2),
            "skipped": True,
        }
        print(f"[MCMIPF FNP01] Skipped in {result['duration_seconds']}s", flush=True)
        return result

    if proc_mode in {"viewer", "full"}:
        outputs.update(sp_mcmipf_fnp01_goes_original(nc_path, output_dir))

    outputs.update(sp_mcmipf_fnp01_wgs84(nc_path, output_dir))

    if proc_mode in {"viewer", "full"}:
        outputs.update(sp_mcmipf_fnp01_mercator(nc_path, output_dir))

    result = {
        "product": "ABI-L2-MCMIPF",
        "fnp": "fnp01",
        "proc_mode": proc_mode,
        "outputs": outputs,
        "checkpoint": checkpoint,
        "duration_seconds": round(time.time() - start_time, 2),
        "skipped": False,
    }

    print(
        f"[MCMIPF FNP01] Finished in {result['duration_seconds']}s",
        flush=True,
    )

    return result
