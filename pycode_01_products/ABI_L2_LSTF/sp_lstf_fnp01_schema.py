"""
Output schema for LSTF FNP01 simple processing.

The names are intentionally the same style used by the original processor so
new functions can coexist with the current LegionGOES viewers and processors.
"""

from pathlib import Path

from legion_goes.pycode_01_products.common import (
    ensure_output_dir,
    parse_goes_filename,
)


def sp_lstf_fnp01_output_schema(nc_path, output_dir):
    """
    Build all expected output paths for LSTF FNP01.
    """

    output_dir = ensure_output_dir(output_dir)
    meta = parse_goes_filename(nc_path)
    prefix = meta["simple_prefix"]
    position = meta["position"]

    return {
        "goes_native_grey_png": Path(output_dir)
        / f"{prefix}_CRS-Goes{position}_LSTF-fnp01-Celsius-Grey.png",
        "goes_native_color_png": Path(output_dir)
        / f"{prefix}_CRS-Goes{position}_LSTF-fnp01-Celsius-Color.png",
        "wgs84_grey_png": Path(output_dir)
        / f"{prefix}_CRS-WGS84_LSTF-fnp01-Celsius-Grey.png",
        "wgs84_color_png": Path(output_dir)
        / f"{prefix}_CRS-WGS84_LSTF-fnp01-Celsius-Color.png",
        "wgs84_grey_tif": Path(output_dir)
        / f"{prefix}_CRS-WGS84_LSTF-fnp01-Celsius-Grey.tif",
        "wgs84_color_tif": Path(output_dir)
        / f"{prefix}_CRS-WGS84_LSTF-fnp01-Celsius-Color.tif",
        "mercator_grey_png": Path(output_dir)
        / f"{prefix}_CRS-Mercator_LSTF-fnp01-Celsius-Grey.png",
        "mercator_color_png": Path(output_dir)
        / f"{prefix}_CRS-Mercator_LSTF-fnp01-Celsius-Color.png",
        "statistics_general_csv": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-General.csv",
        "statistics_general_json": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-General.json",
        "statistics_pixel_csv": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-Pixel.csv",
        "statistics_pixel_json": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-Pixel.json",
        "statistics_position_csv": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-Position-Celsius.csv",
        "statistics_position_json": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-Position-Celsius.json",
        "statistics_dispersion_csv": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-Dispersion-Celsius.csv",
        "statistics_dispersion_json": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Statistics-Dispersion-Celsius.json",
        "histogram_plot_html": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Histogram-Plotly.html",
        "histogram_plot_json": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Histogram-Plotly.json",
        "histogram_plot_png": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Histogram-Plotly.png",
        "histogram_plot_pkl": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Histogram-Plotly.pkl",
        "boxplot_plot_html": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Boxplot-Plotly.html",
        "boxplot_plot_json": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Boxplot-Plotly.json",
        "boxplot_plot_png": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Boxplot-Plotly.png",
        "boxplot_plot_pkl": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Boxplot-Plotly.pkl",
        "temperature_reference_vertical_png": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Reference-Vertical.png",
        "temperature_reference_horizontal_png": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Reference-Horizontal.png",
        "temperature_reference_json": Path(output_dir)
        / f"{prefix}_LSTF-fnp01-Celsius-Reference.json",
    }
