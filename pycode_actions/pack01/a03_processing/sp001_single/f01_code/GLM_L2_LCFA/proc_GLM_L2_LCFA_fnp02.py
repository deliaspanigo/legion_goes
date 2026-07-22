"""
Path:
legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/GLM_L2_LCFA/proc_GLM_L2_LCFA_fnp02.py

Description:
    GLM-L2-LCFA FNP02.

    This processor builds one electrical-storm frame for one ABI-L2-MCMIPF
    full-disk scan. It can keep GLM files by scan overlap or by the clean
    10-minute UTC block defined by the MCMIPF start time, then exports both
    vector and transparent raster layers.

Main outputs:
    - WGS84 flash points CSV
    - WGS84 flash points GeoJSON
    - WGS84 density grid CSV
    - WGS84 transparent points PNG
    - WGS84 transparent density-grid PNG
    - WGS84 transparent heatmap PNG
    - JSON statistics
    - JSON manifest
"""

# ==============================================================================================================================================
# Execution example:
# python -m legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.GLM_L2_LCFA.proc_GLM_L2_LCFA_fnp02
# ==============================================================================================================================================

import csv
import json
import math
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import netCDF4 as nc
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import (
    get_position_by_sat_id,
)


WGS84_WIDTH_DEFAULT = 3600
WGS84_HEIGHT_DEFAULT = 1800


def parse_goes_timestamp(timestamp):
    """
    Parses GOES timestamps such as 20260031200230.

    GOES filenames commonly use YYYYDDDHHMMSSd. The last digit is treated as
    fractional seconds when present.
    """

    text = str(timestamp)

    if not re.fullmatch(r"\d{13,14}", text):
        raise ValueError(f"Invalid GOES timestamp: {timestamp}")

    year = int(text[0:4])
    day_of_year = int(text[4:7])
    hour = int(text[7:9])
    minute = int(text[9:11])
    second = int(text[11:13])
    fraction = text[13:]

    microsecond = 0

    if fraction:
        microsecond = int(round(float("0." + fraction) * 1000000))

    return (
        datetime(year, 1, 1, tzinfo=timezone.utc)
        + timedelta(
            days=day_of_year - 1,
            hours=hour,
            minutes=minute,
            seconds=second,
            microseconds=microsecond,
        )
    )


def format_utc(dt):
    if dt is None:
        return None

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_goes_filename(path):
    """
    Extracts product, satellite, start and end timestamps from GOES filenames.
    """

    file_name = Path(path).name
    match = re.search(
        r"OR_(?P<product>ABI-L2-MCMIPF|GLM-L2-LCFA)(?:-[A-Z0-9]+)?_"
        r"(?P<sat>G\d{2})_s(?P<start>\d{13,14})_e(?P<end>\d{13,14})_c(?P<created>\d{13,14})",
        file_name,
    )

    if not match:
        raise ValueError(f"Could not parse GOES filename: {file_name}")

    sat = match.group("sat")
    sat_number = sat[1:]

    return {
        "file_name": file_name,
        "product": match.group("product"),
        "sat": sat,
        "sat_number": sat_number,
        "position": get_position_by_sat_id(sat_id=sat_number),
        "start_raw": match.group("start"),
        "end_raw": match.group("end"),
        "created_raw": match.group("created"),
        "start_utc": parse_goes_timestamp(match.group("start")),
        "end_utc": parse_goes_timestamp(match.group("end")),
        "created_utc": parse_goes_timestamp(match.group("created")),
    }


