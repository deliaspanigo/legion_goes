"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_MCMIPF/proc_ABI_L2_MCMIPF_fnp01.py
Version: 0.0.4
Description:
    Core processing - ABI-L2-MCMIPF FNP01.

    This FNP generates 5 mandatory files:
    - GOES native true color PNG
    - GOES native day-only PNG
    - WGS84 true color PNG
    - WGS84 day-only PNG
    - WGS84 true color GeoTIFF

    If any mandatory file cannot be generated, the function returns False.

Last modification: 31-05-2026
"""

# =========================================================================================================================================
#  Execution:
#  python -m legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_MCMIPF.proc_ABI_L2_MCMIPF_fnp01
# =========================================================================================================================================


# =============================================================================
# Libraries
# =============================================================================

import time
import gc
import re
import traceback
from pathlib import Path

from satpy import Scene
from pyresample.geometry import AreaDefinition


# =============================================================================
# Local libraries
# =============================================================================

from legion_goes.satpy_config.my_config_satpy import CACHE_DIR
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import (
    get_position_by_sat_id,
)

def gen_dict_output_file_name(nc_path):
    """
    Generates the expected output filenames for ABI-L2-MCMIPF FNP01.

    This function defines the output contract of FNP01.

    All files returned here are mandatory.
    If one of these files is not created, the runner/pipeline must consider
    the processing incomplete.
    """

    nc_file_name = Path(nc_path).name

    match = re.search(
        r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})",
        nc_file_name,
    )

    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start")
    str_position = get_position_by_sat_id(sat_id=str_sat_number)

    str_name = f"SP-01-simple_G{str_sat_number}-{str_position}-s{str_stimestamp}"

    dict_output_schema = {
        "goes_native_true_color_png": (
            f"{str_name}_CRS-Goes{str_position}_MCMIPF-fnp01-TrueColor.png"
        ),
        "goes_native_true_color_day_only_png": (
            f"{str_name}_CRS-Goes{str_position}_MCMIPF-fnp01-TrueColor-DayOnly.png"
        ),
        "wgs84_true_color_png": (
            f"{str_name}_CRS-WGS84_MCMIPF-fnp01-TrueColor.png"
        ),
        "wgs84_true_color_day_only_png": (
            f"{str_name}_CRS-WGS84_MCMIPF-fnp01-TrueColor-DayOnly.png"
        ),
        "wgs84_true_color_tif": (
            f"{str_name}_CRS-WGS84_MCMIPF-fnp01-TrueColor.tif"
        ),
    }

    return dict_output_schema


def get_required_output_keys():
    """
    Returns all mandatory output keys expected by this FNP.
    """

    return [
        "goes_native_true_color_png",
        "goes_native_true_color_day_only_png",
        "wgs84_true_color_png",
        "wgs84_true_color_day_only_png",
        "wgs84_true_color_tif",
    ]


def validate_required_kwargs(kwargs):
    """
    Validates that all mandatory output paths were provided.
    """

    missing = [
        key
        for key in get_required_output_keys()
        if key not in kwargs or kwargs.get(key) is None or str(kwargs.get(key)).strip() == ""
    ]

    if missing:
        raise ValueError(
            "Missing mandatory output path(s): " + ", ".join(missing)
        )


def validate_output_files(kwargs):
    """
    Validates that all mandatory output files exist and are not empty.
    """

    missing_or_empty = []

    for key in get_required_output_keys():
        path_obj = Path(kwargs[key])

        if not path_obj.exists():
            missing_or_empty.append((key, path_obj, "missing"))
            continue

        if not path_obj.is_file():
            missing_or_empty.append((key, path_obj, "not_a_file"))
            continue

        if path_obj.stat().st_size == 0:
            missing_or_empty.append((key, path_obj, "empty"))
            continue

    if missing_or_empty:
        msg_lines = ["Mandatory output validation failed:"]

        for key, path_obj, reason in missing_or_empty:
            msg_lines.append(f"  - {key}: {path_obj} [{reason}]")

        raise RuntimeError("\n".join(msg_lines))


# =============================================================================
# 2. DARK PIXEL MASK FUNCTION
# =============================================================================
def apply_dark_pixel_mask(data_array, threshold=0.05):
    """Filters out pixels with intensity below the threshold."""
    avg_intensity = data_array.mean(dim="bands")
    return data_array.where(avg_intensity > threshold)


# =============================================================================
# 2. CORE PROCESSING FUNCTION
# =============================================================================

def run_proc_ABI_L2_MCMIPF_fnp01(nc_path, **kwargs):
    """
    Executes FNP01 for ABI-L2-MCMIPF.

    Parameters
    ----------
    nc_path : str or Path
        Input ABI-L2-MCMIPF NetCDF file.

    **kwargs
        Mandatory output paths.

    Returns
    -------
    bool
        True if all five mandatory files were generated successfully.
        False otherwise.
    """

    start_time = time.time()
    file_path = Path(nc_path)

    prod_raw = "true_color"
    path_cache = CACHE_DIR

    resample_kwargs = {
        "cache_dir": str(path_cache),
        "nprocs": 4,
        "static_data": True,
    }

    my_chunks = {
        "y": 1024,
        "x": 1024,
    }

    scn = None
    scn_day = None
    scn_res = None
    scn_res_day = None

    try:
        # ---------------------------------------------------------------------
        # Validate inputs
        # ---------------------------------------------------------------------

        if not file_path.exists():
            raise FileNotFoundError(f"Input NetCDF does not exist: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Input path is not a file: {file_path}")

        validate_required_kwargs(kwargs)

        first_output_file_path = list(kwargs.values())[0]
        output_folder = Path(first_output_file_path).parent
        output_folder.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] output_folder = {output_folder}", flush=True)

        # ---------------------------------------------------------------------
        # Area definitions
        # ---------------------------------------------------------------------

        area_wgs84 = AreaDefinition(
            "wgs84",
            "Global WGS84",
            "epsg4326",
            "EPSG:4326",
            3600,
            1800,
            [-180, -90, 180, 90],
        )

        # ---------------------------------------------------------------------
        # Step 01
        # ---------------------------------------------------------------------

        print(
            "\n[Step 01/08] Loading true color product...",
            end=" ",
            flush=True,
        )

        scn = Scene(
            filenames=[str(file_path)],
            reader="abi_l2_nc",
            reader_kwargs={"chunks": my_chunks},
        )

        scn.load([prod_raw])

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 02
        # ---------------------------------------------------------------------

        print(
            "[Step 02/08] Saving native true color PNG...",
            end=" ",
            flush=True,
        )

        scn.save_dataset(
            prod_raw,
            filename=kwargs["goes_native_true_color_png"],
            writer="simple_image",
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 03
        # ---------------------------------------------------------------------

        print(
            "[Step 03/08] Applying dark pixel mask...",
            end=" ",
            flush=True,
        )

        scn_day = scn.copy()
        scn_day[prod_raw] = apply_dark_pixel_mask(
            scn_day[prod_raw], threshold=0.05
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 04
        # ---------------------------------------------------------------------

        print(
            "[Step 04/08] Saving native day-only PNG...",
            end=" ",
            flush=True,
        )

        scn_day.save_dataset(
            prod_raw,
            filename=kwargs["goes_native_true_color_day_only_png"],
            writer="simple_image",
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 05
        # ---------------------------------------------------------------------

        print(
            "[Step 05/08] Resampling GOES projection to WGS84...",
            end=" ",
            flush=True,
        )

        scn_res = scn.resample(
            area_wgs84,
            resampler="kd_tree",
            **resample_kwargs,
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 06
        # ---------------------------------------------------------------------

        print(
            "[Step 06/08] Saving WGS84 true color PNG and GeoTIFF...",
            end=" ",
            flush=True,
        )

        scn_res.save_dataset(
            prod_raw,
            filename=kwargs["wgs84_true_color_png"],
            writer="simple_image",
        )

        scn_res.save_dataset(
            prod_raw,
            filename=kwargs["wgs84_true_color_tif"],
            writer="geotiff",
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 07
        # ---------------------------------------------------------------------

        print(
            "[Step 07/08] Resampling day-only to WGS84...",
            end=" ",
            flush=True,
        )

        scn_res_day = scn_day.resample(
            area_wgs84,
            resampler="kd_tree",
            **resample_kwargs,
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 08
        # ---------------------------------------------------------------------

        print(
            "[Step 08/08] Saving WGS84 day-only PNG...",
            end=" ",
            flush=True,
        )

        scn_res_day.save_dataset(
            prod_raw,
            filename=kwargs["wgs84_true_color_day_only_png"],
            writer="simple_image",
        )

        print("[OK]", flush=True)

        # Validate outputs
        print(
            "[Step 09/08] Validating mandatory outputs...",
            end=" ",
            flush=True,
        )

        validate_output_files(kwargs)

        print("[OK]", flush=True)

        duration = round(time.time() - start_time, 2)

        print(f"[SUMMARY] Total time: {duration}s", flush=True)
        print("[STATUS] Process finished successfully.", flush=True)

        return True

    except Exception as e:
        print("\n[ERROR] FNP01 failed.", flush=True)
        print(f"[ERROR] {str(e)}", flush=True)
        print("[TRACEBACK]", flush=True)
        print(traceback.format_exc(), flush=True)

        return False

    finally:
        try:
            if scn is not None:
                del scn

            if scn_day is not None:
                del scn_day

            if scn_res is not None:
                del scn_res

            if scn_res_day is not None:
                del scn_res_day

            gc.collect()

        except Exception:
            pass


# =============================================================================
# SIMPLE MAIN
# =============================================================================

if __name__ == "__main__":

    print("\n" + " FNP01: MCMIPF DIAGNOSTIC TEST ".center(80, "="))

    working_dir = Path.cwd() / "test_one_image"

    nc_candidates = sorted(list(working_dir.glob("*MCMIPF*.nc")))

    if not nc_candidates:
        print(f"[ERROR] No .nc files with MCMIPF found in: {working_dir}")

    else:
        target_nc = nc_candidates[0]

        test_out = working_dir / "test_outputs" / target_nc.stem
        test_out.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] FILE   : {target_nc.name}")
        print(f"[INFO] OUTPUT : {test_out}")
        print("-" * 80)

        dict_output_file_name = gen_dict_output_file_name(
            nc_path=str(target_nc)
        )

        dict_output_file_path = {
            key: str(test_out / file_name)
            for key, file_name in dict_output_file_name.items()
        }

        success = run_proc_ABI_L2_MCMIPF_fnp01(
            nc_path=str(target_nc),
            **dict_output_file_path,
        )

        if success:
            print("-" * 80)
            print("[OK] TEST COMPLETED SUCCESSFULLY")
            print("=" * 80)
        else:
            print("-" * 80)
            print("[ERROR] TEST FAILED")
            print("=" * 80)
