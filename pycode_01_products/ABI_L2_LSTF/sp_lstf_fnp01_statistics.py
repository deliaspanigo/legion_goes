"""
LSTF FNP01 - statistics and reference products.

This module keeps statistics separate from map rendering. All numeric
statistics are computed from the original GOES grid after converting LST from
Kelvin to Celsius. No WGS84, Mercator, or GOES-display PNG is used here.
"""

import csv
import json
import pickle
import time
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image, ImageDraw, ImageFont
from satpy import Scene

from legion_goes.pycode_01_products.common import (
    ensure_input_file,
    ensure_output_files,
    parse_goes_filename,
    satpy_reader_chunks,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_reference import (
    sp_lstf_fnp01_reference,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_schema import (
    sp_lstf_fnp01_output_schema,
)


LSTF_REFERENCE_COLORS = [
    (148, 0, 211),
    (65, 105, 225),
    (0, 255, 255),
    (34, 139, 34),
    (255, 255, 0),
    (255, 140, 0),
    (255, 0, 0),
    (128, 0, 0),
]


def _safe_float(value, digits=4):
    if value is None:
        return None
    value = float(value)
    if not np.isfinite(value):
        return None
    return round(value, digits)


def _read_original_lst_celsius(nc_path):
    """
    Read the original ABI-L2-LSTF grid and return Celsius values.
    """

    file_path = ensure_input_file(nc_path)

    scene = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )
    scene.load(["LST"])

    data = scene["LST"].data
    if hasattr(data, "compute"):
        data = data.compute()

    values_kelvin = np.ma.filled(data, np.nan).astype("float64", copy=False)
    values_celsius = values_kelvin - 273.15

    return values_celsius


def _valid_lst_values(values_celsius, min_valid=-100.0, max_valid=100.0):
    """
    Extract valid Celsius values from the original GOES grid.
    """

    flat = np.asarray(values_celsius, dtype="float64").ravel()
    mask = np.isfinite(flat) & (flat >= min_valid) & (flat <= max_valid)
    return flat[mask]


def _write_rows_csv(rows, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    keys = sorted({key for row in rows for key in row.keys()})
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_rows_json(rows, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_general_info_table(nc_path, values_celsius, valid_values):
    meta = parse_goes_filename(nc_path)
    rows, cols = values_celsius.shape
    total = int(values_celsius.size)
    finite = int(np.isfinite(values_celsius).sum())
    valid = int(valid_values.size)

    return [
        {"Measure": "Input file", "Value": Path(nc_path).name},
        {"Measure": "Product", "Value": "ABI-L2-LSTF"},
        {"Measure": "Satellite", "Value": meta["satellite"]},
        {"Measure": "GOES position", "Value": meta["position"]},
        {"Measure": "Start timestamp", "Value": meta["start_timestamp"]},
        {"Measure": "Statistics source", "Value": "Original GOES NetCDF grid"},
        {"Measure": "Unit", "Value": "Celsius"},
        {"Measure": "Native rows", "Value": rows},
        {"Measure": "Native columns", "Value": cols},
        {"Measure": "Native total pixels", "Value": total},
        {"Measure": "Finite pixels", "Value": finite},
        {"Measure": "Valid statistics pixels", "Value": valid},
    ]


def _build_pixel_info_table(values_celsius, valid_values, min_valid=-100.0, max_valid=100.0):
    total = int(values_celsius.size)
    finite_mask = np.isfinite(values_celsius)
    finite = int(finite_mask.sum())
    valid = int(valid_values.size)

    below = int((finite_mask & (values_celsius < min_valid)).sum())
    above = int((finite_mask & (values_celsius > max_valid)).sum())
    nan_count = int(total - finite)

    return [
        {"Measure": "Total native pixels", "Value": total},
        {"Measure": "Finite pixels", "Value": finite},
        {"Measure": "Valid pixels used in statistics", "Value": valid},
        {"Measure": "NaN or masked pixels", "Value": nan_count},
        {"Measure": f"Finite pixels below {min_valid} C", "Value": below},
        {"Measure": f"Finite pixels above {max_valid} C", "Value": above},
        {"Measure": "Valid fraction of total", "Value": _safe_float(valid / total, 6)},
        {"Measure": "Valid fraction of finite", "Value": _safe_float(valid / finite, 6) if finite else None},
    ]


def _build_position_stats_table(valid_values):
    qs = np.quantile(
        valid_values,
        [0.00, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 1.00],
    )

    return [
        {"Measure": "n", "Value": int(valid_values.size)},
        {"Measure": "Minimum", "Value": _safe_float(qs[0])},
        {"Measure": "Percentile 1", "Value": _safe_float(qs[1])},
        {"Measure": "Percentile 5", "Value": _safe_float(qs[2])},
        {"Measure": "First quartile", "Value": _safe_float(qs[3])},
        {"Measure": "Mean", "Value": _safe_float(np.mean(valid_values))},
        {"Measure": "Median", "Value": _safe_float(qs[4])},
        {"Measure": "Third quartile", "Value": _safe_float(qs[5])},
        {"Measure": "Percentile 95", "Value": _safe_float(qs[6])},
        {"Measure": "Percentile 99", "Value": _safe_float(qs[7])},
        {"Measure": "Maximum", "Value": _safe_float(qs[8])},
    ]


def _build_dispersion_stats_table(valid_values):
    q1 = float(np.quantile(valid_values, 0.25))
    q3 = float(np.quantile(valid_values, 0.75))
    min_value = float(np.min(valid_values))
    max_value = float(np.max(valid_values))

    return [
        {"Measure": "n", "Value": int(valid_values.size)},
        {"Measure": "Variance", "Value": _safe_float(np.var(valid_values, ddof=1))},
        {"Measure": "Standard deviation", "Value": _safe_float(np.std(valid_values, ddof=1))},
        {"Measure": "Interquartile range", "Value": _safe_float(q3 - q1)},
        {"Measure": "Range", "Value": _safe_float(max_value - min_value)},
        {"Measure": "Median absolute deviation", "Value": _safe_float(np.median(np.abs(valid_values - np.median(valid_values))))},
    ]


def _stats_dict(valid_values):
    return {
        "n": int(valid_values.size),
        "min": float(np.min(valid_values)),
        "p01": float(np.quantile(valid_values, 0.01)),
        "p05": float(np.quantile(valid_values, 0.05)),
        "q1": float(np.quantile(valid_values, 0.25)),
        "mean": float(np.mean(valid_values)),
        "median": float(np.quantile(valid_values, 0.50)),
        "q3": float(np.quantile(valid_values, 0.75)),
        "p95": float(np.quantile(valid_values, 0.95)),
        "p99": float(np.quantile(valid_values, 0.99)),
        "max": float(np.max(valid_values)),
    }


def _build_histogram_figure(valid_values, nc_file_name):
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=valid_values,
            nbinsx=90,
            marker_color="#f97316",
            opacity=0.88,
            name="LST Celsius",
        )
    )
    fig.update_layout(
        title=f"LSTF Celsius histogram - {nc_file_name}",
        xaxis_title="Land surface temperature (Celsius)",
        yaxis_title="Pixel count",
        template="plotly_white",
        bargap=0.02,
    )
    return fig


def _build_boxplot_figure(stats_values, nc_file_name):
    fig = go.Figure()
    fig.add_trace(
        go.Box(
            x=["LSTF"],
            q1=[stats_values["q1"]],
            median=[stats_values["median"]],
            q3=[stats_values["q3"]],
            lowerfence=[stats_values["min"]],
            upperfence=[stats_values["max"]],
            mean=[stats_values["mean"]],
            boxpoints=False,
            marker_color="#0ea5e9",
            name="LST Celsius",
        )
    )
    fig.update_layout(
        title=f"LSTF Celsius boxplot - {nc_file_name}",
        yaxis_title="Land surface temperature (Celsius)",
        template="plotly_white",
    )
    return fig


def _write_plotly_figure(fig, html_path, json_path, png_path, pkl_path, fallback_kind, valid_values=None, stats_values=None):
    html_path = Path(html_path)
    json_path = Path(json_path)
    png_path = Path(png_path)
    pkl_path = Path(pkl_path)

    for path in [html_path, json_path, png_path, pkl_path]:
        path.parent.mkdir(parents=True, exist_ok=True)

    fig.write_html(str(html_path), include_plotlyjs="cdn")
    json_path.write_text(pio.to_json(fig, pretty=True), encoding="utf-8")

    with pkl_path.open("wb") as f:
        pickle.dump(fig, f)

    try:
        fig.write_image(str(png_path), width=1200, height=760, scale=2)
    except Exception:
        if fallback_kind == "histogram":
            _write_histogram_fallback_png(valid_values, png_path)
        elif fallback_kind == "boxplot":
            _write_boxplot_fallback_png(stats_values, png_path)
        else:
            raise


def _write_histogram_fallback_png(valid_values, output_path):
    width, height = 1200, 760
    margin_left, margin_right, margin_top, margin_bottom = 95, 45, 70, 90
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    values = valid_values[np.isfinite(valid_values)]
    counts, edges = np.histogram(values, bins=90)
    max_count = max(int(counts.max()), 1)
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    bar_w = plot_w / len(counts)

    draw.text((margin_left, 24), "LSTF Celsius histogram", fill="#111827")
    draw.line((margin_left, margin_top + plot_h, margin_left + plot_w, margin_top + plot_h), fill="#111827", width=2)
    draw.line((margin_left, margin_top, margin_left, margin_top + plot_h), fill="#111827", width=2)

    for i, count in enumerate(counts):
        x0 = margin_left + i * bar_w
        x1 = margin_left + (i + 1) * bar_w - 1
        y1 = margin_top + plot_h
        y0 = y1 - (count / max_count) * plot_h
        draw.rectangle((x0, y0, x1, y1), fill="#f97316")

    draw.text((margin_left, height - 54), f"Temperature range: {edges[0]:.1f} C to {edges[-1]:.1f} C", fill="#111827")
    draw.text((margin_left, height - 30), f"Pixels: {len(values):,}", fill="#111827")
    img.save(output_path)


def _write_boxplot_fallback_png(stats_values, output_path):
    width, height = 900, 760
    margin_left, margin_right, margin_top, margin_bottom = 120, 120, 80, 90
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    min_v = stats_values["min"]
    max_v = stats_values["max"]
    q1 = stats_values["q1"]
    q3 = stats_values["q3"]
    median = stats_values["median"]
    mean = stats_values["mean"]
    pad = max((max_v - min_v) * 0.08, 1)
    scale_min = min_v - pad
    scale_max = max_v + pad

    plot_h = height - margin_top - margin_bottom
    center_x = width // 2

    def y_for(value):
        return margin_top + plot_h - ((value - scale_min) / (scale_max - scale_min)) * plot_h

    draw.text((margin_left, 28), "LSTF Celsius boxplot", fill="#111827")
    draw.line((margin_left, margin_top, margin_left, margin_top + plot_h), fill="#111827", width=2)
    draw.line((center_x, y_for(min_v), center_x, y_for(max_v)), fill="#0f172a", width=3)
    draw.line((center_x - 55, y_for(min_v), center_x + 55, y_for(min_v)), fill="#0f172a", width=3)
    draw.line((center_x - 55, y_for(max_v), center_x + 55, y_for(max_v)), fill="#0f172a", width=3)
    draw.rectangle((center_x - 120, y_for(q3), center_x + 120, y_for(q1)), outline="#0ea5e9", fill="#bae6fd", width=3)
    draw.line((center_x - 120, y_for(median), center_x + 120, y_for(median)), fill="#dc2626", width=4)
    draw.ellipse((center_x - 6, y_for(mean) - 6, center_x + 6, y_for(mean) + 6), fill="#111827")

    labels = [
        ("max", max_v),
        ("q3", q3),
        ("median", median),
        ("q1", q1),
        ("min", min_v),
    ]
    for label, value in labels:
        draw.text((center_x + 145, y_for(value) - 8), f"{label}: {value:.2f} C", fill="#111827")

    draw.text((margin_left, height - 42), f"Pixels: {stats_values['n']:,}", fill="#111827")
    img.save(output_path)


def _interpolate_colors(colors, n):
    stops = np.array(colors, dtype="float64")
    x_old = np.linspace(0, 1, len(stops))
    x_new = np.linspace(0, 1, n)
    channels = [np.interp(x_new, x_old, stops[:, i]) for i in range(3)]
    return np.stack(channels, axis=1).astype("uint8")


def _write_temperature_reference_png(output_path, orientation="vertical"):
    reference = sp_lstf_fnp01_reference()
    scale_min = float(reference["scale_min"])
    scale_max = float(reference["scale_max"])
    zero_line = float(reference["zero_line"])

    if orientation == "horizontal":
        width, height = 980, 160
        bar_x, bar_y, bar_w, bar_h = 80, 48, 760, 36
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        colors = _interpolate_colors(LSTF_REFERENCE_COLORS, bar_w)
        for i, color in enumerate(colors):
            draw.line((bar_x + i, bar_y, bar_x + i, bar_y + bar_h), fill=tuple(color) + (255,))
        zero_x = bar_x + int((zero_line - scale_min) / (scale_max - scale_min) * bar_w)
        draw.line((zero_x, bar_y - 10, zero_x, bar_y + bar_h + 10), fill=(0, 0, 0, 255), width=2)
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), outline=(20, 20, 20, 255), width=1)
        draw.text((bar_x, bar_y + bar_h + 18), f"{scale_min:.0f} C", fill=(20, 20, 20, 255))
        draw.text((zero_x - 18, bar_y + bar_h + 18), "0 C", fill=(20, 20, 20, 255))
        draw.text((bar_x + bar_w - 45, bar_y + bar_h + 18), f"{scale_max:.0f} C", fill=(20, 20, 20, 255))
        draw.text((bar_x, 14), "LSTF Celsius reference", fill=(20, 20, 20, 255))
    else:
        width, height = 220, 680
        bar_x, bar_y, bar_w, bar_h = 66, 70, 42, 520
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        colors = _interpolate_colors(list(reversed(LSTF_REFERENCE_COLORS)), bar_h)
        for i, color in enumerate(colors):
            draw.line((bar_x, bar_y + i, bar_x + bar_w, bar_y + i), fill=tuple(color) + (255,))
        zero_y = bar_y + int((scale_max - zero_line) / (scale_max - scale_min) * bar_h)
        draw.line((bar_x - 10, zero_y, bar_x + bar_w + 10, zero_y), fill=(0, 0, 0, 255), width=2)
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), outline=(20, 20, 20, 255), width=1)
        draw.text((bar_x + bar_w + 18, bar_y - 8), f"{scale_max:.0f} C", fill=(20, 20, 20, 255))
        draw.text((bar_x + bar_w + 18, zero_y - 8), "0 C", fill=(20, 20, 20, 255))
        draw.text((bar_x + bar_w + 18, bar_y + bar_h - 8), f"{scale_min:.0f} C", fill=(20, 20, 20, 255))
        draw.text((24, 24), "LSTF Celsius", fill=(20, 20, 20, 255))

    img.save(output_path)


