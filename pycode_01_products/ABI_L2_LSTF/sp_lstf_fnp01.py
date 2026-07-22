"""
LSTF FNP01 simple processing orchestrator.

This file is the human-friendly entry point for LSTF FNP01. It delegates the
real work to one function per reference system and decides, before processing,
whether the expected output set is already complete.
"""

import time

from legion_goes.pycode_01_products.common import processing_checkpoint
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_goes_original import (
    sp_lstf_fnp01_goes_original,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_mercator import (
    sp_lstf_fnp01_mercator,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_reference import (
    sp_lstf_fnp01_reference,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_schema import (
    sp_lstf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_statistics import (
    sp_lstf_fnp01_statistics,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_wgs84 import (
    sp_lstf_fnp01_wgs84,
)


def _expected_lstf_fnp01_outputs(nc_path, output_dir, proc_mode):
    schema = sp_lstf_fnp01_output_schema(nc_path, output_dir)
    expected = {}

    if proc_mode in {"viewer", "full"}:
        expected.update({key: value for key, value in schema.items() if key.startswith("goes_native_")})

    expected.update({key: value for key, value in schema.items() if key.startswith("wgs84_")})

    if proc_mode in {"viewer", "full"}:
        expected.update({key: value for key, value in schema.items() if key.startswith("mercator_")})

    expected.update({key: value for key, value in schema.items() if key.startswith("statistics_")})
    expected.update({key: value for key, value in schema.items() if key.startswith("histogram_")})
    expected.update({key: value for key, value in schema.items() if key.startswith("boxplot_")})
    expected.update({key: value for key, value in schema.items() if key.startswith("temperature_reference_")})

    return expected


def sp_lstf_fnp01(nc_path, output_dir, proc_mode="viewer", overwrite=False):
    """
    Run LSTF FNP01 according to a processing mode.

    If all expected outputs for the selected ``proc_mode`` already exist and
    ``overwrite`` is False, processing is skipped. If the set is incomplete,
    existing partial outputs are removed and the FNP is processed again.
    """

    start_time = time.time()
    proc_mode = str(proc_mode).strip().lower()
    outputs = {}

    print(f"[LSTF FNP01] Processing mode: {proc_mode}", flush=True)

    if proc_mode not in {"operative", "viewer", "full"}:
        raise ValueError(
            "Unsupported proc_mode for LSTF FNP01: "
            f"{proc_mode}. Use 'operative', 'viewer', or 'full'."
        )

    expected_outputs = _expected_lstf_fnp01_outputs(nc_path, output_dir, proc_mode)
    checkpoint = processing_checkpoint(
        "LSTF FNP01",
        expected_outputs=expected_outputs,
        overwrite=overwrite,
    )

    if checkpoint["action"] == "skip":
        result = {
            "product": "ABI-L2-LSTF",
            "fnp": "fnp01",
            "proc_mode": proc_mode,
            "outputs": expected_outputs,
            "reference": sp_lstf_fnp01_reference(),
            "checkpoint": checkpoint,
            "duration_seconds": round(time.time() - start_time, 2),
            "skipped": True,
        }
        print(f"[LSTF FNP01] Skipped in {result['duration_seconds']}s", flush=True)
        return result

    if proc_mode in {"viewer", "full"}:
        outputs.update(sp_lstf_fnp01_goes_original(nc_path, output_dir))

    outputs.update(sp_lstf_fnp01_wgs84(nc_path, output_dir))

    if proc_mode in {"viewer", "full"}:
        outputs.update(sp_lstf_fnp01_mercator(nc_path, output_dir))

    outputs.update(sp_lstf_fnp01_statistics(nc_path, output_dir))

    result = {
        "product": "ABI-L2-LSTF",
        "fnp": "fnp01",
        "proc_mode": proc_mode,
        "outputs": outputs,
        "reference": sp_lstf_fnp01_reference(),
        "checkpoint": checkpoint,
        "duration_seconds": round(time.time() - start_time, 2),
        "skipped": False,
    }

    print(
        f"[LSTF FNP01] Finished in {result['duration_seconds']}s",
        flush=True,
    )

    return result
