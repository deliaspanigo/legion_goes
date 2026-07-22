"""
Path:
legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_MCMIPF/proc_ABI_L2_MCMIPF_fnp03.py

Description:
    Core processing - ABI-L2-MCMIPF FNP03.

    Generates a WGS84 PNG for each selected Satpy composite used in
    notebooks/ABI_L2_MCMIPF/note04_satpy_multi.
"""

import gc
import re
import time
import traceback
from pathlib import Path

from pyresample.geometry import AreaDefinition
from satpy import Scene

from legion_goes.satpy_config.my_config_satpy import CACHE_DIR
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import (
    get_position_by_sat_id,
)


SATPY_MULTI_COMPOSITES = [
    "24h_microphysics",
    "airmass",
    "ash",
    "cimss_cloud_type",
    "cimss_cloud_type_raw",
    "cimss_green",
    "cimss_green_sunz_rayleigh",
    "cimss_true_color",
    "cimss_true_color_sunz",
    "cimss_true_color_sunz_rayleigh",
    "cira_day_convection",
    "cira_fire_temperature",
    "cloudtop",
    "cloud_phase",
    "cloud_phase_raw",
    "cloud_phase_distinction",
    "cloud_phase_distinction_raw",
    "colorized_ir_clouds",
    "color_infrared",
    "convection",
    "day_microphysics",
    "day_microphysics_abi",
    "day_microphysics_eum",
    "dust",
    "fire_temperature_awips",
    "fog",
    "geo_color_high_clouds",
    "green",
    "natural_color",
    "true_color",
]


def safe_key(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower()


def gen_dict_output_file_name(nc_path):
    """
    Generates the expected output filenames for ABI-L2-MCMIPF FNP03.
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

    return {
        f"wgs84_{safe_key(composite)}_png": (
            f"{str_name}_CRS-WGS84_MCMIPF-fnp03-{composite}.png"
        )
        for composite in SATPY_MULTI_COMPOSITES
    }


def get_required_output_keys():
    return list(gen_dict_output_file_name("OR_ABI-L2-MCMIPF-M6_G19_s20260010000000_e20260010009599_c20260010010000.nc").keys())


def validate_required_kwargs(kwargs):
    missing = [
        key
        for key in get_required_output_keys()
        if key not in kwargs or kwargs.get(key) is None or str(kwargs.get(key)).strip() == ""
    ]

    if missing:
        raise ValueError("Missing mandatory output path(s): " + ", ".join(missing))


def validate_output_files(kwargs):
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

    if missing_or_empty:
        msg_lines = ["Mandatory output validation failed:"]
        for key, path_obj, reason in missing_or_empty:
            msg_lines.append(f"  - {key}: {path_obj} [{reason}]")
        raise RuntimeError("\n".join(msg_lines))


def run_proc_ABI_L2_MCMIPF_fnp03(nc_path, **kwargs):
    """
    Executes FNP03 for ABI-L2-MCMIPF.

    This function writes one WGS84 PNG for each composite in
    SATPY_MULTI_COMPOSITES.
    """

    start_time = time.time()
    file_path = Path(nc_path)

    scn = None
    scn_res = None

    try:
        if not file_path.exists():
            raise FileNotFoundError(f"Input NetCDF does not exist: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Input path is not a file: {file_path}")

        validate_required_kwargs(kwargs)

        first_output_file_path = list(kwargs.values())[0]
        output_folder = Path(first_output_file_path).parent
        output_folder.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] output_folder = {output_folder}", flush=True)

        area_wgs84 = AreaDefinition(
            "wgs84",
            "Global WGS84",
            "epsg4326",
            "EPSG:4326",
            3600,
            1800,
            [-180, -90, 180, 90],
        )

        resample_kwargs = {
            "cache_dir": str(CACHE_DIR),
            "nprocs": 4,
            "static_data": True,
        }

        my_chunks = {
            "y": 1024,
            "x": 1024,
        }

        print("[Step 01/04] Opening MCMIPF scene...", end=" ", flush=True)
        scn = Scene(
            filenames=[str(file_path)],
            reader="abi_l2_nc",
            reader_kwargs={"chunks": my_chunks},
        )
        available_composites = set(str(x) for x in scn.available_composite_names())
        print("[OK]", flush=True)

        missing_available = [
            composite
            for composite in SATPY_MULTI_COMPOSITES
            if composite not in available_composites
        ]
        if missing_available:
            raise RuntimeError(
                "Some configured Satpy composites are not available: "
                + ", ".join(missing_available)
            )

        print(
            f"[Step 02/04] Loading {len(SATPY_MULTI_COMPOSITES)} Satpy composites...",
            end=" ",
            flush=True,
        )
        scn.load(SATPY_MULTI_COMPOSITES)
        print("[OK]", flush=True)

        print("[Step 03/04] Resampling composites to WGS84...", end=" ", flush=True)
        scn_res = scn.resample(
            area_wgs84,
            resampler="kd_tree",
            **resample_kwargs,
        )
        print("[OK]", flush=True)

        print("[Step 04/04] Saving WGS84 PNG composites...", flush=True)
        total = len(SATPY_MULTI_COMPOSITES)
        for idx, composite in enumerate(SATPY_MULTI_COMPOSITES, start=1):
            output_key = f"wgs84_{safe_key(composite)}_png"
            print(f"  [{idx:02d}/{total:02d}] {composite}", end=" ", flush=True)
            scn_res.save_dataset(
                composite,
                filename=kwargs[output_key],
                writer="simple_image",
            )
            print("[OK]", flush=True)

        print("[Step 05/04] Validating mandatory outputs...", end=" ", flush=True)
        validate_output_files(kwargs)
        print("[OK]", flush=True)

        duration = time.time() - start_time
        print(f"[DONE] ABI-L2-MCMIPF FNP03 completed in {duration:.2f} seconds.", flush=True)
        return True

    except Exception:
        print("[ERROR] ABI-L2-MCMIPF FNP03 failed.", flush=True)
        traceback.print_exc()
        return False

    finally:
        try:
            del scn_res
        except Exception:
            pass
        try:
            del scn
        except Exception:
            pass
        gc.collect()


if __name__ == "__main__":
    print("\n" + " FNP03: MCMIPF SATPY MULTI WGS84 TEST ".center(80, "="))
    working_dir = Path.cwd()
    nc_candidates = sorted(list(working_dir.glob("*MCMIPF*.nc")))
    if not nc_candidates:
        print(f"[ERROR] No .nc files with 'MCMIPF' found in: {working_dir}")
    else:
        target_nc = nc_candidates[0]
        output_dir = working_dir / "fnp03_test_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            key: str(output_dir / value)
            for key, value in gen_dict_output_file_name(target_nc).items()
        }
        run_proc_ABI_L2_MCMIPF_fnp03(nc_path=target_nc, **paths)