def gen_dict_output_file_name(mcmipf_nc_path):
    """
    Defines the output contract for the GLM-MCMIPF aggregated FNP02 frame.
    """

    info = parse_goes_filename(mcmipf_nc_path)

    if info["product"] != "ABI-L2-MCMIPF":
        raise ValueError(
            "GLM FNP02 must be anchored to an ABI-L2-MCMIPF NetCDF file."
        )

    str_name = (
        f"SP-01-simple_G{info['sat_number']}-{info['position']}-"
        f"s{info['start_raw']}"
    )

    return {
        "points_csv": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-FlashPoints.csv"
        ),
        "points_geojson": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-FlashPoints.geojson"
        ),
        "density_grid_csv": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-DensityGrid.csv"
        ),
        "wgs84_points_png": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-FlashPoints.png"
        ),
        "wgs84_density_png": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-DensityGrid.png"
        ),
        "wgs84_heatmap_png": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-Heatmap.png"
        ),
        "stats_json": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-Stats.json"
        ),
        "manifest_json": (
            f"{str_name}_CRS-WGS84_GLM-LCFA-fnp02-Manifest.json"
        ),
    }


def get_required_output_keys():
    return [
        "points_csv",
        "points_geojson",
        "density_grid_csv",
        "wgs84_points_png",
        "wgs84_density_png",
        "wgs84_heatmap_png",
        "stats_json",
        "manifest_json",
    ]


def _resolve_output_paths(mcmipf_nc_path, output_dir=None, **kwargs):
    names = gen_dict_output_file_name(mcmipf_nc_path)

    if output_dir is None:
        output_dir = Path.cwd() / "glm_l2_lcfa_fnp02_outputs" / Path(mcmipf_nc_path).stem
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {}

    for key, file_name in names.items():
        candidate = kwargs.get(key)
        paths[key] = Path(candidate) if candidate else output_dir / file_name
        paths[key].parent.mkdir(parents=True, exist_ok=True)

    return paths


def _masked_to_float(values):
    arr = np.ma.asarray(values).astype(np.float64)
    return np.asarray(arr.filled(np.nan), dtype=np.float64)


def _get_optional_variable(ds, name, size):
    if name not in ds.variables:
        return np.full(size, np.nan, dtype=np.float64)

    return _masked_to_float(ds.variables[name][:])


