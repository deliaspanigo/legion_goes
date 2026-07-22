"""
Output schema for MCMIPF FNP01 simple processing.

FNP01 is the LegionGOES True Color processing for ABI-L2-MCMIPF.
"""

from pathlib import Path

from legion_goes.pycode_01_products.common import (
    ensure_output_dir,
    parse_goes_filename,
)


def sp_mcmipf_fnp01_output_schema(nc_path, output_dir):
    """
    Build all expected output paths for MCMIPF FNP01.
    """

    output_dir = ensure_output_dir(output_dir)
    meta = parse_goes_filename(nc_path)
    prefix = meta["simple_prefix"]
    position = meta["position"]

    return {
        "goes_native_true_color_png": Path(output_dir)
        / f"{prefix}_CRS-Goes{position}_MCMIPF-fnp01-TrueColor.png",
        "goes_native_true_color_day_only_png": Path(output_dir)
        / f"{prefix}_CRS-Goes{position}_MCMIPF-fnp01-TrueColor-DayOnly.png",
        "wgs84_true_color_png": Path(output_dir)
        / f"{prefix}_CRS-WGS84_MCMIPF-fnp01-TrueColor.png",
        "wgs84_true_color_day_only_png": Path(output_dir)
        / f"{prefix}_CRS-WGS84_MCMIPF-fnp01-TrueColor-DayOnly.png",
        "wgs84_true_color_tif": Path(output_dir)
        / f"{prefix}_CRS-WGS84_MCMIPF-fnp01-TrueColor.tif",
        "mercator_true_color_png": Path(output_dir)
        / f"{prefix}_CRS-Mercator_MCMIPF-fnp01-TrueColor.png",
        "mercator_true_color_day_only_png": Path(output_dir)
        / f"{prefix}_CRS-Mercator_MCMIPF-fnp01-TrueColor-DayOnly.png",
    }

