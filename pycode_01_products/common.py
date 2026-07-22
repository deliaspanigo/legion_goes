"""
Common helpers for simple product processing.

The helpers in this file are intentionally small and explicit. They avoid
duplicating the same GOES filename parsing, area definitions, and output checks
in every product module.
"""

import re
from pathlib import Path

from pyresample.geometry import AreaDefinition

from legion_goes.satpy_config.my_config_satpy import CACHE_DIR
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import (
    get_position_by_sat_id,
)


def parse_goes_filename(nc_path):
    """
    Read the product, satellite, and start timestamp from a GOES filename.

    Returns
    -------
    dict
        Metadata used to create human-readable and stable output names.
    """

    nc_file_name = Path(nc_path).name
    match = re.search(
        r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})",
        nc_file_name,
    )

    if not match:
        raise ValueError(f"Could not parse GOES filename: {nc_file_name}")

    sat = match.group("sat")
    sat_number = sat[1:]
    position = get_position_by_sat_id(sat_id=sat_number)

    return {
        "product": match.group("prod"),
        "satellite": sat,
        "satellite_number": sat_number,
        "position": position,
        "start_timestamp": match.group("start"),
        "simple_prefix": (
            f"SP-01-simple_G{sat_number}-{position}-s{match.group('start')}"
        ),
    }


def ensure_input_file(nc_path):
    """
    Validate that the input NetCDF exists and return it as a Path.
    """

    file_path = Path(nc_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Input NetCDF does not exist: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Input path is not a file: {file_path}")

    return file_path


def ensure_output_dir(output_dir):
    """
    Create an output directory and return it as a Path.
    """

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_output_files(output_paths):
    """
    Confirm that every generated output exists and is not empty.
    """

    missing_or_empty = []

    for key, path in output_paths.items():
        path_obj = Path(path)

        if not path_obj.exists():
            missing_or_empty.append((key, path_obj, "missing"))
            continue

        if not path_obj.is_file():
            missing_or_empty.append((key, path_obj, "not_a_file"))
            continue

        if path_obj.stat().st_size == 0:
            missing_or_empty.append((key, path_obj, "empty"))

    if missing_or_empty:
        lines = ["Output validation failed:"]
        for key, path_obj, reason in missing_or_empty:
            lines.append(f"  - {key}: {path_obj} [{reason}]")
        raise RuntimeError("\n".join(lines))

    return True


def area_wgs84():
    """
    Global WGS84 area used by the LegionGOES viewers.
    """

    return AreaDefinition(
        "wgs84",
        "Global WGS84",
        "epsg4326",
        "EPSG:4326",
        3600,
        1800,
        [-180, -90, 180, 90],
    )


def area_web_mercator():
    """
    Global Web Mercator area used by Leaflet-style maps.
    """

    web_mercator_max = 20037508.342789244

    return AreaDefinition(
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


def satpy_resample_kwargs():
    """
    Default Satpy resampling options used by the simple processors.
    """

    return {
        "cache_dir": str(CACHE_DIR),
        "nprocs": 4,
        "static_data": True,
    }


def satpy_reader_chunks():
    """
    Default chunk size used when loading ABI L2 NetCDF files.
    """

    return {
        "y": 1024,
        "x": 1024,
    }


def _flatten_output_paths(output_paths):
    """
    Return a flat ``dict[str, Path]`` from a schema-like output dictionary.

    Product schemas intentionally describe exact files. The checkpoint helpers
    use those paths to decide whether processing can be resumed safely.
    """

    flat = {}

    for key, value in dict(output_paths).items():
        if value is None:
            continue
        if isinstance(value, (str, Path)):
            flat[str(key)] = Path(value)

    return flat


def output_paths_status(output_paths):
    """
    Inspect expected output files.

    Returns
    -------
    dict
        Contains ``complete`` plus ``ok``, ``missing``, ``empty`` and
        ``not_file`` lists. A complete set means every expected path exists,
        is a regular file, and is not empty.
    """

    expected = _flatten_output_paths(output_paths)
    status = {
        "complete": False,
        "expected": expected,
        "ok": [],
        "missing": [],
        "empty": [],
        "not_file": [],
    }

    for key, path in expected.items():
        if not path.exists():
            status["missing"].append((key, path))
            continue
        if not path.is_file():
            status["not_file"].append((key, path))
            continue
        if path.stat().st_size == 0:
            status["empty"].append((key, path))
            continue
        status["ok"].append((key, path))

    status["complete"] = (
        bool(expected)
        and not status["missing"]
        and not status["empty"]
        and not status["not_file"]
    )
    return status


def remove_expected_outputs(output_paths):
    """
    Delete expected output files that already exist.

    This is intentionally scoped to the paths declared by the schema. It does
    not remove arbitrary files from the output directory.
    """

    removed = []
    for key, path in _flatten_output_paths(output_paths).items():
        if path.exists() and path.is_file():
            path.unlink()
            removed.append((key, path))
    return removed


def processing_checkpoint(label, expected_outputs, overwrite=False):
    """
    Decide whether one FNP should be processed, skipped, or cleaned first.

    Rules
    -----
    - If ``overwrite`` is True, remove existing expected outputs and process.
    - If every expected output exists and is not empty, skip processing.
    - If at least one expected output is missing/empty, remove the partial set
      and process from a clean state.
    """

    status = output_paths_status(expected_outputs)
    expected = status["expected"]

    if not expected:
        raise ValueError(f"[{label}] No expected outputs were declared.")

    if overwrite:
        removed = remove_expected_outputs(expected)
        print(
            f"[{label}] overwrite=True. Removed {len(removed)} existing expected output(s).",
            flush=True,
        )
        return {
            "action": "process",
            "reason": "overwrite",
            "status": status,
            "removed": removed,
            "expected_outputs": expected,
        }

    if status["complete"]:
        print(
            f"[{label}] All {len(expected)} expected output(s) already exist. Skipping processing.",
            flush=True,
        )
        return {
            "action": "skip",
            "reason": "complete",
            "status": status,
            "removed": [],
            "expected_outputs": expected,
        }

    problem_count = len(status["missing"]) + len(status["empty"]) + len(status["not_file"])
    print(
        f"[{label}] Expected output set is incomplete ({problem_count} problem(s)). Cleaning partial outputs and processing again.",
        flush=True,
    )
    for kind in ("missing", "empty", "not_file"):
        for key, path in status[kind][:8]:
            print(f"[{label}] {kind}: {key} -> {path}", flush=True)
        if len(status[kind]) > 8:
            print(f"[{label}] {kind}: ... {len(status[kind]) - 8} more", flush=True)

    removed = remove_expected_outputs(expected)
    print(f"[{label}] Removed {len(removed)} partial expected output(s).", flush=True)

    return {
        "action": "process",
        "reason": "incomplete",
        "status": status,
        "removed": removed,
        "expected_outputs": expected,
    }

