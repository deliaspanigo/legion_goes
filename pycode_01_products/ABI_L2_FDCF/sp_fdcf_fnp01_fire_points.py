"""
FDCF FNP01 fire point extraction.

The raster PNGs are visual products. This module creates the vector-friendly
WGS84 point products associated with the same FDCF NetCDF.
"""

import csv
import json
from pathlib import Path

import numpy as np
import xarray as xr
from pyproj import Proj

from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_reference import (
    FDCF_FIRE_DETECTION_CODES,
)
from legion_goes.pycode_01_products.ABI_L2_FDCF.sp_fdcf_fnp01_schema import (
    sp_fdcf_fnp01_output_schema,
)
from legion_goes.pycode_01_products.common import ensure_input_file, ensure_output_files


FDCF_FIRE_CLASS_LABELS = {
    10: "Processed fire pixel",
    11: "Saturated fire pixel",
    12: "Cloud contaminated fire",
    13: "High probability fire",
    14: "Medium probability fire",
    15: "Low probability fire",
    30: "TF processed fire pixel",
    31: "TF saturated fire pixel",
    32: "TF cloud contaminated fire",
    33: "TF high probability fire",
    34: "TF medium probability fire",
    35: "TF low probability fire",
}


def _to_python_scalar(value):
    if value is None:
        return None

    try:
        if np.ma.is_masked(value):
            return None
    except Exception:
        pass

    if isinstance(value, np.generic):
        value = value.item()

    try:
        if isinstance(value, float) and not np.isfinite(value):
            return None
    except Exception:
        pass

    return value


def _read_optional_values(ds, variable_name, rows, cols):
    if variable_name not in ds:
        return [None] * len(rows)

    try:
        var = ds[variable_name]
        vals = var.values[rows, cols]
        attrs = var.attrs
        fill_value = attrs.get("_FillValue")
        scale_factor = attrs.get("scale_factor", 1)
        add_offset = attrs.get("add_offset", 0)
        out = []

        for val in vals:
            val = _to_python_scalar(val)

            if val is None:
                out.append(None)
                continue

            if fill_value is not None and val == _to_python_scalar(fill_value):
                out.append(None)
                continue

            try:
                val = val * float(scale_factor) + float(add_offset)
            except Exception:
                pass

            out.append(_to_python_scalar(val))

        return out
    except Exception:
        return [None] * len(rows)


def _decode_scan_angle(coord_var, indices):
    vals = coord_var.values[indices]
    attrs = coord_var.attrs
    scale_factor = float(attrs.get("scale_factor", 1))
    add_offset = float(attrs.get("add_offset", 0))
    return vals.astype(np.float64) * scale_factor + add_offset


