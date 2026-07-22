"""
Output schema for FDCF FNP01 simple processing.

The names intentionally keep the existing LegionGOES viewer style:
CRS-WGS84, CRS-Mercator, CRS-GoesEAST/WEST, FDCF-fnp01-colorXX.
"""

from pathlib import Path

from legion_goes.pycode_01_products.common import (
    ensure_output_dir,
    parse_goes_filename,
)


FDCF_COLOR_VARIANTS = {
    "color01": "my_fdc_fn01",
    "color02": "my_fdc_fn02",
    "color03": "my_fdc_fn03",
    "color04": "my_fdc_fn04",
    "color05": "my_fdc_fn05",
}


def sp_fdcf_fnp01_output_schema(nc_path, output_dir):
    """
    Build all expected output paths for FDCF FNP01.
    """

    output_dir = ensure_output_dir(output_dir)
    meta = parse_goes_filename(nc_path)
    prefix = meta["simple_prefix"]
    position = meta["position"]

    outputs = {}

    for color_name in FDCF_COLOR_VARIANTS:
        outputs[f"goes_native_{color_name}_png"] = (
            Path(output_dir)
            / f"{prefix}_CRS-Goes{position}_FDCF-fnp01-{color_name}.png"
        )
        outputs[f"wgs84_{color_name}_tif"] = (
            Path(output_dir)
            / f"{prefix}_CRS-WGS84_FDCF-fnp01-{color_name}.tif"
        )
        outputs[f"wgs84_{color_name}_png"] = (
            Path(output_dir)
            / f"{prefix}_CRS-WGS84_FDCF-fnp01-{color_name}.png"
        )
        outputs[f"mercator_{color_name}_png"] = (
            Path(output_dir)
            / f"{prefix}_CRS-Mercator_FDCF-fnp01-{color_name}.png"
        )
        outputs[f"{color_name}_reference_full_csv"] = (
            Path(output_dir)
            / f"{prefix}_FDCF-fnp01-{color_name}-Reference-Full.csv"
        )
        outputs[f"{color_name}_reference_full_json"] = (
            Path(output_dir)
            / f"{prefix}_FDCF-fnp01-{color_name}-Reference-Full.json"
        )
        outputs[f"{color_name}_reference_active_csv"] = (
            Path(output_dir)
            / f"{prefix}_FDCF-fnp01-{color_name}-Reference-Active.csv"
        )
        outputs[f"{color_name}_reference_active_json"] = (
            Path(output_dir)
            / f"{prefix}_FDCF-fnp01-{color_name}-Reference-Active.json"
        )

    outputs["fire_points_csv"] = (
        Path(output_dir) / f"{prefix}_CRS-WGS84_FDCF-fnp01-FirePoints.csv"
    )
    outputs["fire_points_geojson"] = (
        Path(output_dir) / f"{prefix}_CRS-WGS84_FDCF-fnp01-FirePoints.geojson"
    )

    for color_name in FDCF_COLOR_VARIANTS:
        outputs[f"goes_native_fire_points_{color_name}_png"] = (
            Path(output_dir)
            / f"{prefix}_CRS-Goes{position}_FDCF-fnp01-FirePoints-{color_name}.png"
        )
        outputs[f"wgs84_fire_points_{color_name}_png"] = (
            Path(output_dir)
            / f"{prefix}_CRS-WGS84_FDCF-fnp01-FirePoints-{color_name}.png"
        )
        outputs[f"mercator_fire_points_{color_name}_png"] = (
            Path(output_dir)
            / f"{prefix}_CRS-Mercator_FDCF-fnp01-FirePoints-{color_name}.png"
        )

    return outputs

