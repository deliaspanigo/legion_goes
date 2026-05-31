"""
Path:
legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f03_pipelines/ABI_L2_FDCF/pipeline_ABI_L2_FDCF.py

Version: 0.0.2
Description:
    Pipeline/orquestador para ABI-L2-FDCF.

    Este pipeline:
    - Recibe un nc_path y una folder data_proc.
    - Crea una folder _control al same nivel que las folders FNP.
    - Runs una o varias FNPs.
    - Por ahour soporta fnp01.
    - Guarda logs clean en cada ejecucin.
    - Genera manifest.json para que R/Shiny pueda leer qu pas.
    - No depende de Path.cwd() para definir outputs.

Estructura esperada:

data_proc/
  sp01_single/
    noaa-goes19-EAST/
      ABI-L2-FDCF/
        2026/
          003/
            12/
              s20260031200230/
                ABI-L2-FDCF_fnp01/
                  outputs...
                _control/
                  manifest.json
                  pipeline.log
                  error.log
                  fnp01.log
"""

# =========================================================================================================================================
#  Execution:
#  python -m legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f03_pipelines.ABI_L2_FDCF.pipeline_ABI_L2_FDCF
# =========================================================================================================================================


# =============================================================================
# Libraries
# =============================================================================

import json
import re
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Dict, Any, List


# =============================================================================
# Local libraries
# =============================================================================

from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import (
    get_position_by_sat_id,
)

from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.ABI_L2_FDCF.runner_ABI_L2_FDCF_fnp01 import (
    gen_dict_path_output as gen_dict_path_output_fnp01,
    run_runner_ABI_L2_FDCF_fnp01,
)



# =============================================================================
# Small helpers
# =============================================================================

class Tee:
    """
    Writes to multiple streams at the same time.
    Useful to keep terminal output and save logs to files.
    """

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


def now_seconds() -> float:
    return time.time()


def ensure_dir(path_obj: Path) -> Path:
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def safe_unix_path(path_obj) -> str:
    return str(Path(path_obj).resolve()).replace("\\", "/")


def parse_goes_nc_file(nc_path) -> Dict[str, str]:
    """
    Parse minimal metadata from a GOES filename.

    Example:
    OR_ABI-L2-FDCF-M6_G19_s20260031200230_e20260031209539_c20260031214569.nc
    """

    nc_file_name = Path(nc_path).name

    match = re.search(
        r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})",
        nc_file_name,
    )

    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    product = match.group("prod")
    satellite = match.group("sat")
    satellite_number = satellite[1:]
    start_timestamp = match.group("start")
    start_timestamp_mod = f"s{start_timestamp}"
    position = get_position_by_sat_id(sat_id=satellite_number)

    year = start_timestamp[0:4]
    day = start_timestamp[4:7]
    hour = start_timestamp[7:9]

    bucket = f"noaa-goes{satellite_number}"
    bucket_position = f"{bucket}-{position}"

    return {
        "nc_file_name": nc_file_name,
        "product": product,
        "satellite": satellite,
        "satellite_number": satellite_number,
        "position": position,
        "start_timestamp": start_timestamp,
        "start_timestamp_mod": start_timestamp_mod,
        "year": year,
        "day": day,
        "hour": hour,
        "bucket": bucket,
        "bucket_position": bucket_position,
    }


def gen_timestamp_folder(nc_path, data_proc_dir) -> Path:
    """
    Folder that groups all FNPs and _control for one timestamp.

    data_proc/sp01_single/noaa-goes19-EAST/ABI-L2-FDCF/YYYY/DDD/HH/sYYYYDDDHHMMSS
    """

    info = parse_goes_nc_file(nc_path)

    return (
        Path(data_proc_dir).resolve()
        / "sp01_single"
        / info["bucket_position"]
        / info["product"]
        / info["year"]
        / info["day"]
        / info["hour"]
        / info["start_timestamp_mod"]
    )


def gen_control_folder(nc_path, data_proc_dir, control_folder_name="_control") -> Path:
    return gen_timestamp_folder(nc_path, data_proc_dir) / control_folder_name


def path_status(path_obj: Path) -> Dict[str, Any]:
    exists = path_obj.exists()
    is_file = path_obj.is_file() if exists else False
    size_bytes = path_obj.stat().st_size if exists and is_file else None
    mtime = path_obj.stat().st_mtime if exists else None

    return {
        "path": safe_unix_path(path_obj),
        "file_name": path_obj.name,
        "exists": exists,
        "is_file": is_file,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / 1024**2, 4) if size_bytes is not None else None,
        "valid": bool(exists and is_file and size_bytes and size_bytes > 0),
        "mtime": mtime,
    }