def _ten_minute_block_for_mcmipf(start_utc):
    block_start = start_utc.replace(
        minute=(start_utc.minute // 10) * 10,
        second=0,
        microsecond=0,
    )
    block_end = block_start + timedelta(minutes=10)
    return block_start, block_end


def _glm_file_is_in_window(glm_info, start_utc, end_utc, matching_mode):
    glm_start = glm_info["start_utc"]
    glm_end = glm_info["end_utc"]

    if matching_mode == "overlap":
        return glm_start < end_utc and glm_end > start_utc

    if matching_mode == "glm_start_inside":
        return glm_start >= start_utc and glm_start < end_utc

    if matching_mode == "ten_minute_block":
        block_start, block_end = _ten_minute_block_for_mcmipf(start_utc)
        return glm_start >= block_start and glm_start < block_end

    raise ValueError(
        "matching_mode must be 'glm_start_inside', 'overlap', or 'ten_minute_block'."
    )


def select_glm_files_for_mcmipf(mcmipf_nc_path, glm_nc_paths, matching_mode="overlap"):
    """
    Returns only the GLM files associated with the MCMIPF frame.
    """

    mcmipf_info = parse_goes_filename(mcmipf_nc_path)

    if mcmipf_info["product"] != "ABI-L2-MCMIPF":
        raise ValueError("The anchor file must be ABI-L2-MCMIPF.")

    selected = []
    rejected = []

    for glm_path in glm_nc_paths:
        try:
            glm_info = parse_goes_filename(glm_path)
        except Exception as exc:
            rejected.append({
                "path": str(glm_path),
                "reason": f"parse_error: {exc}",
            })
            continue

        if glm_info["product"] != "GLM-L2-LCFA":
            rejected.append({
                "path": str(glm_path),
                "reason": "not_glm_l2_lcfa",
            })
            continue

        if glm_info["sat_number"] != mcmipf_info["sat_number"]:
            rejected.append({
                "path": str(glm_path),
                "reason": "satellite_mismatch",
            })
            continue

        if _glm_file_is_in_window(
            glm_info,
            mcmipf_info["start_utc"],
            mcmipf_info["end_utc"],
            matching_mode,
        ):
            selected.append((Path(glm_path), glm_info))
        else:
            rejected.append({
                "path": str(glm_path),
                "reason": "outside_matching_window",
            })

    selected = sorted(selected, key=lambda item: item[1]["start_utc"])

    return selected, rejected, mcmipf_info


def _read_glm_flash_rows(glm_path, glm_info, mcmipf_info, quality_good_only=True):
    rows = []

    with nc.Dataset(glm_path) as ds:
        if "flash_lat" not in ds.variables or "flash_lon" not in ds.variables:
            return rows

        lats = _masked_to_float(ds.variables["flash_lat"][:])
        lons = _masked_to_float(ds.variables["flash_lon"][:])
        n = len(lats)

        energies = _get_optional_variable(ds, "flash_energy", n)
        areas = _get_optional_variable(ds, "flash_area", n)

        if "flash_quality_flag" in ds.variables:
            quality = np.ma.asarray(ds.variables["flash_quality_flag"][:])
            quality = np.asarray(quality.filled(-9999), dtype=np.int32)
        else:
            quality = np.zeros(n, dtype=np.int32)

        if "flash_time_offset_of_first_event" in ds.variables:
            first_offset = _masked_to_float(
                ds.variables["flash_time_offset_of_first_event"][:]
            )
        else:
            first_offset = np.full(n, np.nan, dtype=np.float64)

        if "flash_time_offset_of_last_event" in ds.variables:
            last_offset = _masked_to_float(
                ds.variables["flash_time_offset_of_last_event"][:]
            )
        else:
            last_offset = np.full(n, np.nan, dtype=np.float64)

    for i in range(n):
        lat = lats[i]
        lon = lons[i]
        qf = int(quality[i]) if np.isfinite(quality[i]) else None

        if not np.isfinite(lat) or not np.isfinite(lon):
            continue

        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            continue

        if quality_good_only and qf != 0:
            continue

        rows.append({
            "mcmipf_file": mcmipf_info["file_name"],
            "mcmipf_start_raw": mcmipf_info["start_raw"],
            "mcmipf_end_raw": mcmipf_info["end_raw"],
            "mcmipf_start_utc": format_utc(mcmipf_info["start_utc"]),
            "mcmipf_end_utc": format_utc(mcmipf_info["end_utc"]),
            "satellite": glm_info["sat"],
            "position": glm_info["position"],
            "glm_file": glm_info["file_name"],
            "glm_start_raw": glm_info["start_raw"],
            "glm_end_raw": glm_info["end_raw"],
            "glm_start_utc": format_utc(glm_info["start_utc"]),
            "glm_end_utc": format_utc(glm_info["end_utc"]),
            "flash_index_in_file": i,
            "flash_lat": float(lat),
            "flash_lon": float(lon),
            "flash_energy": None if not np.isfinite(energies[i]) else float(energies[i]),
            "flash_area": None if not np.isfinite(areas[i]) else float(areas[i]),
            "flash_quality_flag": qf,
            "flash_time_offset_first_event": (
                None if not np.isfinite(first_offset[i]) else float(first_offset[i])
            ),
            "flash_time_offset_last_event": (
                None if not np.isfinite(last_offset[i]) else float(last_offset[i])
            ),
        })

    return rows


def _write_csv(rows, output_csv, fieldnames):
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _write_points_geojson(rows, output_geojson):
    features = []

    for idx, row in enumerate(rows, start=1):
        lon = row.get("flash_lon")
        lat = row.get("flash_lat")

        if lon is None or lat is None:
            continue

        props = {
            key: value
            for key, value in row.items()
            if key not in ["flash_lon", "flash_lat"]
        }
        props["point_id"] = idx

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)],
            },
            "properties": props,
        })

    payload = {
        "type": "FeatureCollection",
        "name": Path(output_geojson).stem,
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326",
            },
        },
        "features": features,
    }

    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _lonlat_to_pixel(lon, lat, width, height):
    x = (float(lon) + 180.0) / 360.0 * (width - 1)
    y = (90.0 - float(lat)) / 180.0 * (height - 1)
    return int(round(x)), int(round(y))


