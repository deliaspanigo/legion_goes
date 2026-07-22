"""
FDCF reference metadata.

This module is the LegionGOES source of truth for ABI-L2-FDCF Mask
categories, detection classes, and Satpy visual colors.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np


FDCF_PUG_PDF_URL = "https://www.goes-r.gov/users/docs/PUG-L2+-vol5.pdf"
FDCF_PUG_REFERENCE = "GOES-R Series Product Definition and Users' Guide (PUG), Volume 5: Level 2+ Products; Fire/Hot Spot Characterization; Fire Mask Flag Values and Meanings."

FDCF_MASK_CATEGORIES = [
    (0, "unprocessed_pixel", "Unprocessed pixel"),
    (10, "good_fire_pixel", "Good fire pixel"),
    (11, "saturated_fire_pixel", "Saturated fire pixel"),
    (12, "cloud_contaminated_fire_pixel", "Cloud contaminated fire pixel"),
    (13, "high_probability_fire_pixel", "High probability fire pixel"),
    (14, "medium_probability_fire_pixel", "Medium probability fire pixel"),
    (15, "low_probability_fire_pixel", "Low probability fire pixel"),
    (30, "temporally_filtered_good_fire_pixel", "Temporally filtered good fire pixel"),
    (31, "temporally_filtered_saturated_fire_pixel", "Temporally filtered saturated fire pixel"),
    (32, "temporally_filtered_cloud_contaminated_fire_pixel", "Temporally filtered cloud contaminated fire pixel"),
    (33, "temporally_filtered_high_probability_fire_pixel", "Temporally filtered high probability fire pixel"),
    (34, "temporally_filtered_medium_probability_fire_pixel", "Temporally filtered medium probability fire pixel"),
    (35, "temporally_filtered_low_probability_fire_pixel", "Temporally filtered low probability fire pixel"),
    (40, "off_earth_pixel", "Off-earth pixel"),
    (50, "LZA_block_out_zone", "Local zenith angle block-out zone"),
    (60, "SZA_or_glint_angle_block_out_zone", "Solar zenith angle or glint angle block-out zone"),
    (100, "processed_no_fire_pixel", "Processed no-fire pixel"),
    (120, "missing_input_3.89um_pixel", "Missing input 3.89 um pixel"),
    (121, "missing_input_11.19um_pixel", "Missing input 11.19 um pixel"),
    (123, "saturated_input_3.89um_pixel", "Saturated input 3.89 um pixel"),
    (124, "saturated_input_11.19um_pixel", "Saturated input 11.19 um pixel"),
    (125, "invalid_input_radiance_value", "Invalid input radiance value"),
    (126, "below_threshold_input_3.89um_pixel", "Below-threshold input 3.89 um pixel"),
    (127, "below_threshold_input_11.19um_pixel", "Below-threshold input 11.19 um pixel"),
    (150, "invalid_ecosystem_UMD_land_cover_type_sea_water_or_MODIS_land_mask_types_or_framework_desert_mask_type_bright_desert", "Invalid ecosystem: UMD sea water, MODIS land-mask type, or framework bright desert"),
    (151, "invalid_ecosystem_USGS_type_sea_water", "Invalid ecosystem: USGS sea water"),
    (152, "invalid_ecosystem_USGS_types_coastline_fringe_or_compound_coastlines", "Invalid ecosystem: USGS coastline fringe or compound coastlines"),
    (153, "invalid_ecosystem_USGS_types_inland_water_or_water_and_island_fringe_or_land_and_water_shore_or_land_and_water_rivers", "Invalid ecosystem: USGS inland water, water/island fringe, shore, or rivers"),
    (170, "no_background_value_could_be_computed", "No background value could be computed"),
    (180, "conversion_error_between_BT_and_radiance", "Conversion error between brightness temperature and radiance"),
    (182, "conversion_error_radiance_to_adjusted_BT", "Conversion error from radiance to adjusted brightness temperature"),
    (185, "modified_Dozier_technique_bisection_method_invalid_computed_BT", "Modified Dozier bisection method: invalid computed brightness temperature"),
    (186, "modifed_Dozier_technique_Newton_method_invalid_computed_radiance", "Modified Dozier Newton method: invalid computed radiance"),
    (187, "modifed_Dozier_technique_Newton_method_invalid_computed_fire_brighness_temp", "Modified Dozier Newton method: invalid computed fire brightness temperature"),
    (188, "modifed_Dozier_technique_Newton_method_invalid_computed_fire_area", "Modified Dozier Newton method: invalid computed fire area"),
    (200, "cloud_pixel_detected_by_11.19um_threshold_test", "Cloud pixel detected by 11.19 um threshold test"),
    (201, "cloud_pixel_detected_by_3.89um_minus_11.19um_threshold_and_freezing_test", "Cloud pixel detected by 3.89 um minus 11.19 um threshold and freezing test"),
    (205, "cloud_pixel_detected_by_negative_difference_3.89um_minus_11.19um_threshold_test", "Cloud pixel detected by negative difference 3.89 um minus 11.19 um threshold test"),
    (210, "cloud_pixel_detected_by_positive_difference_3.89um_minus_11.19um_threshold_test", "Cloud pixel detected by positive difference 3.89 um minus 11.19 um threshold test"),
    (215, "cloud_pixel_detected_by_albedo_threshold_test", "Cloud pixel detected by albedo threshold test"),
    (220, "cloud_pixel_detected_by_12.27um_threshold_test", "Cloud pixel detected by 12.27 um threshold test"),
    (225, "cloud_pixel_detected_by_negative_difference_11.19um_minus_12.27um_threshold_test", "Cloud pixel detected by negative difference 11.19 um minus 12.27 um threshold test"),
    (230, "cloud_pixel_detected_by_positive_difference_11.19um_minus_12.27um_threshold_test", "Cloud pixel detected by positive difference 11.19 um minus 12.27 um threshold test"),
    (240, "cloud_edge_pixel_detected_by_along_scan_reflectivity_and_3.89um_threshold_test", "Cloud-edge pixel detected by along-scan reflectivity and 3.89 um threshold test"),
    (245, "cloud_edge_pixel_detected_by_along_scan_reflectivity_and_albedo_threshold_test", "Cloud-edge pixel detected by along-scan reflectivity and albedo threshold test"),
]

FDCF_FIRE_DETECTION_CODES = {10, 11, 12, 13, 14, 15, 30, 31, 32, 33, 34, 35}


def _category_group(code: int) -> str:
    if code in {10, 11, 12, 13, 14, 15}:
        return "fire"
    if code in {30, 31, 32, 33, 34, 35}:
        return "temporally_filtered_fire"
    if code in {200, 201, 205, 210, 215, 220, 225, 230, 240, 245}:
        return "cloud"
    if code in {150, 151, 152, 153}:
        return "surface_type"
    if code in {40, 50, 60}:
        return "geometry_or_glint"
    if code in {120, 121, 123, 124, 125, 126, 127}:
        return "input_data"
    if code in {170, 180, 182, 185, 186, 187, 188}:
        return "algorithm_failure"
    if code == 100:
        return "processed_no_fire"
    if code == 0:
        return "unprocessed"
    return "other"


def fdcf_official_mask_categories() -> List[Dict[str, object]]:
    out = []
    for code, flag_meaning, description in FDCF_MASK_CATEGORIES:
        out.append(
            {
                "code": int(code),
                "flag_meaning": flag_meaning,
                "description": description,
                "category_group": _category_group(int(code)),
                "is_fire_detection": int(code) in FDCF_FIRE_DETECTION_CODES,
                "source_pdf_url": FDCF_PUG_PDF_URL,
                "source_reference": FDCF_PUG_REFERENCE,
                "source_variable": "Mask",
                "source_product": "ABI-L2-FDCF",
            }
        )
    return out


def _python_code_root() -> Path:
    return Path(__file__).resolve().parents[7]


def _abi_enhancement_yaml() -> Path:
    return _python_code_root() / "legion_goes" / "satpy_config" / "enhancements" / "abi.yaml"


def _variant_to_enhancement(variant: str) -> str:
    match = re.search(r"(?:color|fn)0*([0-9]+)", variant or "", flags=re.IGNORECASE)
    if not match:
        return "my_fdc_fn01"
    return f"my_fdc_fn{int(match.group(1)):02d}"


def fdcf_palette_from_abi_yaml(variant: str = "color01", yaml_path: Optional[str] = None) -> Dict[int, Dict[str, object]]:
    path = Path(yaml_path) if yaml_path else _abi_enhancement_yaml()
    enhancement = _variant_to_enhancement(variant)

    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_block = False
    palette = {}
    block_re = re.compile(rf"^\s{{2}}{re.escape(enhancement)}\s*:\s*$")
    next_block_re = re.compile(r"^\s{2}[A-Za-z0-9_]+\s*:\s*$")
    color_re = re.compile(
        r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\].*#\s*(-?\d+)\s*:\s*(.*)$"
    )

    for line in text:
        if block_re.match(line):
            in_block = True
            continue

        if in_block and next_block_re.match(line):
            break

        if not in_block:
            continue

        m = color_re.search(line)
        if not m:
            continue

        r, g, b, a, code, label = m.groups()
        code_i = int(code)
        palette[code_i] = {
            "r": int(r),
            "g": int(g),
            "b": int(b),
            "a": int(a),
            "hex": f"#{int(r):02X}{int(g):02X}{int(b):02X}",
            "satpy_label": re.sub(r"\*+", "", label).strip(),
            "enhancement": enhancement,
            "variant": f"color{int(re.search(r'([0-9]+)$', enhancement).group(1)):02d}",
        }

    return palette


def fdcf_mask_counts(nc_path: Optional[str] = None) -> Dict[int, int]:
    if not nc_path:
        return {}

    import xarray as xr

    with xr.open_dataset(nc_path, mask_and_scale=False) as ds:
        if "Mask" not in ds:
            raise ValueError("Mask variable was not found in the FDCF NetCDF file.")
        values = np.rint(ds["Mask"].values).astype(np.int16, copy=False)

    unique, counts = np.unique(values[np.isfinite(values)], return_counts=True)
    return {int(k): int(v) for k, v in zip(unique, counts)}


def fdcf_reference_table(
    variant: str = "color01",
    nc_path: Optional[str] = None,
    active_only: bool = False,
    yaml_path: Optional[str] = None,
) -> List[Dict[str, object]]:
    palette = fdcf_palette_from_abi_yaml(variant=variant, yaml_path=yaml_path)
    counts = fdcf_mask_counts(nc_path=nc_path) if nc_path else {}

    rows = []
    for row in fdcf_official_mask_categories():
        code = int(row["code"])
        color_info = palette.get(code, {})
        count = int(counts.get(code, 0))
        visible_alpha = int(color_info.get("a", 0))
        present = count > 0
        visible_in_selected_png = visible_alpha > 0 and bool(color_info)

        if active_only and not (present and visible_in_selected_png):
            continue

        out = dict(row)
        out.update(
            {
                "variant": color_info.get("variant", variant),
                "enhancement": color_info.get("enhancement", _variant_to_enhancement(variant)),
                "r": color_info.get("r"),
                "g": color_info.get("g"),
                "b": color_info.get("b"),
                "a": color_info.get("a"),
                "hex": color_info.get("hex"),
                "satpy_label": color_info.get("satpy_label"),
                "visible_in_selected_png": visible_in_selected_png,
                "present_in_current_frame": present,
                "pixel_count": count,
            }
        )
        rows.append(out)

    return rows


def write_fdcf_reference_json(output: str, variant: str = "color01", nc_path: Optional[str] = None, active_only: bool = False) -> str:
    payload = {
        "product": "ABI-L2-FDCF",
        "variable": "Mask",
        "variant": variant,
        "active_only": bool(active_only),
        "source_pdf_url": FDCF_PUG_PDF_URL,
        "source_reference": FDCF_PUG_REFERENCE,
        "categories": fdcf_reference_table(
            variant=variant,
            nc_path=nc_path,
            active_only=active_only,
        ),
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def write_fdcf_reference_csv(output: str, variant: str = "color01", nc_path: Optional[str] = None, active_only: bool = False) -> str:
    rows = fdcf_reference_table(
        variant=variant,
        nc_path=nc_path,
        active_only=active_only,
    )
    fieldnames = [
        "code",
        "flag_meaning",
        "description",
        "category_group",
        "is_fire_detection",
        "source_product",
        "source_variable",
        "source_pdf_url",
        "source_reference",
        "variant",
        "enhancement",
        "r",
        "g",
        "b",
        "a",
        "hex",
        "satpy_label",
        "visible_in_selected_png",
        "present_in_current_frame",
        "pixel_count",
    ]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return str(path)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export ABI-L2-FDCF reference metadata.")
    parser.add_argument("--variant", default="color01")
    parser.add_argument("--nc-path", default=None)
    parser.add_argument("--active-only", action="store_true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.format == "csv":
        write_fdcf_reference_csv(
            output=args.output,
            variant=args.variant,
            nc_path=args.nc_path,
            active_only=args.active_only,
        )
    else:
        write_fdcf_reference_json(
            output=args.output,
            variant=args.variant,
            nc_path=args.nc_path,
            active_only=args.active_only,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