def output_status_from_dict(dict_path_output: Dict[str, Path]) -> Dict[str, Dict[str, Any]]:
    return {
        key: path_status(path_obj)
        for key, path_obj in dict_path_output.items()
    }


def missing_output_keys(outputs_status: Dict[str, Dict[str, Any]]) -> List[str]:
    return [
        key
        for key, value in outputs_status.items()
        if not value.get("valid", False)
    ]


def write_json(path_obj: Path, obj: Dict[str, Any]) -> None:
    ensure_dir(path_obj.parent)

    with open(path_obj, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# =============================================================================
# FNP execution layer
# =============================================================================

def run_fnp01_for_pipeline(nc_path, data_proc_dir, overwrite=False) -> Dict[str, Any]:
    """
    Wrapper around runner FNP01.

    This keeps the pipeline manifest independent from the runner internal prints.
    """

    start = now_seconds()

    dict_path_output = gen_dict_path_output_fnp01(
        nc_path=nc_path,
        str_folder_path_data_proc=data_proc_dir,
    )

    outputs_before = output_status_from_dict(dict_path_output)
    missing_before = missing_output_keys(outputs_before)

    success = False
    error = None

    try:
        success = run_runner_ABI_L2_FDCF_fnp01(
            nc_path=nc_path,
            str_folder_path_data_proc=data_proc_dir,
            overwrite=overwrite,
        )

    except Exception:
        success = False
        error = traceback.format_exc()

    outputs_after = output_status_from_dict(dict_path_output)
    missing_after = missing_output_keys(outputs_after)

    if success and len(missing_after) == 0:
        if len(missing_before) == 0 and not overwrite:
            status = "skipped_existing"
        else:
            status = "processed_complete"

    elif success and len(missing_after) > 0:
        status = "processed_incomplete"

        if error is None:
            error = (
                "Runner returned True, but mandatory outputs are missing or empty. "
                f"Missing outputs after processing: {missing_after}"
            )

    else:
        status = "error"

        if error is None:
            error = (
                "Runner returned False. "
                "Check fnp01.log for the real processing error. "
                f"Missing outputs after processing: {missing_after}"
            )

    return {
        "fnp_id": "fnp01",
        "success": bool(success and len(missing_after) == 0),
        "status": status,
        "overwrite": bool(overwrite),
        "duration_seconds": round(now_seconds() - start, 3),
        "missing_before": missing_before,
        "missing_after": missing_after,
        "outputs_before": outputs_before,
        "outputs_after": outputs_after,
        "error": error,
    }


# Registry preparado para futuras FNPs.
FNP_REGISTRY = {
    "fnp01": run_fnp01_for_pipeline,
}


# =============================================================================
# Main pipeline
# =============================================================================

def run_pipeline_ABI_L2_FDCF(
    nc_path,
    data_proc_dir,
    overwrite=False,
    fnps=None,
    control_folder_name="_control",
    echo_logs=True,
) -> Dict[str, Any]:
    """
    Orchestrates one or more FDCF FNPs.

    Parameters
    ----------
    nc_path : str or Path
        Input .nc file.

    data_proc_dir : str or Path
        Root data_proc folder.

    overwrite : bool
        Passed to each FNP runner.

    fnps : list[str] or None
        FNP list. Default: ["fnp01"].

    control_folder_name : str
        Name of the control folder. Default: "_control".

    echo_logs : bool
        If True, logs are printed to terminal and written to files.
        If False, logs are only written to files.

    Returns
    -------
    dict
        Manifest dictionary.
    """

    if fnps is None:
        fnps = ["fnp01"]

    nc_path = Path(nc_path).resolve()
    data_proc_dir = Path(data_proc_dir).resolve()

    if not nc_path.exists():
        raise FileNotFoundError(f"NC file does not exist: {nc_path}")

    if not nc_path.is_file():
        raise ValueError(f"NC path is not a file: {nc_path}")

    ensure_dir(data_proc_dir)

    info = parse_goes_nc_file(nc_path)
    timestamp_folder = gen_timestamp_folder(nc_path, data_proc_dir)

    control_folder = gen_control_folder(
        nc_path=nc_path,
        data_proc_dir=data_proc_dir,
        control_folder_name=control_folder_name,
    )

    ensure_dir(timestamp_folder)
    ensure_dir(control_folder)

    manifest_path = control_folder / "manifest.json"
    pipeline_log_path = control_folder / "pipeline.log"
    error_log_path = control_folder / "error.log"

    start = now_seconds()

    manifest: Dict[str, Any] = {
        "success": False,
        "status": "running",
        "product": info["product"],
        "satellite": info["satellite"],
        "satellite_number": info["satellite_number"],
        "position": info["position"],
        "timestamp_start": info["start_timestamp_mod"],
        "year": info["year"],
        "day": info["day"],
        "hour": info["hour"],
        "nc_file_name": info["nc_file_name"],
        "nc_path": safe_unix_path(nc_path),
        "data_proc_dir": safe_unix_path(data_proc_dir),
        "timestamp_folder": safe_unix_path(timestamp_folder),
        "control_folder": safe_unix_path(control_folder),
        "manifest_path": safe_unix_path(manifest_path),
        "pipeline_log_path": safe_unix_path(pipeline_log_path),
        "error_log_path": safe_unix_path(error_log_path),
        "overwrite": bool(overwrite),
        "fnp_requested": fnps,
        "fnp_completed": [],
        "fnp_skipped": [],
        "fnp_failed": [],
        "fnp_results": {},
        "outputs": {},
        "missing_outputs": {},
        "duration_seconds": None,
        "error": None,
    }

    write_json(manifest_path, manifest)

    try:
        # Important:
        # Use "w", not "a".
        # This avoids mixing previous attempts with the current run.
        with open(pipeline_log_path, "w", encoding="utf-8") as pipeline_log, \
             open(error_log_path, "w", encoding="utf-8") as error_log:

            stdout_target = Tee(sys.stdout, pipeline_log) if echo_logs else pipeline_log
            stderr_target = Tee(sys.stderr, error_log) if echo_logs else error_log

            with redirect_stdout(stdout_target), redirect_stderr(stderr_target):

                print("\n" + " FDCF PIPELINE ".center(80, "="))
                print(f"NC:              {nc_path}")
                print(f"DATA_PROC:       {data_proc_dir}")
                print(f"TIMESTAMP_DIR:   {timestamp_folder}")
                print(f"CONTROL_DIR:     {control_folder}")
                print(f"OVERWRITE:       {overwrite}")
                print(f"FNP REQUESTED:   {fnps}")
                print("-" * 80)

                for fnp_id in fnps:

                    print(f"\n{' Running ' + fnp_id + ' ':=^80}")

                    fnp_log_path = control_folder / f"{fnp_id}.log"

                    if fnp_id not in FNP_REGISTRY:
                        fnp_result = {
                            "fnp_id": fnp_id,
                            "success": False,
                            "status": "not_implemented",
                            "overwrite": bool(overwrite),
                            "duration_seconds": 0,
                            "outputs_before": {},
                            "outputs_after": {},
                            "missing_before": [],
                            "missing_after": [],
                            "error": f"{fnp_id} is not implemented in FNP_REGISTRY.",
                            "log_path": safe_unix_path(fnp_log_path),
                        }

                    else:
                        # Important:
                        # Use "w", not "a".
                        # This gives a clean fnp log for every execution.
                        with open(fnp_log_path, "w", encoding="utf-8") as fnp_log:

                            fnp_stdout = Tee(sys.stdout, fnp_log) if echo_logs else fnp_log

                            with redirect_stdout(fnp_stdout):
                                fnp_result = FNP_REGISTRY[fnp_id](
                                    nc_path=nc_path,
                                    data_proc_dir=data_proc_dir,
                                    overwrite=overwrite,
                                )

                            fnp_result["log_path"] = safe_unix_path(fnp_log_path)

                    manifest["fnp_results"][fnp_id] = fnp_result
                    manifest["outputs"][fnp_id] = fnp_result.get("outputs_after", {})
                    manifest["missing_outputs"][fnp_id] = fnp_result.get("missing_after", [])

                    if fnp_result.get("success") is True:
                        if fnp_result.get("status") == "skipped_existing":
                            manifest["fnp_skipped"].append(fnp_id)
                        else:
                            manifest["fnp_completed"].append(fnp_id)

                    else:
                        manifest["fnp_failed"].append(fnp_id)

                    write_json(manifest_path, manifest)

                if manifest["fnp_failed"]:
                    manifest["success"] = False
                    manifest["status"] = "error_or_incomplete"

                    failed_errors = []

                    for fnp_id in manifest["fnp_failed"]:
                        fnp_res = manifest["fnp_results"].get(fnp_id, {})
                        fnp_error = fnp_res.get("error")
                        fnp_missing = fnp_res.get("missing_after", [])
                        fnp_log = fnp_res.get("log_path")

                        failed_errors.append(
                            {
                                "fnp_id": fnp_id,
                                "status": fnp_res.get("status"),
                                "error": fnp_error,
                                "missing_after": fnp_missing,
                                "log_path": fnp_log,
                            }
                        )

                    manifest["error"] = (
                        "One or more FNPs failed or are incomplete. "
                        "See fnp_results for details."
                    )

                    manifest["failed_details"] = failed_errors

                else:
                    manifest["success"] = True

                    if manifest["fnp_completed"]:
                        manifest["status"] = "processed"

                    elif manifest["fnp_skipped"]:
                        manifest["status"] = "skipped_existing"

                    else:
                        manifest["status"] = "no_action"

                    manifest["error"] = None

                manifest["duration_seconds"] = round(now_seconds() - start, 3)

                print("\n" + "-" * 80)
                print(f"PIPELINE STATUS: {manifest['status']}")
                print(f"SUCCESS:         {manifest['success']}")
                print(f"DURATION:        {manifest['duration_seconds']} s")
                print(f"MANIFEST:        {manifest_path}")

                if manifest.get("error"):
                    print(f"ERROR:           {manifest.get('error')}")

                print("=" * 80)

                write_json(manifest_path, manifest)

    except Exception:
        manifest["success"] = False
        manifest["status"] = "pipeline_exception"
        manifest["error"] = traceback.format_exc()
        manifest["duration_seconds"] = round(now_seconds() - start, 3)

        with open(error_log_path, "w", encoding="utf-8") as error_log:
            error_log.write(manifest["error"])
            error_log.write("\n")

        write_json(manifest_path, manifest)

    return manifest


# =============================================================================
# SIMPLE MAIN (Terminal & Diagnostic)
# =============================================================================

if __name__ == "__main__":

    print("\n" + " FDCF PIPELINE: DIAGNOSTIC TEST ".center(80, "="))

    # -------------------------------------------------------------------------
    # 1. Execution folders
    # -------------------------------------------------------------------------

    folder_data_raw = Path.cwd() / "data_raw"
    folder_data_proc = Path.cwd() / "data_proc"

    print(f"DATA_RAW:  {folder_data_raw}")
    print(f"DATA_PROC: {folder_data_proc}")
    print("-" * 80)

    # -------------------------------------------------------------------------
    # 2. Look recursively for the first .nc file containing 'FDCF'
    # -------------------------------------------------------------------------

    nc_candidates = sorted(list(folder_data_raw.rglob("*FDCF*.nc")))

    if not nc_candidates:

        print(f" Error: No .nc files with 'FDCF' found in: {folder_data_raw}")

    else:

        target_nc = nc_candidates[0]

        print(f" FILE: {target_nc}")
        print("-" * 80)

        # ---------------------------------------------------------------------
        # 3. Run pipeline
        # ---------------------------------------------------------------------

        manifest = run_pipeline_ABI_L2_FDCF(
            nc_path=target_nc,
            data_proc_dir=folder_data_proc,
            overwrite=True,
            fnps=["fnp01"],
        )

        # ---------------------------------------------------------------------
        # 4. Final status
        # ---------------------------------------------------------------------

        if manifest.get("success") is True:

            print("-" * 80)
            print(" PIPELINE TEST COMPLETED")
            print(f"STATUS:   {manifest.get('status')}")
            print(f"MANIFEST: {manifest.get('manifest_path')}")
            print("=" * 80)

        else:

            print("-" * 80)
            print(" PIPELINE TEST FAILED")
            print(f"STATUS:   {manifest.get('status')}")
            print(f"ERROR:    {manifest.get('error')}")
            print(f"MANIFEST: {manifest.get('manifest_path')}")

            failed_details = manifest.get("failed_details")

            if failed_details:
                print("FAILED DETAILS:")
                print(json.dumps(failed_details, indent=2, ensure_ascii=False))

            print("=" * 80)