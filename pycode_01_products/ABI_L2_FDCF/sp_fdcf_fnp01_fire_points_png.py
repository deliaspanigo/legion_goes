"""
FDCF FNP01 fire-point PNG layers.

The CSV and GeoJSON products keep the detected fire pixels as vector-friendly
records. This module draws the same detections into transparent PNG overlays
for each map reference system used by LegionGOES viewers.
"""

import time

import numpy as np
import xarray as xr
from PIL import Image, ImageDraw
from pyproj import Transformer

from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_fire_points import (
    extract_fdcf_fire_points,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_reference import (
    FDCF_FIRE_DETECTION_CODES,
    fdcf_palette_from_abi_yaml,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_schema import (
    FDCF_COLOR_VARIANTS,
    sp_fdcf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.common import ensure_input_file, ensure_output_files


WGS84_WIDTH = 3600
WGS84_HEIGHT = 1800
MERCATOR_WIDTH = 3600
MERCATOR_HEIGHT = 3400
WEB_MERCATOR_MAX = 20037508.342789244


def _fire_color(row, variant):
    palette = fdcf_palette_from_abi_yaml(variant=variant)
    category = int(row["fdcf_class"])
    entry = palette.get(category)

    if entry:
        alpha = int(entry.get("a", 255))
        return (
            int(entry["r"]),
            int(entry["g"]),
            int(entry["b"]),
            max(alpha, 220),
        )

    if category in FDCF_FIRE_DETECTION_CODES:
        return (255, 90, 0, 245)

    return (255, 255, 255, 220)


def _draw_disc(draw, x, y, radius, fill, outline=(255, 255, 255, 210)):
    x = int(round(x))
    y = int(round(y))
    radius = int(radius)
    box = (x - radius, y - radius, x + radius, y + radius)
    draw.ellipse(box, fill=fill, outline=outline, width=1)


def _write_points_png(rows, output_png, width, height, projector, variant, radius):
    image = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")

    for row in rows:
        xy = projector(row)
        if xy is None:
            continue

        x, y = xy
        if not np.isfinite(x) or not np.isfinite(y):
            continue

        if x < -radius or y < -radius or x > width + radius or y > height + radius:
            continue

        _draw_disc(
            draw=draw,
            x=x,
            y=y,
            radius=radius,
            fill=_fire_color(row, variant),
        )

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)


def _project_wgs84(row):
    lon = row.get("lon")
    lat = row.get("lat")

    if lon is None or lat is None:
        return None

    lon = float(lon)
    lat = float(lat)
    x = (lon + 180.0) / 360.0 * WGS84_WIDTH
    y = (90.0 - lat) / 180.0 * WGS84_HEIGHT
    return x, y


_TO_WEB_MERCATOR = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def _project_mercator(row):
    lon = row.get("lon")
    lat = row.get("lat")

    if lon is None or lat is None:
        return None

    lon = float(lon)
    lat = max(min(float(lat), 85.05112878), -85.05112878)
    mx, my = _TO_WEB_MERCATOR.transform(lon, lat)
    x = (mx + WEB_MERCATOR_MAX) / (2.0 * WEB_MERCATOR_MAX) * MERCATOR_WIDTH
    y = (WEB_MERCATOR_MAX - my) / (2.0 * WEB_MERCATOR_MAX) * MERCATOR_HEIGHT
    return x, y


def _project_goes_native(row):
    col = row.get("col")
    native_row = row.get("row")

    if col is None or native_row is None:
        return None

    return float(col), float(native_row)


def _native_shape(nc_path):
    with xr.open_dataset(nc_path, mask_and_scale=False) as ds:
        if "Mask" not in ds:
            raise ValueError("Mask variable was not found in the FDCF NetCDF file.")

        shape = ds["Mask"].shape

    if len(shape) != 2:
        raise ValueError(f"Expected a 2-D FDCF Mask array, got shape: {shape}")

    return int(shape[1]), int(shape[0])


def sp_fdcf_fnp01_fire_points_png_wgs84(nc_path, output_dir, fire_points=None):
    file_path = ensure_input_file(nc_path)
    outputs = sp_fdcf_fnp01_output_schema(file_path, output_dir)
    rows = fire_points if fire_points is not None else extract_fdcf_fire_points(file_path)
    result = {}

    print("[FDCF FNP01 Fire Points PNG WGS84] Writing transparent PNG layers...", flush=True)

    for color_name in FDCF_COLOR_VARIANTS:
        key = f"wgs84_fire_points_{color_name}_png"
        _write_points_png(
            rows=rows,
            output_png=outputs[key],
            width=WGS84_WIDTH,
            height=WGS84_HEIGHT,
            projector=_project_wgs84,
            variant=color_name,
            radius=5,
        )
        result[key] = outputs[key]

    ensure_output_files(result)
    return result


def sp_fdcf_fnp01_fire_points_png_mercator(nc_path, output_dir, fire_points=None):
    file_path = ensure_input_file(nc_path)
    outputs = sp_fdcf_fnp01_output_schema(file_path, output_dir)
    rows = fire_points if fire_points is not None else extract_fdcf_fire_points(file_path)
    result = {}

    print("[FDCF FNP01 Fire Points PNG Mercator] Writing transparent PNG layers...", flush=True)

    for color_name in FDCF_COLOR_VARIANTS:
        key = f"mercator_fire_points_{color_name}_png"
        _write_points_png(
            rows=rows,
            output_png=outputs[key],
            width=MERCATOR_WIDTH,
            height=MERCATOR_HEIGHT,
            projector=_project_mercator,
            variant=color_name,
            radius=5,
        )
        result[key] = outputs[key]

    ensure_output_files(result)
    return result


def sp_fdcf_fnp01_fire_points_png_goes_original(nc_path, output_dir, fire_points=None):
    file_path = ensure_input_file(nc_path)
    outputs = sp_fdcf_fnp01_output_schema(file_path, output_dir)
    rows = fire_points if fire_points is not None else extract_fdcf_fire_points(file_path)
    width, height = _native_shape(file_path)
    result = {}

    print("[FDCF FNP01 Fire Points PNG GOES original] Writing transparent PNG layers...", flush=True)

    for color_name in FDCF_COLOR_VARIANTS:
        key = f"goes_native_fire_points_{color_name}_png"
        _write_points_png(
            rows=rows,
            output_png=outputs[key],
            width=width,
            height=height,
            projector=_project_goes_native,
            variant=color_name,
            radius=6,
        )
        result[key] = outputs[key]

    ensure_output_files(result)
    return result


def sp_fdcf_fnp01_fire_points_png(nc_path, output_dir, proc_mode="viewer", fire_points=None):
    """
    Generate transparent fire-point PNG overlays for a processing mode.
    """

    start_time = time.time()
    proc_mode = str(proc_mode).strip().lower()
    outputs = {}

    if proc_mode not in {"operative", "viewer", "full"}:
        raise ValueError(
            "Unsupported proc_mode for fire-point PNGs: "
            f"{proc_mode}. Use 'operative', 'viewer', or 'full'."
        )

    rows = fire_points if fire_points is not None else extract_fdcf_fire_points(nc_path)

    if proc_mode in {"viewer", "full"}:
        outputs.update(
            sp_fdcf_fnp01_fire_points_png_goes_original(
                nc_path,
                output_dir,
                fire_points=rows,
            )
        )

    outputs.update(
        sp_fdcf_fnp01_fire_points_png_wgs84(
            nc_path,
            output_dir,
            fire_points=rows,
        )
    )

    if proc_mode in {"viewer", "full"}:
        outputs.update(
            sp_fdcf_fnp01_fire_points_png_mercator(
                nc_path,
                output_dir,
                fire_points=rows,
            )
        )

    print(
        f"[FDCF FNP01 Fire Points PNG] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return outputs