def sp_lstf_fnp01_statistics(nc_path, output_dir):
    """
    Generate statistics, Plotly figures, and reference PNGs for LSTF FNP01.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_lstf_fnp01_output_schema(file_path, output_dir)

    print("[LSTF FNP01 Statistics] Reading original GOES LSTF grid...", flush=True)
    values_celsius = _read_original_lst_celsius(file_path)
    valid_values = _valid_lst_values(values_celsius)

    if valid_values.size == 0:
        raise ValueError("No valid original-grid LSTF Celsius values were found.")

    print(f"[LSTF FNP01 Statistics] Valid pixels: {valid_values.size}", flush=True)

    general_info = _build_general_info_table(file_path, values_celsius, valid_values)
    pixel_info = _build_pixel_info_table(values_celsius, valid_values)
    position_stats = _build_position_stats_table(valid_values)
    dispersion_stats = _build_dispersion_stats_table(valid_values)
    stats_values = _stats_dict(valid_values)

    _write_rows_csv(general_info, outputs["statistics_general_csv"])
    _write_rows_json(general_info, outputs["statistics_general_json"])
    _write_rows_csv(pixel_info, outputs["statistics_pixel_csv"])
    _write_rows_json(pixel_info, outputs["statistics_pixel_json"])
    _write_rows_csv(position_stats, outputs["statistics_position_csv"])
    _write_rows_json(position_stats, outputs["statistics_position_json"])
    _write_rows_csv(dispersion_stats, outputs["statistics_dispersion_csv"])
    _write_rows_json(dispersion_stats, outputs["statistics_dispersion_json"])

    histogram_fig = _build_histogram_figure(valid_values, file_path.name)
    boxplot_fig = _build_boxplot_figure(stats_values, file_path.name)

    _write_plotly_figure(
        histogram_fig,
        outputs["histogram_plot_html"],
        outputs["histogram_plot_json"],
        outputs["histogram_plot_png"],
        outputs["histogram_plot_pkl"],
        fallback_kind="histogram",
        valid_values=valid_values,
    )
    _write_plotly_figure(
        boxplot_fig,
        outputs["boxplot_plot_html"],
        outputs["boxplot_plot_json"],
        outputs["boxplot_plot_png"],
        outputs["boxplot_plot_pkl"],
        fallback_kind="boxplot",
        stats_values=stats_values,
    )

    reference = sp_lstf_fnp01_reference()
    reference_payload = {
        **reference,
        "colors_rgb": [list(color) for color in LSTF_REFERENCE_COLORS],
        "source": "legion_goes/satpy_config/enhancements/abi.yaml: lst_celsius_color01",
    }
    Path(outputs["temperature_reference_json"]).write_text(
        json.dumps(reference_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_temperature_reference_png(
        outputs["temperature_reference_vertical_png"],
        orientation="vertical",
    )
    _write_temperature_reference_png(
        outputs["temperature_reference_horizontal_png"],
        orientation="horizontal",
    )

    result = {
        "statistics_general_csv": outputs["statistics_general_csv"],
        "statistics_general_json": outputs["statistics_general_json"],
        "statistics_pixel_csv": outputs["statistics_pixel_csv"],
        "statistics_pixel_json": outputs["statistics_pixel_json"],
        "statistics_position_csv": outputs["statistics_position_csv"],
        "statistics_position_json": outputs["statistics_position_json"],
        "statistics_dispersion_csv": outputs["statistics_dispersion_csv"],
        "statistics_dispersion_json": outputs["statistics_dispersion_json"],
        "histogram_plot_html": outputs["histogram_plot_html"],
        "histogram_plot_json": outputs["histogram_plot_json"],
        "histogram_plot_png": outputs["histogram_plot_png"],
        "histogram_plot_pkl": outputs["histogram_plot_pkl"],
        "boxplot_plot_html": outputs["boxplot_plot_html"],
        "boxplot_plot_json": outputs["boxplot_plot_json"],
        "boxplot_plot_png": outputs["boxplot_plot_png"],
        "boxplot_plot_pkl": outputs["boxplot_plot_pkl"],
        "temperature_reference_vertical_png": outputs["temperature_reference_vertical_png"],
        "temperature_reference_horizontal_png": outputs["temperature_reference_horizontal_png"],
        "temperature_reference_json": outputs["temperature_reference_json"],
    }

    ensure_output_files(result)

    print(
        "[LSTF FNP01 Statistics] Finished in "
        f"{round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result
