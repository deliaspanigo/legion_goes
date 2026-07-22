"""
Electrical Storms activity processing.

This activity keeps the product-level outputs separated in data_proc while
coordinating the files that belong to the same storm visualization frame:

- MCMIPF FNP01: True Color / visual context.
- MCMIPF FNP02: cloud and infrared context.
- GLM-L2-LCFA FNP02: flashes aggregated in the clean 10-minute block anchored
  to the MCMIPF frame.
"""

import time
from pathlib import Path

from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp01 import (
    sp_mcmipf_fnp01,
)
from legion_goes.pycode_01_products.ABI_L2_MCMIPF.sp_mcmipf_fnp02 import (
    sp_mcmipf_fnp02,
)
from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.GLM_L2_LCFA.runner_GLM_L2_LCFA_fnp02 import (
    run_runner_GLM_L2_LCFA_fnp02,
)


def sp_activity_electrical_storms(
    mcmipf_nc_path,
    glm_nc_paths,
    output_dir,
    data_proc_dir,
    proc_mode="viewer",
    mcmipf_output_dir=None,
    mcmipf_fnp01_output_dir=None,
    mcmipf_fnp02_output_dir=None,
    matching_mode="ten_minute_block",
    overwrite=False,
):
    """
    Process one Electrical Storms activity frame.

    Parameters
    ----------
    mcmipf_nc_path : str or pathlib.Path
        ABI-L2-MCMIPF NetCDF file used as the storm window anchor.
    glm_nc_paths : list[str | pathlib.Path]
        Candidate GLM-L2-LCFA NetCDF files. The GLM processor keeps only the
        files matching ``matching_mode``.
    output_dir : str or pathlib.Path
        Activity metadata directory. Product outputs remain in their product
        folders unless explicit output directories are supplied.
    data_proc_dir : str or pathlib.Path
        Root data_proc directory used by the GLM runner for product outputs.
    proc_mode : {"operative", "viewer", "full"}
        MCMIPF processing mode. Viewer/full generate all viewer projections;
        operative is WGS84 focused.
    mcmipf_output_dir : str or pathlib.Path, optional
        Shared fallback MCMIPF output directory.
    mcmipf_fnp01_output_dir, mcmipf_fnp02_output_dir : str or pathlib.Path, optional
        FNP-specific MCMIPF output directories.
    matching_mode : str
        GLM-MCMIPF matching mode. The default ``ten_minute_block`` uses the
        clean UTC block assigned to the MCMIPF start time.
    overwrite : bool
        If True, regenerate existing outputs.
    """

    start_time = time.time()
    proc_mode = str(proc_mode).strip().lower()
    output_dir = Path(output_dir)
    data_proc_dir = Path(data_proc_dir)
    mcmipf_nc_path = Path(mcmipf_nc_path)
    glm_nc_paths = [Path(path) for path in glm_nc_paths]

    if proc_mode not in {"operative", "viewer", "full"}:
        raise ValueError(
            "Unsupported proc_mode for Electrical Storms activity: "
            f"{proc_mode}. Use 'operative', 'viewer', or 'full'."
        )

    if not glm_nc_paths:
        raise ValueError("Electrical Storms activity needs at least one GLM file.")

    output_dir.mkdir(parents=True, exist_ok=True)

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

    print("[ACTIVITY Electrical Storms] Processing MCMIPF FNP01.", flush=True)
    fnp01_result = sp_mcmipf_fnp01(
        nc_path=mcmipf_nc_path,
        output_dir=fnp01_output_dir,
        proc_mode=proc_mode,
        overwrite=overwrite,
    )

    print("[ACTIVITY Electrical Storms] Processing MCMIPF FNP02.", flush=True)
    fnp02_result = sp_mcmipf_fnp02(
        nc_path=mcmipf_nc_path,
        output_dir=fnp02_output_dir,
        proc_mode=proc_mode,
        overwrite=overwrite,
    )

    print(
        "[ACTIVITY Electrical Storms] Processing GLM FNP02 "
        f"with {len(glm_nc_paths)} candidate files.",
        flush=True,
    )
    glm_success = run_runner_GLM_L2_LCFA_fnp02(
        mcmipf_nc_path=mcmipf_nc_path,
        glm_nc_paths=glm_nc_paths,
        str_folder_path_data_proc=data_proc_dir,
        overwrite=overwrite,
        matching_mode=matching_mode,
    )

    if not glm_success:
        raise RuntimeError("GLM FNP02 processing failed for the storm window.")

    result = {
        "activity": "electrical_storms",
        "proc_mode": proc_mode,
        "matching_mode": matching_mode,
        "mcmipf": {
            "fnp01": fnp01_result,
            "fnp02": fnp02_result,
        },
        "glm": {
            "fnp02_success": bool(glm_success),
            "candidate_files": len(glm_nc_paths),
        },
        "duration_seconds": round(time.time() - start_time, 2),
    }

    print(
        f"[ACTIVITY Electrical Storms] Finished in {result['duration_seconds']}s",
        flush=True,
    )

    return result