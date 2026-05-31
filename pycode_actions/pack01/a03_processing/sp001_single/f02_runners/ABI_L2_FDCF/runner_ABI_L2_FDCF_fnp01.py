"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f02_runners/ABI_L2_FDCF/runner_ABI_L2_FDCF_fnp01.py
Version: 0.0.3
Description: Runner - ABI-L2-FDCF FNP01 with explicit data_proc path and output validation.
"""

import re
from pathlib import Path

from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_FDCF.proc_ABI_L2_FDCF_fnp01 import (
    gen_dict_output_file_name,
    run_proc_ABI_L2_FDCF_fnp01,
)
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import (
    get_position_by_sat_id,
)


def gen_str_folder_output(nc_path):
    """
    Parses the NC filename to generate a hierarchical output folder structure.

    Important:
    This returned path is relative to data_proc.
    It must NOT include Path("data_proc").
    """

    nc_file_name = Path(nc_path).name
    match = re.search(
        r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})",
        nc_file_name,
    )

    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    str_prod = match.group("prod")
    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start")
    str_stimestamp_mod = f"s{str_stimestamp}"
    str_position = get_position_by_sat_id(sat_id=str_sat_number)

    str_year = str_stimestamp[0:4]
    str_day = str_stimestamp[4:7]
    str_hour = str_stimestamp[7:9]

    str_bucket = "noaa-goes" + str_sat_number
    str_bucket_mod = f"{str_bucket}-{str_position}"
    str_prod_fnp = str_prod + "_fnp01"

    return (
        Path("sp01_single")
        / str_bucket_mod
        / str_prod
        / str_year
        / str_day
        / str_hour
        / str_stimestamp_mod
        / str_prod_fnp
    )


def gen_dict_path_output(nc_path, str_folder_path_data_proc=None):
    """
    Creates the output directory and maps schema filenames to full Path objects.
    """

    if str_folder_path_data_proc is None:
        raise ValueError("str_folder_path_data_proc is required")

    nc_path = Path(nc_path)
    data_proc_dir = Path(str_folder_path_data_proc).expanduser().resolve()

    if data_proc_dir.exists() and not data_proc_dir.is_dir():
        raise ValueError(f"str_folder_path_data_proc exists but is not a folder: {data_proc_dir}")

    data_proc_dir.mkdir(parents=True, exist_ok=True)

    output_folder_path = data_proc_dir / gen_str_folder_output(nc_path)
    output_folder_path.mkdir(parents=True, exist_ok=True)

    dict_output_file_name = gen_dict_output_file_name(nc_path=str(nc_path))

    return {
        key: output_folder_path / file_name
        for key, file_name in dict_output_file_name.items()
    }


def get_missing_or_empty_outputs(output_dict: dict) -> dict:
    missing = {}

    for key, path_obj in output_dict.items():
        path_obj = Path(path_obj)

        if not path_obj.exists() or not path_obj.is_file() or path_obj.stat().st_size == 0:
            missing[key] = path_obj

    return missing


def is_processing_complete(output_dict: dict) -> bool:
    return len(get_missing_or_empty_outputs(output_dict)) == 0


def count_valid_outputs(output_dict: dict) -> int:
    n = 0

    for path_obj in output_dict.values():
        path_obj = Path(path_obj)
        if path_obj.exists() and path_obj.is_file() and path_obj.stat().st_size > 0:
            n += 1

    return n


def run_runner_ABI_L2_FDCF_fnp01(nc_path, str_folder_path_data_proc=None, overwrite=False):
    """
    Main runner logic: manages skip-logic, cleanup, core execution,
    and final validation of expected outputs.
    """

    nc_path = Path(nc_path).expanduser().resolve()

    if not nc_path.exists():
        raise FileNotFoundError(f"NC file does not exist: {nc_path}")

    if not nc_path.is_file():
        raise ValueError(f"nc_path is not a file: {nc_path}")

    dict_path_output = gen_dict_path_output(
        nc_path=nc_path,
        str_folder_path_data_proc=str_folder_path_data_proc,
    )

    total_expected = len(dict_path_output)
    exists_count = count_valid_outputs(dict_path_output)
    all_exist = is_processing_complete(dict_path_output)

    if all_exist and not overwrite:
        print(f"  [SKIPPED]     {nc_path.name} (All {total_expected} outputs exist)")
        return True

    if overwrite and all_exist:
        reason = "OVERWRITE (Forced by user)"
    elif exists_count > 0:
        reason = f"INCOMPLETE ({exists_count}/{total_expected} valid files found, fixing...)"
    else:
        reason = "NEW (No previous valid outputs found)"

    print(f"  [PROCESSING]  {nc_path.name}")
    print(f"                Reason: {reason}")

    for path_obj in dict_path_output.values():
        path_obj = Path(path_obj)
        if path_obj.exists() and path_obj.is_file():
            path_obj.unlink()

    dict_str_paths = {
        key: str(path_obj)
        for key, path_obj in dict_path_output.items()
    }

    try:
        success = run_proc_ABI_L2_FDCF_fnp01(
            nc_path=str(nc_path),
            **dict_str_paths,
        )
    except Exception as e:
        print(f"  [ERROR] Error processing {nc_path.name}: {e}")
        return False

    if not success:
        print(f"  [FAILED]      {nc_path.name}")
        print("                Core function returned False.")
        return False

    missing_after = get_missing_or_empty_outputs(dict_path_output)

    if missing_after:
        print(f"  [INCOMPLETE]  {nc_path.name}")
        print("                Missing or empty expected outputs:")
        for key, path_obj in missing_after.items():
            print(f"                - {key}: {path_obj}")
        return False

    print(f"  [COMPLETED]   {nc_path.name}")
    print(f"                All {total_expected} expected outputs exist and are not empty.")
    return True


if __name__ == "__main__":
    print("\n" + " Runner FDCF FNP01: DIAGNOSTIC TEST ".center(80, "="))

    folder_data_raw = Path.cwd() / "data_raw"
    folder_data_proc = Path.cwd() / "data_proc"

    print(f"DATA_RAW:  {folder_data_raw}")
    print(f"DATA_PROC: {folder_data_proc}")
    print("-" * 80)

    nc_candidates = sorted([
        p for p in folder_data_raw.rglob("*.nc")
        if "FDCF" in p.name.upper()
    ])

    if not nc_candidates:
        print(f"[ERROR] No .nc files with FDCF found in: {folder_data_raw}")
    else:
        target_nc = nc_candidates[0]
        print(f"[INFO] FILE: {target_nc}")
        print("-" * 80)
        success = run_runner_ABI_L2_FDCF_fnp01(
            nc_path=target_nc,
            str_folder_path_data_proc=folder_data_proc,
            overwrite=True,
        )
        print("-" * 80)
        print("[OK] TEST COMPLETED" if success else "[ERROR] TEST FAILED")
        print("=" * 80)