def _energy_norm(values):
    arr = np.asarray([
        value for value in values
        if value is not None and np.isfinite(value) and value > 0
    ], dtype=np.float64)

    if arr.size == 0:
        return None, None

    return float(np.nanmin(arr)), float(np.nanmax(arr))


def _point_color(energy, min_energy, max_energy, alpha=230):
    if energy is None or not np.isfinite(energy) or min_energy is None or max_energy is None:
        t = 0.55
    elif max_energy <= min_energy:
        t = 0.75
    else:
        e = max(float(energy), 0.0)
        lo = math.log10(max(min_energy, 1e-12))
        hi = math.log10(max(max_energy, 1e-12))
        vv = math.log10(max(e, 1e-12))
        t = max(0.0, min(1.0, (vv - lo) / (hi - lo))) if hi > lo else 0.75

    if t < 0.5:
        local = t / 0.5
        r = int(255)
        g = int(235 - 95 * local)
        b = int(40 - 20 * local)
    else:
        local = (t - 0.5) / 0.5
        r = int(255)
        g = int(140 - 120 * local)
        b = int(20 + 180 * local)

    return r, max(0, g), max(0, min(255, b)), alpha


def _heat_color(t):
    t = max(0.0, min(1.0, float(t)))

    stops = [
        (0.00, (255, 230, 40)),
        (0.35, (255, 150, 0)),
        (0.70, (255, 35, 0)),
        (1.00, (220, 0, 255)),
    ]

    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]

        if t >= t0 and t <= t1:
            local = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(
                int(round(c0[j] + (c1[j] - c0[j]) * local))
                for j in range(3)
            )

    return stops[-1][1]


def _write_points_png(rows, output_png, width, height, radius_px=7):
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    energies = [row.get("flash_energy") for row in rows]
    min_energy, max_energy = _energy_norm(energies)

    for row in rows:
        lon = row.get("flash_lon")
        lat = row.get("flash_lat")

        if lon is None or lat is None:
            continue

        x, y = _lonlat_to_pixel(lon, lat, width, height)
        color = _point_color(row.get("flash_energy"), min_energy, max_energy, alpha=235)
        glow = (color[0], color[1], color[2], 70)
        outline = (255, 255, 255, 210)

        draw.ellipse(
            [
                x - radius_px - 2,
                y - radius_px - 2,
                x + radius_px + 2,
                y + radius_px + 2,
            ],
            fill=glow,
        )
        draw.ellipse(
            [x - radius_px, y - radius_px, x + radius_px, y + radius_px],
            fill=color,
            outline=outline,
            width=1,
        )

    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)


def _build_density_grid(rows, lon_step=1.0, lat_step=1.0):
    cells = {}

    for row in rows:
        lon = row.get("flash_lon")
        lat = row.get("flash_lat")

        if lon is None or lat is None:
            continue

        lon_idx = int(math.floor((float(lon) + 180.0) / lon_step))
        lat_idx = int(math.floor((float(lat) + 90.0) / lat_step))
        lon_idx = max(0, min(int(360.0 / lon_step) - 1, lon_idx))
        lat_idx = max(0, min(int(180.0 / lat_step) - 1, lat_idx))
        key = (lon_idx, lat_idx)
        energy = row.get("flash_energy")

        if key not in cells:
            lon_min = -180.0 + lon_idx * lon_step
            lat_min = -90.0 + lat_idx * lat_step
            cells[key] = {
                "cell_id": f"lon{lon_idx:04d}_lat{lat_idx:04d}",
                "lon_min": lon_min,
                "lon_max": lon_min + lon_step,
                "lat_min": lat_min,
                "lat_max": lat_min + lat_step,
                "flash_count": 0,
                "energy_sum": 0.0,
            }

        cells[key]["flash_count"] += 1

        if energy is not None and np.isfinite(energy):
            cells[key]["energy_sum"] += float(energy)

    out = list(cells.values())
    out.sort(key=lambda item: (item["lat_min"], item["lon_min"]))

    for row in out:
        row["energy_mean"] = (
            row["energy_sum"] / row["flash_count"]
            if row["flash_count"] > 0
            else None
        )

    return out


