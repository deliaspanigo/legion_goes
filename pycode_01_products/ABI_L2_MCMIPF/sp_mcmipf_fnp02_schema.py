"""
Output schema for MCMIPF FNP02 simple processing.

FNP02 is the LegionGOES colorized IR cloud processing for ABI-L2-MCMIPF.
"""

from pathlib import Path

from legion_goes.pycode_01_products.common import (
    ensure_output_dir,
    parse_goes_filename,
)


def sp_mcmipf_fnp02_output_schema(nc_path, output_dir):
    """
    Build all expected output paths for MCMIPF FNP02.
    """

    output_dir = ensure_output_dir(output_dir)
    meta = parse_goes_filename(nc_path)
    prefix = meta["simple_prefix"]
    position = meta["position"]

    return {
        "goes_native_ir_png": Path(output_dir)
        / f"{prefix}_CRS-Goes{position}_MCMIPF-fnp02-IR-Colorized.png",
        "goes_native_transparent_png": Path(output_dir)
        / f"{prefix}_CRS-Goes{position}_MCMIPF-fnp02-IR-Colorized-Transparent.png",
        "goes_native_selected_clouds_png": Path(output_dir)
        / f"{prefix}_CRS-Goes{position}_MCMIPF-fnp02-IR-selected_clouds.png",
        "wgs84_ir_png": Path(output_dir)
        / f"{prefix}_CRS-WGS84_MCMIPF-fnp02-IR-Colorized.png",
        "wgs84_transparent_png": Path(output_dir)
        / f"{prefix}_CRS-WGS84_MCMIPF-fnp02-IR-Colorized-Transparent.png",
        "wgs84_selected_clouds_png": Path(output_dir)
        / f"{prefix}_CRS-WGS84_MCMIPF-fnp02-IR-selected_clouds.png",
        "wgs84_ir_tif": Path(output_dir)
        / f"{prefix}_CRS-WGS84_MCMIPF-fnp02-IR-Colorized.tif",
        "mercator_ir_png": Path(output_dir)
        / f"{prefix}_CRS-Mercator_MCMIPF-fnp02-IR-Colorized.png",
        "mercator_transparent_png": Path(output_dir)
        / f"{prefix}_CRS-Mercator_MCMIPF-fnp02-IR-Colorized-Transparent.png",
        "mercator_selected_clouds_png": Path(output_dir)
        / f"{prefix}_CRS-Mercator_MCMIPF-fnp02-IR-selected_clouds.png",
    }