def _write_fire_points_csv(rows, output_csv):
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "point_id",
        "row",
        "col",
        "lon",
        "lat",
        "x_scan_angle",
        "y_scan_angle",
        "fdcf_class",
        "class_name",
        "area",
        "temp",
        "power",
        "dqf",
    ]

    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_fire_points_geojson(rows, output_geojson):
    output_geojson = Path(output_geojson)
    output_geojson.parent.mkdir(parents=True, exist_ok=True)

    features = []

    for row in rows:
        lon = row.get("lon")
        lat = row.get("lat")

        if lon is None or lat is None:
            continue

        if not np.isfinite(lon) or not np.isfinite(lat):
            continue

        props = {
            key: value
            for key, value in row.items()
            if key not in ["lon", "lat"]
        }

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)],
                },
                "properties": props,
            }
        )

    payload = {
        "type": "FeatureCollection",
        "name": output_geojson.stem,
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326",
            },
        },
        "features": features,
    }

    output_geojson.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def extract_fdcf_fire_points(nc_path):
    """
    Extract fire pixels from the native FDCF Mask array.

    The returned rows are the in-memory source of truth used by CSV, GeoJSON,
    and transparent fire-point PNG overlays.
    """

    rows_out = []

    with xr.open_dataset(nc_path, mask_and_scale=False) as ds:
        if "Mask" not in ds:
            raise ValueError("Mask variable was not found in the FDCF NetCDF file.")

        mask = ds["Mask"].values
        mask_round = np.rint(mask).astype(np.int16, copy=False)
        fire_mask = np.isin(mask_round, sorted(FDCF_FIRE_DETECTION_CODES))
        rows, cols = np.where(fire_mask)

        if len(rows) > 0:
            projection_name = "goes_imager_projection"

            if projection_name not in ds:
                projection_candidates = [
                    name
                    for name in ds.variables
                    if "projection" in name.lower()
                ]

                if not projection_candidates:
                    raise ValueError("GOES projection variable was not found.")

                projection_name = projection_candidates[0]

            projection_attrs = ds[projection_name].attrs
            perspective_point_height = float(projection_attrs["perspective_point_height"])
            semi_major_axis = float(projection_attrs["semi_major_axis"])
            semi_minor_axis = float(projection_attrs["semi_minor_axis"])
            longitude_of_projection_origin = float(
                projection_attrs["longitude_of_projection_origin"]
            )
            sweep_angle_axis = projection_attrs.get("sweep_angle_axis", "x")

            x_scan = _decode_scan_angle(ds["x"], cols)
            y_scan = _decode_scan_angle(ds["y"], rows)

            geos_proj = Proj(
                proj="geos",
                h=perspective_point_height,
                lon_0=longitude_of_projection_origin,
                sweep=sweep_angle_axis,
                a=semi_major_axis,
                b=semi_minor_axis,
            )

            lon, lat = geos_proj(
                x_scan * perspective_point_height,
                y_scan * perspective_point_height,
                inverse=True,
            )

            area_values = _read_optional_values(ds, "Area", rows, cols)
            temp_values = _read_optional_values(ds, "Temp", rows, cols)
            power_values = _read_optional_values(ds, "Power", rows, cols)
            dqf_values = _read_optional_values(ds, "DQF", rows, cols)
            classes = mask_round[rows, cols]

            for i in range(len(rows)):
                fdcf_class = int(classes[i])
                rows_out.append(
                    {
                        "point_id": i + 1,
                        "row": int(rows[i]),
                        "col": int(cols[i]),
                        "lon": _to_python_scalar(float(lon[i])),
                        "lat": _to_python_scalar(float(lat[i])),
                        "x_scan_angle": _to_python_scalar(float(x_scan[i])),
                        "y_scan_angle": _to_python_scalar(float(y_scan[i])),
                        "fdcf_class": fdcf_class,
                        "class_name": FDCF_FIRE_CLASS_LABELS.get(
                            fdcf_class,
                            "Fire pixel",
                        ),
                        "area": area_values[i],
                        "temp": temp_values[i],
                        "power": power_values[i],
                        "dqf": dqf_values[i],
                    }
                )

    return rows_out


def export_fdcf_fire_points(nc_path, output_csv, output_geojson):
    """
    Extract fire pixels from the native FDCF Mask array and write WGS84 points.
    """

    rows_out = extract_fdcf_fire_points(nc_path)
    _write_fire_points_csv(rows_out, output_csv)
    _write_fire_points_geojson(rows_out, output_geojson)

    return rows_out


def sp_fdcf_fnp01_fire_points(nc_path, output_dir, fire_points=None):
    """
    Generate FDCF FNP01 WGS84 fire-point CSV and GeoJSON files.
    """

    file_path = ensure_input_file(nc_path)
    outputs = sp_fdcf_fnp01_output_schema(file_path, output_dir)

    print("[FDCF FNP01 Fire Points] Exporting WGS84 fire points...", flush=True)

    if fire_points is None:
        fire_points = export_fdcf_fire_points(
            nc_path=str(file_path),
            output_csv=outputs["fire_points_csv"],
            output_geojson=outputs["fire_points_geojson"],
        )
    else:
        _write_fire_points_csv(fire_points, outputs["fire_points_csv"])
        _write_fire_points_geojson(fire_points, outputs["fire_points_geojson"])

    result = {
        "fire_points_csv": outputs["fire_points_csv"],
        "fire_points_geojson": outputs["fire_points_geojson"],
    }
    ensure_output_files(result)

    print(
        f"[FDCF FNP01 Fire Points] Fire points exported: {len(fire_points)}",
        flush=True,
    )

    return result