def _write_density_png(density_rows, output_png, width, height):
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    max_count = max([row["flash_count"] for row in density_rows], default=0)

    for row in density_rows:
        if max_count <= 0:
            continue

        t = math.log1p(row["flash_count"]) / math.log1p(max_count)
        color = _heat_color(t)
        alpha = int(45 + 165 * t)
        x1, y1 = _lonlat_to_pixel(row["lon_min"], row["lat_max"], width, height)
        x2, y2 = _lonlat_to_pixel(row["lon_max"], row["lat_min"], width, height)

        draw.rectangle(
            [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)],
            fill=(color[0], color[1], color[2], alpha),
            outline=(255, 255, 255, min(160, alpha + 30)),
            width=1,
        )

    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)


def _write_heatmap_png(rows, output_png, width, height, blur_radius_px=14):
    heat = np.zeros((height, width), dtype=np.float32)

    for row in rows:
        lon = row.get("flash_lon")
        lat = row.get("flash_lat")

        if lon is None or lat is None:
            continue

        x, y = _lonlat_to_pixel(lon, lat, width, height)

        if x < 0 or x >= width or y < 0 or y >= height:
            continue

        heat[y, x] += 1.0

    if np.nanmax(heat) > 0:
        raw = Image.fromarray(np.clip(heat / np.nanmax(heat) * 255.0, 0, 255).astype(np.uint8), mode="L")
        blurred = raw.filter(ImageFilter.GaussianBlur(radius=blur_radius_px))
        arr = np.asarray(blurred, dtype=np.float32)

        if np.nanmax(arr) > 0:
            arr = arr / np.nanmax(arr)
    else:
        arr = heat

    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    mask = arr > 0

    if np.any(mask):
        values = arr[mask]
        colors = np.array([_heat_color(v) for v in values], dtype=np.uint8)
        rgba[mask, 0:3] = colors
        rgba[mask, 3] = np.clip(values * 220, 0, 220).astype(np.uint8)

    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(output_png)


def _write_stats_json(stats, output_json):
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def _write_manifest_json(manifest, output_json):
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def _validate_outputs(paths):
    missing = []

    for key in get_required_output_keys():
        path = Path(paths[key])

        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            missing.append(f"{key}: {path}")

    if missing:
        raise RuntimeError("Missing or empty GLM FNP02 outputs:\n  - " + "\n  - ".join(missing))


