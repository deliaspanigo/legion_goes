"""
Surface Temperature activity processing.

This is the activity-level entry point that R/Shiny should call in the future.
It combines the product-level processors needed for the Temperature viewer and
operative apps.

The activity is intentionally simple:
  - LSTF is the main science product.
  - MCMIPF FNP01 is an optional True Color background.
"""

import time
from pathlib import Path

from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01 import (
    sp_lstf_fnp01,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01 import (
    sp_mcmipf_fnp01,
)


def sp_activity_surface_temperature(
    lstf_nc_path,
    output_dir,
    proc_mode="viewer",
    mcmipf_nc_path=None,
    lstf_output_dir=None,
    mcmipf_output_dir=None,
    overwrite=False,
):
    """
    Process the Surface Temperature activity.

    Parameters
    ----------
    lstf_nc_path : str or Path
        ABI-L2-LSTF NetCDF file. This file is required.
    output_dir : str or Path
        Activity output directory.
    proc_mode : str
        Processing mode passed to the product processors:
        - "operative": WGS84 only.
        - "viewer": GOES original, WGS84, and Mercator.
        - "full": same as viewer for now.
    mcmipf_nc_path : str or Path, optional
        ABI-L2-MCMIPF NetCDF file used as a True Color background.
    lstf_output_dir : str or Path, optional
        Product output directory for LSTF. When omitted, an activity-local
        directory is used.
    mcmipf_output_dir : str or Path, optional
        Product output directory for MCMIPF. When omitted, an activity-local
        directory is used.
    overwrite : bool
        If True, regenerate existing product outputs.

    Returns
    -------
    dict
        Activity result with product outputs and processing metadata.
    """

    start_time = time.time()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    proc_mode = str(proc_mode).strip().lower()

    print("[ACTIVITY Surface Temperature] Starting activity.", flush=True)
    print(f"[ACTIVITY Surface Temperature] proc_mode = {proc_mode}", flush=True)

    if lstf_output_dir is None or str(lstf_output_dir).strip() == "":
        lstf_output_dir = output_dir / "ABI_L2_LSTF"
    else:
        lstf_output_dir = Path(lstf_output_dir)

    if mcmipf_output_dir is None or str(mcmipf_output_dir).strip() == "":
        mcmipf_output_dir = output_dir / "ABI_L2_MCMIPF"
    else:
        mcmipf_output_dir = Path(mcmipf_output_dir)

    result = {
        "activity": "surface_temperature",
        "proc_mode": proc_mode,
        "lstf": None,
        "mcmipf_fnp01": None,
        "mcmipf_status": "not_requested",
    }

    print("[ACTIVITY Surface Temperature] Processing LSTF FNP01.", flush=True)
    result["lstf"] = sp_lstf_fnp01(
        nc_path=lstf_nc_path,
        output_dir=lstf_output_dir,
        proc_mode=proc_mode,
        overwrite=overwrite,
    )

    if mcmipf_nc_path is not None and str(mcmipf_nc_path).strip() != "":
        print(
            "[ACTIVITY Surface Temperature] Processing MCMIPF FNP01 background.",
            flush=True,
        )
        result["mcmipf_fnp01"] = sp_mcmipf_fnp01(
            nc_path=mcmipf_nc_path,
            output_dir=mcmipf_output_dir,
            proc_mode=proc_mode,
            overwrite=overwrite,
        )
        result["mcmipf_status"] = "processed"
    else:
        print(
            "[ACTIVITY Surface Temperature] No MCMIPF file was provided. "
            "The activity will contain LSTF only.",
            flush=True,
        )

    result["duration_seconds"] = round(time.time() - start_time, 2)

    print(
        "[ACTIVITY Surface Temperature] Finished in "
        f"{result['duration_seconds']}s",
        flush=True,
    )

    return result


def sp_activity_surface_temperature_operative(
    lstf_nc_path,
    output_dir,
    mcmipf_nc_path=None,
    lstf_output_dir=None,
    mcmipf_output_dir=None,
    overwrite=False,
):
    """
    Process Surface Temperature for operative apps.

    Operative processing is intentionally fast and focused. It generates the
    WGS84 products needed to show the latest temperature scene quickly.
    """

    return sp_activity_surface_temperature(
        lstf_nc_path=lstf_nc_path,
        mcmipf_nc_path=mcmipf_nc_path,
        output_dir=output_dir,
        proc_mode="operative",
        lstf_output_dir=lstf_output_dir,
        mcmipf_output_dir=mcmipf_output_dir,
        overwrite=overwrite,
    )


def sp_activity_surface_temperature_viewer(
    lstf_nc_path,
    output_dir,
    mcmipf_nc_path=None,
    lstf_output_dir=None,
    mcmipf_output_dir=None,
    overwrite=False,
):
    """
    Process Surface Temperature for viewer apps.

    Viewer processing generates all current map reference systems used by the
    Temperature Viewer: GOES original, WGS84, and Web Mercator.
    """

    return sp_activity_surface_temperature(
        lstf_nc_path=lstf_nc_path,
        mcmipf_nc_path=mcmipf_nc_path,
        output_dir=output_dir,
        proc_mode="viewer",
        lstf_output_dir=lstf_output_dir,
        mcmipf_output_dir=mcmipf_output_dir,
        overwrite=overwrite,
    )
