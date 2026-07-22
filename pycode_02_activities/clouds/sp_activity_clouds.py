"""
Clouds activity processing.

This activity is intentionally thin: it delegates the actual product work to
MCMIPF product-level processors and only decides which FNPs are needed for the
operative or viewer use case.
"""

import time
from pathlib import Path

from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01 import (
    sp_mcmipf_fnp01,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02 import (
    sp_mcmipf_fnp02,
)


def sp_activity_clouds(
    mcmipf_nc_path,
    output_dir,
    proc_mode="viewer",
    mcmipf_output_dir=None,
    mcmipf_fnp01_output_dir=None,
    mcmipf_fnp02_output_dir=None,
    overwrite=False,
):
    """
    Process the Clouds activity from one ABI-L2-MCMIPF NetCDF file.

    Parameters
    ----------
    mcmipf_nc_path : str or pathlib.Path
        ABI-L2-MCMIPF NetCDF file.
    output_dir : str or pathlib.Path
        Base output directory used when ``mcmipf_output_dir`` is not provided.
    proc_mode : {"operative", "viewer", "full"}
        Operative generates WGS84 only. Viewer/full generate GOES original,
        WGS84, and Mercator.
    mcmipf_output_dir : str or pathlib.Path, optional
        Shared product output directory for MCMIPF. Kept for backward
        compatibility and operative temporary processing.
    mcmipf_fnp01_output_dir, mcmipf_fnp02_output_dir : str or pathlib.Path, optional
        FNP-specific product output directories. Use these when persistent
        outputs should stay separated by FNP in ``data_proc``.
    overwrite : bool
        If True, regenerate existing product outputs.
    """

    start_time = time.time()
    proc_mode = str(proc_mode).strip().lower()
    output_dir = Path(output_dir)

    if proc_mode not in {"operative", "viewer", "full"}:
        raise ValueError(
            "Unsupported proc_mode for Clouds activity: "
            f"{proc_mode}. Use 'operative', 'viewer', or 'full'."
        )

    if mcmipf_output_dir is None:
        mcmipf_output_dir = output_dir / "ABI_L2_MCMIPF"
    else:
        mcmipf_output_dir = Path(mcmipf_output_dir)

    fnp01_output_dir = (
        Path(mcmipf_fnp01_output_dir)
        if mcmipf_fnp01_output_dir is not None
        else mcmipf_output_dir
    )
    fnp02_output_dir = (
        Path(mcmipf_fnp02_output_dir)
        if mcmipf_fnp02_output_dir is not None
        else mcmipf_output_dir
    )

    print("[ACTIVITY Clouds] Processing MCMIPF FNP01.", flush=True)
    fnp01_result = sp_mcmipf_fnp01(
        nc_path=mcmipf_nc_path,
        output_dir=fnp01_output_dir,
        proc_mode=proc_mode,
        overwrite=overwrite,
    )

    print("[ACTIVITY Clouds] Processing MCMIPF FNP02.", flush=True)
    fnp02_result = sp_mcmipf_fnp02(
        nc_path=mcmipf_nc_path,
        output_dir=fnp02_output_dir,
        proc_mode=proc_mode,
        overwrite=overwrite,
    )

    result = {
        "activity": "clouds",
        "proc_mode": proc_mode,
        "mcmipf": {
            "fnp01": fnp01_result,
            "fnp02": fnp02_result,
        },
        "duration_seconds": round(time.time() - start_time, 2),
    }

    print(
        f"[ACTIVITY Clouds] Finished in {result['duration_seconds']}s",
        flush=True,
    )

    return result