def run_proc_GLM_L2_LCFA_fnp02(
    mcmipf_nc_path,
    glm_nc_paths,
    output_dir=None,
    matching_mode="overlap",
    quality_good_only=True,
    width=WGS84_WIDTH_DEFAULT,
    height=WGS84_HEIGHT_DEFAULT,
    point_radius_px=7,
    density_lon_step=1.0,
    density_lat_step=1.0,
    heatmap_blur_radius_px=14,
    **kwargs,
):
    """
    Builds vector and transparent raster GLM products for one MCMIPF scan.

    Parameters
    ----------
    mcmipf_nc_path : str or Path
        MCMIPF anchor file. Its filename start/end timestamps define the GLM
        matching interval.

    glm_nc_paths : list[str | Path]
        GLM candidates. The processor keeps only GLM files associated with the
        selected MCMIPF frame.

    output_dir : str or Path, optional
        Output directory. If omitted, a local diagnostic folder is created.

    matching_mode : str
        'overlap' keeps GLM files whose interval overlaps the MCMIPF scan.
        'glm_start_inside' keeps only GLM files whose start time is inside the
        MCMIPF interval.
        'ten_minute_block' keeps GLM files whose start time is inside the clean
        10-minute UTC block defined by the MCMIPF start time.

    Returns
    -------
    bool
        True if all outputs were generated.
    """

    start_time = time.time()
    mcmipf_nc_path = Path(mcmipf_nc_path)
    glm_nc_paths = [Path(path) for path in glm_nc_paths]
    paths = _resolve_output_paths(mcmipf_nc_path, output_dir=output_dir, **kwargs)

    print("\n" + " GLM-L2-LCFA FNP02: MCMIPF WINDOW AGGREGATION ".center(80, "="))
    print(f"[GLM FNP02] Anchor MCMIPF: {mcmipf_nc_path.name}", flush=True)
    print(f"[GLM FNP02] Candidate GLM files: {len(glm_nc_paths)}", flush=True)

    selected_glm, rejected_glm, mcmipf_info = select_glm_files_for_mcmipf(
        mcmipf_nc_path=mcmipf_nc_path,
        glm_nc_paths=glm_nc_paths,
        matching_mode=matching_mode,
    )
    glm_block_start, glm_block_end = _ten_minute_block_for_mcmipf(mcmipf_info["start_utc"])

    print(
        "[GLM FNP02] MCMIPF scan window: "
        f"{format_utc(mcmipf_info['start_utc'])} to {format_utc(mcmipf_info['end_utc'])}",
        flush=True,
    )
    if matching_mode == "ten_minute_block":
        print(
            "[GLM FNP02] GLM 10-minute block: "
            f"{format_utc(glm_block_start)} to {format_utc(glm_block_end - timedelta(seconds=1))}",
            flush=True,
        )
    print(f"[GLM FNP02] Matched GLM files: {len(selected_glm)}", flush=True)

    rows = []
    file_summaries = []

    for index, (glm_path, glm_info) in enumerate(selected_glm, start=1):
        print(f"[GLM FNP02] Reading GLM {index}/{len(selected_glm)}: {glm_path.name}", flush=True)
        file_rows = _read_glm_flash_rows(
            glm_path=glm_path,
            glm_info=glm_info,
            mcmipf_info=mcmipf_info,
            quality_good_only=quality_good_only,
        )
        rows.extend(file_rows)
        file_summaries.append({
            "glm_file": glm_info["file_name"],
            "glm_start_utc": format_utc(glm_info["start_utc"]),
            "glm_end_utc": format_utc(glm_info["end_utc"]),
            "flash_count": len(file_rows),
        })

    for point_id, row in enumerate(rows, start=1):
        row["point_id"] = point_id

    point_fields = [
        "point_id",
        "mcmipf_file",
        "mcmipf_start_raw",
        "mcmipf_end_raw",
        "mcmipf_start_utc",
        "mcmipf_end_utc",
        "satellite",
        "position",
        "glm_file",
        "glm_start_raw",
        "glm_end_raw",
        "glm_start_utc",
        "glm_end_utc",
        "flash_index_in_file",
        "flash_lat",
        "flash_lon",
        "flash_energy",
        "flash_area",
        "flash_quality_flag",
        "flash_time_offset_first_event",
        "flash_time_offset_last_event",
    ]

    density_rows = _build_density_grid(
        rows,
        lon_step=float(density_lon_step),
        lat_step=float(density_lat_step),
    )

    density_fields = [
        "cell_id",
        "lon_min",
        "lon_max",
        "lat_min",
        "lat_max",
        "flash_count",
        "energy_sum",
        "energy_mean",
    ]

    print(f"[GLM FNP02] Writing vector outputs: {len(rows)} flashes", flush=True)
    _write_csv(rows, paths["points_csv"], point_fields)
    _write_points_geojson(rows, paths["points_geojson"])
    _write_csv(density_rows, paths["density_grid_csv"], density_fields)

    print("[GLM FNP02] Writing transparent WGS84 PNG overlays", flush=True)
    _write_points_png(
        rows,
        paths["wgs84_points_png"],
        width=int(width),
        height=int(height),
        radius_px=int(point_radius_px),
    )
    _write_density_png(
        density_rows,
        paths["wgs84_density_png"],
        width=int(width),
        height=int(height),
    )
    _write_heatmap_png(
        rows,
        paths["wgs84_heatmap_png"],
        width=int(width),
        height=int(height),
        blur_radius_px=int(heatmap_blur_radius_px),
    )

    energies = [
        row.get("flash_energy") for row in rows
        if row.get("flash_energy") is not None and np.isfinite(row.get("flash_energy"))
    ]
    areas = [
        row.get("flash_area") for row in rows
        if row.get("flash_area") is not None and np.isfinite(row.get("flash_area"))
    ]

    duration = round(time.time() - start_time, 3)
    stats = {
        "processor": "GLM_L2_LCFA_fnp02",
        "description": "GLM flashes aggregated by one MCMIPF frame.",
        "mcmipf_file": mcmipf_info["file_name"],
        "mcmipf_start_utc": format_utc(mcmipf_info["start_utc"]),
        "mcmipf_end_utc": format_utc(mcmipf_info["end_utc"]),
        "glm_block_start_utc": format_utc(glm_block_start),
        "glm_block_end_utc": format_utc(glm_block_end),
        "matching_mode": matching_mode,
        "quality_good_only": bool(quality_good_only),
        "candidate_glm_files": len(glm_nc_paths),
        "matched_glm_files": len(selected_glm),
        "rejected_glm_files": len(rejected_glm),
        "flash_count": len(rows),
        "density_cell_count": len(density_rows),
        "energy_min": float(np.min(energies)) if energies else None,
        "energy_max": float(np.max(energies)) if energies else None,
        "energy_sum": float(np.sum(energies)) if energies else None,
        "area_min": float(np.min(areas)) if areas else None,
        "area_max": float(np.max(areas)) if areas else None,
        "area_sum": float(np.sum(areas)) if areas else None,
        "wgs84_png_width": int(width),
        "wgs84_png_height": int(height),
        "density_lon_step": float(density_lon_step),
        "density_lat_step": float(density_lat_step),
        "processing_seconds": duration,
        "glm_file_summaries": file_summaries,
    }

    manifest = {
        "processor": "GLM_L2_LCFA_fnp02",
        "anchor_mcmipf": str(mcmipf_nc_path),
        "matched_glm_files": [str(path) for path, _info in selected_glm],
        "rejected_glm_files": rejected_glm,
        "outputs": {key: str(value) for key, value in paths.items()},
        "stats": stats,
        "overlay_bounds": {
            "crs": "EPSG:4326",
            "west": -180.0,
            "south": -90.0,
            "east": 180.0,
            "north": 90.0,
        },
    }

    _write_stats_json(stats, paths["stats_json"])
    _write_manifest_json(manifest, paths["manifest_json"])
    _validate_outputs(paths)

    print(f"[GLM FNP02] Finished in {duration}s", flush=True)
    print("=" * 80 + "\n")

    return True


if __name__ == "__main__":
    print("\n" + " GLM-L2-LCFA FNP02 DIAGNOSTIC ".center(80, "="))
    current_dir = Path.cwd()
    mcmipf_candidates = sorted(current_dir.rglob("*ABI-L2-MCMIPF*.nc"))
    glm_candidates = sorted(current_dir.rglob("*GLM-L2-LCFA*.nc"))

    if not mcmipf_candidates:
        print(f"No MCMIPF NetCDF files found under: {current_dir}")
    elif not glm_candidates:
        print(f"No GLM NetCDF files found under: {current_dir}")
    else:
        run_proc_GLM_L2_LCFA_fnp02(
            mcmipf_nc_path=mcmipf_candidates[0],
            glm_nc_paths=glm_candidates,
            output_dir=current_dir / "test_outputs" / "GLM_L2_LCFA_fnp02",
            matching_mode="overlap",
        )
