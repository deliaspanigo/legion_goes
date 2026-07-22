"""
FDCF FNP01 simple processing orchestrator.

This is the human-friendly entry point for Fire Detection FNP01. It delegates
the raster work to one function per reference system, and keeps reference and
point products as explicit side products.
"""

import time

from legion_goes.pycode_01_products.common import processing_checkpoint
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_fire_points import (
    extract_fdcf_fire_points,
    sp_fdcf_fnp01_fire_points,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_fire_points_png import (
    sp_fdcf_fnp01_fire_points_png,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_goes_original import (
    sp_fdcf_fnp01_goes_original,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_mercator import (
    sp_fdcf_fnp01_mercator,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_reference import (
    sp_fdcf_fnp01_reference,
    write_fdcf_reference_csv,
    write_fdcf_reference_json,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_schema import (
    FDCF_COLOR_VARIANTS,
    sp_fdcf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_wgs84 import (
    sp_fdcf_fnp01_wgs84,
)


def _write_reference_outputs(nc_path, output_dir):
    outputs = sp_fdcf_fnp01_output_schema(nc_path, output_dir)
    result = {}

    print("[FDCF FNP01 Reference] Writing FDCF reference tables...", flush=True)

    for color_name in FDCF_COLOR_VARIANTS:
        full_csv_key = f"{color_name}_reference_full_csv"
        full_json_key = f"{color_name}_reference_full_json"
        active_csv_key = f"{color_name}_reference_active_csv"
        active_json_key = f"{color_name}_reference_active_json"

        write_fdcf_reference_csv(
            output=outputs[full_csv_key],
            variant=color_name,
            nc_path=nc_path,
            active_only=False,
        )
        write_fdcf_reference_json(
            output=outputs[full_json_key],
            variant=color_name,
            nc_path=nc_path,
            active_only=False,
        )
        write_fdcf_reference_csv(
            output=outputs[active_csv_key],
            variant=color_name,
            nc_path=nc_path,
            active_only=True,
        )
        write_fdcf_reference_json(
            output=outputs[active_json_key],
            variant=color_name,
            nc_path=nc_path,
            active_only=True,
        )

        result[full_csv_key] = outputs[full_csv_key]
        result[full_json_key] = outputs[full_json_key]
        result[active_csv_key] = outputs[active_csv_key]
        result[active_json_key] = outputs[active_json_key]

    return result


def _expected_fdcf_fnp01_outputs(nc_path, output_dir, proc_mode):
    schema = sp_fdcf_fnp01_output_schema(nc_path, output_dir)
    expected = {}

    if proc_mode in {"viewer", "full"}:
        expected.update({key: value for key, value in schema.items() if key.startswith("goes_native_")})

    expected.update({key: value for key, value in schema.items() if key.startswith("wgs84_")})

    if proc_mode in {"viewer", "full"}:
        expected.update({key: value for key, value in schema.items() if key.startswith("mercator_")})

    expected.update({key: value for key, value in schema.items() if "fire_points" in key})
    expected.update({key: value for key, value in schema.items() if "reference_" in key})

    return expected


def sp_fdcf_fnp01(nc_path, output_dir, proc_mode="viewer", overwrite=False):
    """
    Run FDCF FNP01 according to a processing mode.

    If all expected outputs for the selected ``proc_mode`` already exist and
    ``overwrite`` is False, processing is skipped. If the set is incomplete,
    existing partial outputs are removed and the FNP is processed again.
    """

    start_time = time.time()
    proc_mode = str(proc_mode).strip().lower()
    outputs = {}

    print(f"[FDCF FNP01] Processing mode: {proc_mode}", flush=True)

    if proc_mode not in {"operative", "viewer", "full"}:
        raise ValueError(
            "Unsupported proc_mode for FDCF FNP01: "
            f"{proc_mode}. Use 'operative', 'viewer', or 'full'."
        )

    expected_outputs = _expected_fdcf_fnp01_outputs(nc_path, output_dir, proc_mode)
    checkpoint = processing_checkpoint(
        "FDCF FNP01",
        expected_outputs=expected_outputs,
        overwrite=overwrite,
    )

    if checkpoint["action"] == "skip":
        result = {
            "product": "ABI-L2-FDCF",
            "fnp": "fnp01",
            "proc_mode": proc_mode,
            "outputs": expected_outputs,
            "reference": sp_fdcf_fnp01_reference(),
            "checkpoint": checkpoint,
            "duration_seconds": round(time.time() - start_time, 2),
            "skipped": True,
        }
        print(f"[FDCF FNP01] Skipped in {result['duration_seconds']}s", flush=True)
        return result

    if proc_mode in {"viewer", "full"}:
        outputs.update(sp_fdcf_fnp01_goes_original(nc_path, output_dir))

    outputs.update(sp_fdcf_fnp01_wgs84(nc_path, output_dir))

    if proc_mode in {"viewer", "full"}:
        outputs.update(sp_fdcf_fnp01_mercator(nc_path, output_dir))

    fire_points = extract_fdcf_fire_points(nc_path)
    outputs.update(sp_fdcf_fnp01_fire_points(nc_path, output_dir, fire_points=fire_points))
    outputs.update(
        sp_fdcf_fnp01_fire_points_png(
            nc_path,
            output_dir,
            proc_mode=proc_mode,
            fire_points=fire_points,
        )
    )
    outputs.update(_write_reference_outputs(nc_path, output_dir))

    result = {
        "product": "ABI-L2-FDCF",
        "fnp": "fnp01",
        "proc_mode": proc_mode,
        "outputs": outputs,
        "reference": sp_fdcf_fnp01_reference(),
        "checkpoint": checkpoint,
        "duration_seconds": round(time.time() - start_time, 2),
        "skipped": False,
    }

    print(
        f"[FDCF FNP01] Finished in {result['duration_seconds']}s",
        flush=True,
    )

    return result
