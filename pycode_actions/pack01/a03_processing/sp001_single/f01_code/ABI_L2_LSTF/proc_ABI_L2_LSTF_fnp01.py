"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_LSTF/proc_ABI_L2_LSTF_fnp01.py
Version: 0.0.5
Description:
    Core processing - ABI-L2-LSTF FNP01.

    This FNP generates 8 mandatory files:
    - GOES native grey PNG
    - GOES native color PNG
    - WGS84 grey PNG
    - WGS84 color PNG
    - WGS84 grey GeoTIFF
    - WGS84 color GeoTIFF
    - Mercator grey PNG
    - Mercator color PNG

    If any mandatory file cannot be generated, the function returns False.

Last modification: 20-05-2026
"""

# =========================================================================================================================================
#  Execution:
#  python -m legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_LSTF.proc_ABI_L2_LSTF_fnp01
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


# =============================================================================
# 1. OUTPUT SCHEMA
# =============================================================================

def gen_dict_output_file_name(nc_path):
    """
    Generates the expected output filenames for ABI-L2-LSTF FNP01.

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
        "goes_native_grey_png": (
            f"{str_name}_CRS-Goes{str_position}_LSTF-fnp01-Celsius-Grey.png"
        ),
        "goes_native_color_png": (
            f"{str_name}_CRS-Goes{str_position}_LSTF-fnp01-Celsius-Color.png"
        ),
        "wgs84_grey_png": (
            f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Grey.png"
        ),
        "wgs84_color_png": (
            f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Color.png"
        ),
        "wgs84_grey_tif": (
            f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Grey.tif"
        ),
        "wgs84_color_tif": (
            f"{str_name}_CRS-WGS84_LSTF-fnp01-Celsius-Color.tif"
        ),
        "mercator_grey_png": (
            f"{str_name}_CRS-Mercator_LSTF-fnp01-Celsius-Grey.png"
        ),
        "mercator_color_png": (
            f"{str_name}_CRS-Mercator_LSTF-fnp01-Celsius-Color.png"
        ),
    }

    return dict_output_schema


def get_required_output_keys():
    """
    Returns all mandatory output keys expected by this FNP.
    """

    return [
        "goes_native_grey_png",
        "goes_native_color_png",
        "wgs84_grey_png",
        "wgs84_color_png",
        "wgs84_grey_tif",
        "wgs84_color_tif",
        "mercator_grey_png",
        "mercator_color_png",
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
# 2. CORE PROCESSING
# =============================================================================

def run_proc_ABI_L2_LSTF_fnp01(nc_path, **kwargs):
    """
    Executes FNP01 for ABI-L2-LSTF.

    Parameters
    ----------
    nc_path : str or Path
        Input ABI-L2-LSTF NetCDF file.

    **kwargs
        Mandatory output paths.

    Returns
    -------
    bool
        True if all eight mandatory files were generated successfully.
        False otherwise.
    """

    start_time = time.time()
    file_path = Path(nc_path)

    prod_raw = "LST"
    prod_color = "lst_celsius_color01"

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
    scn_wgs84 = None
    scn_mercator = None

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

        web_mercator_max = 20037508.342789244

        area_mercator = AreaDefinition(
            "webmercator",
            "Global Web Mercator",
            "epsg3857",
            "EPSG:3857",
            3600,
            3400,
            [
                -web_mercator_max,
                -web_mercator_max,
                web_mercator_max,
                web_mercator_max,
            ],
        )

        # ---------------------------------------------------------------------
        # Step 01
        # ---------------------------------------------------------------------

        print(
            "\n[Step 01/08] Loading LST scene and mandatory color product...",
            end=" ",
            flush=True,
        )

        scn = Scene(
            filenames=[str(file_path)],
            reader="abi_l2_nc",
            reader_kwargs={"chunks": my_chunks},
        )

        # Raw LST is mandatory.
        scn.load([prod_raw])

        # Convert LST from Kelvin to Celsius.
        scn[prod_raw] = scn[prod_raw] - 273.15
        scn[prod_raw].attrs["units"] = "Celsius"

        # Color product is mandatory.
        # If this fails, FNP01 must fail.
        scn.load([prod_color])

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 02
        # ---------------------------------------------------------------------

        print(
            "[Step 02/08] Saving mandatory native PNGs...",
            end=" ",
            flush=True,
        )

        scn.save_dataset(
            prod_raw,
            filename=kwargs["goes_native_grey_png"],
            writer="simple_image",
        )

        scn.save_dataset(
            prod_color,
            filename=kwargs["goes_native_color_png"],
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 03
        # ---------------------------------------------------------------------

        print(
            "[Step 03/08] Resampling GOES projection to WGS84...",
            end=" ",
            flush=True,
        )

        scn_wgs84 = scn.resample(
            area_wgs84,
            resampler="kd_tree",
            **resample_kwargs,
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 04
        # ---------------------------------------------------------------------

        print(
            "[Step 04/08] Saving mandatory WGS84 GeoTIFFs...",
            end=" ",
            flush=True,
        )

        scn_wgs84.save_dataset(
            prod_raw,
            filename=kwargs["wgs84_grey_tif"],
            writer="geotiff",
        )

        scn_wgs84.save_dataset(
            prod_color,
            filename=kwargs["wgs84_color_tif"],
            writer="geotiff",
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 05
        # ---------------------------------------------------------------------

        print(
            "[Step 05/08] Saving mandatory WGS84 PNGs...",
            end=" ",
            flush=True,
        )

        scn_wgs84.save_dataset(
            prod_raw,
            filename=kwargs["wgs84_grey_png"],
            writer="simple_image",
        )

        scn_wgs84.save_dataset(
            prod_color,
            filename=kwargs["wgs84_color_png"],
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 06
        # ---------------------------------------------------------------------

        print(
            "[Step 06/08] Resampling GOES projection to Web Mercator...",
            end=" ",
            flush=True,
        )

        scn_mercator = scn.resample(
            area_mercator,
            resampler="kd_tree",
            **resample_kwargs,
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 07
        # ---------------------------------------------------------------------

        print(
            "[Step 07/08] Saving mandatory Mercator PNGs...",
            end=" ",
            flush=True,
        )

        scn_mercator.save_dataset(
            prod_raw,
            filename=kwargs["mercator_grey_png"],
            writer="simple_image",
        )

        scn_mercator.save_dataset(
            prod_color,
            filename=kwargs["mercator_color_png"],
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 08
        # ---------------------------------------------------------------------

        print(
            "[Step 08/08] Validating mandatory outputs...",
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

            if scn_wgs84 is not None:
                del scn_wgs84

            if scn_mercator is not None:
                del scn_mercator

            gc.collect()

        except Exception:
            pass


# =============================================================================
# SIMPLE MAIN
# =============================================================================

if __name__ == "__main__":

    print("\n" + " FNP01: LSTF DIAGNOSTIC TEST ".center(80, "="))

    working_dir = Path.cwd() / "test_one_image"

    nc_candidates = sorted(list(working_dir.glob("*LSTF*.nc")))

    if not nc_candidates:
        print(f"[ERROR] No .nc files with LSTF found in: {working_dir}")

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

        success = run_proc_ABI_L2_LSTF_fnp01(
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