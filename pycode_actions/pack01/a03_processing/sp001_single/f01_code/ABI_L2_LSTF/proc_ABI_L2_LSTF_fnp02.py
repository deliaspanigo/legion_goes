"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_LSTF/proc_ABI_L2_LSTF_fnp02.py
Version: 0.0.2
Description:
    Core processing - ABI-L2-LSTF FNP02.

    This FNP generates Plotly statistics products for LST in Celsius,
    using the ORIGINAL NetCDF grid, not WGS84.

    Outputs:
    - Histogram plot: HTML, JSON, PNG, PKL
    - Boxplot plot: HTML, JSON, PNG, PKL
    - General information table: CSV, JSON
    - Pixel information table: CSV, JSON
    - Position statistics table: CSV, JSON
    - Dispersion statistics table: CSV, JSON

    Important:
    The n used in position/dispersion statistics must match the number of
    valid pixels in the original NetCDF.

Last modification: 21-05-2026
"""

# =========================================================================================================================================
#  Execution:
#  python -m legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_LSTF.proc_ABI_L2_LSTF_fnp02
# =========================================================================================================================================


# =============================================================================
# Libraries
# =============================================================================

import time
import gc
import re
import csv
import json
import pickle
import traceback
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from satpy import Scene


# =============================================================================
# Local libraries
# =============================================================================

from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import (
    get_position_by_sat_id,
)


# =============================================================================
# 1. OUTPUT SCHEMA
# =============================================================================

def gen_dict_output_file_name(nc_path):
    """
    Generates the expected output filenames for ABI-L2-LSTF FNP02.

    All files returned here are mandatory.
    """

    nc_file_name = Path(nc_path).name

    match = re.search(
        r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})",
        nc_file_name,
    )

    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    str_sat = match.group("sat")
    str_sat_number = str_sat[1:]
    str_stimestamp = match.group("start")
    str_position = get_position_by_sat_id(sat_id=str_sat_number)

    str_name = f"SP-01-simple_G{str_sat_number}-{str_position}-s{str_stimestamp}"

    return {
        "histogram_plot_html": (
            f"{str_name}_LSTF-fnp02-Celsius-Histogram-Plotly.html"
        ),
        "histogram_plot_json": (
            f"{str_name}_LSTF-fnp02-Celsius-Histogram-Plotly.json"
        ),
        "histogram_plot_png": (
            f"{str_name}_LSTF-fnp02-Celsius-Histogram-Plotly.png"
        ),
        "histogram_plot_pkl": (
            f"{str_name}_LSTF-fnp02-Celsius-Histogram-Plotly.pkl"
        ),

        "boxplot_plot_html": (
            f"{str_name}_LSTF-fnp02-Celsius-Boxplot-Plotly.html"
        ),
        "boxplot_plot_json": (
            f"{str_name}_LSTF-fnp02-Celsius-Boxplot-Plotly.json"
        ),
        "boxplot_plot_png": (
            f"{str_name}_LSTF-fnp02-Celsius-Boxplot-Plotly.png"
        ),
        "boxplot_plot_pkl": (
            f"{str_name}_LSTF-fnp02-Celsius-Boxplot-Plotly.pkl"
        ),

        "table_general_info_csv": (
            f"{str_name}_LSTF-fnp02-General-Info.csv"
        ),
        "table_general_info_json": (
            f"{str_name}_LSTF-fnp02-General-Info.json"
        ),

        "table_pixel_info_csv": (
            f"{str_name}_LSTF-fnp02-Pixel-Info.csv"
        ),
        "table_pixel_info_json": (
            f"{str_name}_LSTF-fnp02-Pixel-Info.json"
        ),

        "table_position_stats_csv": (
            f"{str_name}_LSTF-fnp02-Position-Stats-Celsius.csv"
        ),
        "table_position_stats_json": (
            f"{str_name}_LSTF-fnp02-Position-Stats-Celsius.json"
        ),

        "table_dispersion_stats_csv": (
            f"{str_name}_LSTF-fnp02-Dispersion-Stats-Celsius.csv"
        ),
        "table_dispersion_stats_json": (
            f"{str_name}_LSTF-fnp02-Dispersion-Stats-Celsius.json"
        ),
    }


def get_required_output_keys():
    """
    Returns all mandatory output keys expected by this FNP.
    """

    return [
        "histogram_plot_html",
        "histogram_plot_json",
        "histogram_plot_png",
        "histogram_plot_pkl",

        "boxplot_plot_html",
        "boxplot_plot_json",
        "boxplot_plot_png",
        "boxplot_plot_pkl",

        "table_general_info_csv",
        "table_general_info_json",

        "table_pixel_info_csv",
        "table_pixel_info_json",

        "table_position_stats_csv",
        "table_position_stats_json",

        "table_dispersion_stats_csv",
        "table_dispersion_stats_json",
    ]


def validate_required_kwargs(kwargs):
    """
    Validates that all mandatory output paths were provided.
    """

    missing = [
        key
        for key in get_required_output_keys()
        if key not in kwargs or kwargs.get(key) is None or str(kwargs.get(key)).strip() == ""
    ]

    if missing:
        raise ValueError(
            "Missing mandatory output path(s): " + ", ".join(missing)
        )


def validate_output_files(kwargs):
    """
    Validates that all mandatory output files exist and are not empty.
    """

    missing_or_empty = []

    for key in get_required_output_keys():
        path_obj = Path(kwargs[key])

        if not path_obj.exists():
            missing_or_empty.append((key, path_obj, "missing"))
            continue

        if not path_obj.is_file():
            missing_or_empty.append((key, path_obj, "not_a_file"))
            continue

        if path_obj.stat().st_size == 0:
            missing_or_empty.append((key, path_obj, "empty"))
            continue

    if missing_or_empty:
        msg_lines = ["Mandatory output validation failed:"]

        for key, path_obj, reason in missing_or_empty:
            msg_lines.append(f"  - {key}: {path_obj} [{reason}]")

        raise RuntimeError("\n".join(msg_lines))


# =============================================================================
# 2. TABLE HELPERS
# =============================================================================

def write_table_csv(path_out, rows):
    """
    Writes a list of dictionaries to CSV.
    """

    path_out = Path(path_out)
    path_out.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise ValueError(f"Cannot write empty table: {path_out}")

    fieldnames = list(rows[0].keys())

    with open(path_out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_table_json(path_out, rows):
    """
    Writes a list of dictionaries to JSON.
    """

    path_out = Path(path_out)
    path_out.parent.mkdir(parents=True, exist_ok=True)

    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def safe_float(x, digits=4):
    """
    Converts a value to float and rounds it.
    """

    if x is None:
        return None

    try:
        if not np.isfinite(x):
            return None

        return round(float(x), digits)

    except Exception:
        return None


def dataarray_to_numpy(data_array):
    """
    Converts xarray/dask DataArray values to numpy array.

    Handles dask arrays and masked arrays.
    """

    values = data_array.data

    if hasattr(values, "compute"):
        values = values.compute()

    values = np.asanyarray(values)

    if np.ma.isMaskedArray(values):
        values = values.filled(np.nan)

    values = np.asarray(values, dtype="float64")

    return values


def get_native_resolution_meters(data_array):
    """
    Tries to get native pixel size from SatPy area metadata.
    """

    area = data_array.attrs.get("area", None)

    if area is None:
        return None, None

    res_x = getattr(area, "pixel_size_x", None)
    res_y = getattr(area, "pixel_size_y", None)

    return res_x, res_y


def build_valid_mask(values_celsius, min_valid=-100.0, max_valid=100.0):
    """
    Builds a validity mask for original NetCDF LST Celsius values.

    This removes:
    - NaN
    - inf
    - values outside a reasonable Celsius range
    """

    arr = np.asarray(values_celsius, dtype="float64")

    valid_mask = (
        np.isfinite(arr)
        & (arr >= min_valid)
        & (arr <= max_valid)
    )

    return valid_mask


def extract_valid_lst_values(values_celsius, min_valid=-100.0, max_valid=100.0):
    """
    Extracts valid LST Celsius values from the original NetCDF grid.
    """

    valid_mask = build_valid_mask(
        values_celsius=values_celsius,
        min_valid=min_valid,
        max_valid=max_valid,
    )

    return np.asarray(values_celsius, dtype="float64")[valid_mask]


# =============================================================================
# 3. STATISTICS HELPERS
# =============================================================================

def build_general_info_table(
    nc_file_name,
    native_rows,
    native_cols,
    native_total,
    native_res_x,
    native_res_y,
    valid_min,
    valid_max,
):
    """
    Builds general information table.

    Statistics are computed from the original NetCDF grid.
    """

    return [
        {
            "Measure": "File name",
            "Value": nc_file_name,
        },
        {
            "Measure": "Fuente de statistics",
            "Value": "NetCDF original",
        },
        {
            "Measure": "Resolution original X, metros",
            "Value": safe_float(native_res_x, 4),
        },
        {
            "Measure": "Resolution original Y, metros",
            "Value": safe_float(native_res_y, 4),
        },
        {
            "Measure": "Original pixel rows",
            "Value": int(native_rows),
        },
        {
            "Measure": "Original pixel columns",
            "Value": int(native_cols),
        },
        {
            "Measure": "Total original pixels",
            "Value": int(native_total),
        },
        {
            "Measure": "Minimum Celsius filter",
            "Value": safe_float(valid_min, 2),
        },
        {
            "Measure": "Maximum Celsius filter",
            "Value": safe_float(valid_max, 2),
        },
    ]


def build_pixel_info_table(native_values_celsius, min_valid=-100.0, max_valid=100.0):
    """
    Builds pixel information table from original NetCDF LST values.
    """

    arr = np.asarray(native_values_celsius, dtype="float64")
    total = int(arr.size)

    valid_mask = build_valid_mask(
        values_celsius=arr,
        min_valid=min_valid,
        max_valid=max_valid,
    )

    valid_count = int(np.sum(valid_mask))
    nodata_count = int(total - valid_count)

    return [
        {
            "Measure": "Total pixels",
            "n": total,
            "Percentage": 100.0,
        },
        {
            "Measure": "Pixels without data",
            "n": nodata_count,
            "Percentage": round((nodata_count / total) * 100.0, 4) if total > 0 else None,
        },
        {
            "Measure": "Pixels with data",
            "n": valid_count,
            "Percentage": round((valid_count / total) * 100.0, 4) if total > 0 else None,
        },
    ]


def build_position_stats_table(valid_values):
    """
    Builds position statistics table from valid original NetCDF Celsius values.
    """

    if valid_values.size == 0:
        raise ValueError("No valid LST Celsius values found for position statistics.")

    qs = np.quantile(
        valid_values,
        [0.00, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 1.00],
    )

    return [
        {"Measure": "n", "Value": int(valid_values.size)},
        {"Measure": "Minimum", "Value": safe_float(qs[0], 4)},
        {"Measure": "Percentile 1", "Value": safe_float(qs[1], 4)},
        {"Measure": "Percentile 5", "Value": safe_float(qs[2], 4)},
        {"Measure": "First quartile", "Value": safe_float(qs[3], 4)},
        {"Measure": "Mean", "Value": safe_float(np.mean(valid_values), 4)},
        {"Measure": "Median", "Value": safe_float(qs[4], 4)},
        {"Measure": "Third quartile", "Value": safe_float(qs[5], 4)},
        {"Measure": "Percentile 95", "Value": safe_float(qs[6], 4)},
        {"Measure": "Percentile 99", "Value": safe_float(qs[7], 4)},
        {"Measure": "Maximum", "Value": safe_float(qs[8], 4)},
    ]


def build_dispersion_stats_table(valid_values):
    """
    Builds dispersion statistics table from valid original NetCDF Celsius values.
    """

    if valid_values.size == 0:
        raise ValueError("No valid LST Celsius values found for dispersion statistics.")

    mean_value = float(np.mean(valid_values))
    sd_value = float(np.std(valid_values, ddof=1)) if valid_values.size > 1 else 0.0
    var_value = float(np.var(valid_values, ddof=1)) if valid_values.size > 1 else 0.0

    q1 = float(np.quantile(valid_values, 0.25))
    q3 = float(np.quantile(valid_values, 0.75))

    median_value = float(np.median(valid_values))
    mad_value = float(np.median(np.abs(valid_values - median_value)))

    min_value = float(np.min(valid_values))
    max_value = float(np.max(valid_values))

    cv_value = None
    if mean_value != 0:
        cv_value = sd_value / abs(mean_value)

    return [
        {"Measure": "n", "Value": int(valid_values.size)},
        {"Measure": "Standard deviation", "Value": safe_float(sd_value, 4)},
        {"Measure": "Variance", "Value": safe_float(var_value, 4)},
        {"Measure": "Interquartile range", "Value": safe_float(q3 - q1, 4)},
        {"Measure": "Range", "Value": safe_float(max_value - min_value, 4)},
        {"Measure": "Medayn absolute deviation", "Value": safe_float(mad_value, 4)},
        {"Measure": "Coefficient of variation", "Value": safe_float(cv_value, 4)},
    ]


def stats_dict_from_values(valid_values):
    """
    Computes a compact stats dictionary for plots.
    """

    if valid_values.size == 0:
        raise ValueError("No valid LST Celsius values found.")

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


# =============================================================================
# 4. PLOTLY HELPERS
# =============================================================================

def build_histogram_figure(valid_values, nc_file_name):
    """
    Builds Plotly histogram from original NetCDF valid Celsius values.
    """

    hist_min = -70.0
    hist_max = 70.0
    bin_width = 2.0

    values_plot = valid_values[
        (valid_values >= hist_min)
        & (valid_values <= hist_max)
    ]

    bins = np.arange(hist_min, hist_max + bin_width, bin_width)

    counts, edges = np.histogram(values_plot, bins=bins)
    mids = (edges[:-1] + edges[1:]) / 2.0

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=mids,
            y=counts,
            width=bin_width,
            name="LST",
            hovertemplate=(
                "Temperature: %{x:.1f} C<br>"
                "Frequency: %{y}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=f"Histogram LST Celsius - Original NetCDF<br><sup>{nc_file_name}</sup>",
        xaxis_title="Land Surface Temperature, C",
        yaxis_title="Frequency",
        bargap=0,
        template="plotly_white",
        margin=dict(l=70, r=30, t=80, b=70),
    )

    fig.update_xaxes(
        range=[hist_min, hist_max],
        dtick=10,
    )

    return fig


def build_boxplot_figure(stats_values, nc_file_name):
    """
    Builds Plotly boxplot with whiskers explicitly from minimum to maximum.

    It uses precomputed quartiles:
    - lowerfence = min
    - upperfence = max
    """

    fig = go.Figure()

    fig.add_trace(
        go.Box(
            name="LST Celsius",
            q1=[stats_values["q1"]],
            median=[stats_values["median"]],
            q3=[stats_values["q3"]],
            lowerfence=[stats_values["min"]],
            upperfence=[stats_values["max"]],
            mean=[stats_values["mean"]],
            boxmean=True,
            orientation="v",
            hovertemplate=(
                "Min: %{lowerfence:.2f} C<br>"
                "Q1: %{q1:.2f} C<br>"
                "Median: %{median:.2f} C<br>"
                "Q3: %{q3:.2f} C<br>"
                "Max: %{upperfence:.2f} C"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=f"Boxplot LST Celsius - Original NetCDF<br><sup>{nc_file_name}</sup>",
        yaxis_title="Land Surface Temperature, C",
        template="plotly_white",
        margin=dict(l=70, r=30, t=80, b=70),
    )

    return fig


def save_plotly_figure(fig, html_path, json_path, png_path, pkl_path):
    """
    Saves a Plotly figure as HTML, JSON, PNG and Pickle.

    PNG export requires kaleido.
    """

    html_path = Path(html_path)
    json_path = Path(json_path)
    png_path = Path(png_path)
    pkl_path = Path(pkl_path)

    html_path.parent.mkdir(parents=True, exist_ok=True)

    fig.write_html(
        str(html_path),
        include_plotlyjs="cdn",
        full_html=True,
    )

    fig.write_json(
        str(json_path),
        pretty=True,
    )

    fig.write_image(
        str(png_path),
        width=1400,
        height=900,
        scale=2,
    )

    with open(pkl_path, "wb") as f:
        pickle.dump(fig, f)


# =============================================================================
# 5. CORE PROCESSING
# =============================================================================

def run_proc_ABI_L2_LSTF_fnp02(nc_path, **kwargs):
    """
    Executes FNP02 for ABI-L2-LSTF.

    All statistics and plots are computed from the original NetCDF grid.
    No WGS84 resampling is used in FNP02.

    Returns
    -------
    bool
        True if all mandatory files were generated successfully.
        False otherwise.
    """

    start_time = time.time()
    file_path = Path(nc_path)

    prod_raw = "LST"

    valid_min = -100.0
    valid_max = 100.0

    my_chunks = {
        "y": 1024,
        "x": 1024,
    }

    scn = None

    try:
        # ---------------------------------------------------------------------
        # Validate inputs
        # ---------------------------------------------------------------------

        if not file_path.exists():
            raise FileNotFoundError(f"Input NetCDF does not exist: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Input path is not a file: {file_path}")

        validate_required_kwargs(kwargs)

        first_output_file_path = list(kwargs.values())[0]
        output_folder = Path(first_output_file_path).parent
        output_folder.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] output_folder = {output_folder}", flush=True)

        # ---------------------------------------------------------------------
        # Step 01
        # ---------------------------------------------------------------------

        print(
            "\n[Step 01/06] Loading original NetCDF LST scene...",
            end=" ",
            flush=True,
        )

        scn = Scene(
            filenames=[str(file_path)],
            reader="abi_l2_nc",
            reader_kwargs={"chunks": my_chunks},
        )

        scn.load([prod_raw])

        scn[prod_raw] = scn[prod_raw] - 273.15
        scn[prod_raw].attrs["units"] = "Celsius"

        native_data_array = scn[prod_raw]
        native_values_celsius = dataarray_to_numpy(native_data_array)

        native_rows = native_values_celsius.shape[0]
        native_cols = native_values_celsius.shape[1]
        native_total = int(native_values_celsius.size)

        native_res_x, native_res_y = get_native_resolution_meters(native_data_array)

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 02
        # ---------------------------------------------------------------------

        print(
            "[Step 02/06] Extracting valid Celsius values from original NetCDF...",
            end=" ",
            flush=True,
        )

        valid_values = extract_valid_lst_values(
            values_celsius=native_values_celsius,
            min_valid=valid_min,
            max_valid=valid_max,
        )

        if valid_values.size == 0:
            raise ValueError("No valid LST Celsius values found in original NetCDF.")

        print(f"[OK] n={valid_values.size}", flush=True)

        # ---------------------------------------------------------------------
        # Step 03
        # ---------------------------------------------------------------------

        print(
            "[Step 03/06] Computing tables from original NetCDF...",
            end=" ",
            flush=True,
        )

        general_info = build_general_info_table(
            nc_file_name=file_path.name,
            native_rows=native_rows,
            native_cols=native_cols,
            native_total=native_total,
            native_res_x=native_res_x,
            native_res_y=native_res_y,
            valid_min=valid_min,
            valid_max=valid_max,
        )

        pixel_info = build_pixel_info_table(
            native_values_celsius=native_values_celsius,
            min_valid=valid_min,
            max_valid=valid_max,
        )

        position_stats = build_position_stats_table(
            valid_values=valid_values,
        )

        dispersion_stats = build_dispersion_stats_table(
            valid_values=valid_values,
        )

        stats_values = stats_dict_from_values(valid_values)

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 04
        # ---------------------------------------------------------------------

        print(
            "[Step 04/06] Saving table files...",
            end=" ",
            flush=True,
        )

        write_table_csv(kwargs["table_general_info_csv"], general_info)
        write_table_json(kwargs["table_general_info_json"], general_info)

        write_table_csv(kwargs["table_pixel_info_csv"], pixel_info)
        write_table_json(kwargs["table_pixel_info_json"], pixel_info)

        write_table_csv(kwargs["table_position_stats_csv"], position_stats)
        write_table_json(kwargs["table_position_stats_json"], position_stats)

        write_table_csv(kwargs["table_dispersion_stats_csv"], dispersion_stats)
        write_table_json(kwargs["table_dispersion_stats_json"], dispersion_stats)

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 05
        # ---------------------------------------------------------------------

        print(
            "[Step 05/06] Building and saving Plotly figures...",
            end=" ",
            flush=True,
        )

        histogram_fig = build_histogram_figure(
            valid_values=valid_values,
            nc_file_name=file_path.name,
        )

        boxplot_fig = build_boxplot_figure(
            stats_values=stats_values,
            nc_file_name=file_path.name,
        )

        save_plotly_figure(
            fig=histogram_fig,
            html_path=kwargs["histogram_plot_html"],
            json_path=kwargs["histogram_plot_json"],
            png_path=kwargs["histogram_plot_png"],
            pkl_path=kwargs["histogram_plot_pkl"],
        )

        save_plotly_figure(
            fig=boxplot_fig,
            html_path=kwargs["boxplot_plot_html"],
            json_path=kwargs["boxplot_plot_json"],
            png_path=kwargs["boxplot_plot_png"],
            pkl_path=kwargs["boxplot_plot_pkl"],
        )

        print("[OK]", flush=True)

        # ---------------------------------------------------------------------
        # Step 06
        # ---------------------------------------------------------------------

        print(
            "[Step 06/06] Validating mandatory outputs...",
            end=" ",
            flush=True,
        )

        validate_output_files(kwargs)

        print("[OK]", flush=True)

        duration = round(time.time() - start_time, 2)

        print(f"[SUMMARY] Total time: {duration}s", flush=True)
        print("[STATUS] Process finished successfully.", flush=True)

        return True

    except Exception as e:
        print("\n[ERROR] FNP02 failed.", flush=True)
        print(f"[ERROR] {str(e)}", flush=True)
        print("[TRACEBACK]", flush=True)
        print(traceback.format_exc(), flush=True)

        return False

    finally:
        try:
            if scn is not None:
                del scn

            gc.collect()

        except Exception:
            pass


# =============================================================================
# SIMPLE MAIN
# =============================================================================

if __name__ == "__main__":

    print("\n" + " FNP02: LSTF STATISTICS DIAGNOSTIC TEST ".center(80, "="))

    working_dir = Path.cwd()
    folder_data_raw = working_dir / "data_raw"

    print(f"[INFO] WORKING DIR : {working_dir}")
    print(f"[INFO] DATA RAW    : {folder_data_raw}")

    if not folder_data_raw.exists():

        print(f"[ERROR] data_raw folder does not exist: {folder_data_raw}")

    else:

        nc_candidates = sorted([
            p for p in folder_data_raw.rglob("*.nc")
            if "LSTF" in p.name.upper()
        ])

        if not nc_candidates:

            print(f"[ERROR] No .nc files with LSTF found recursively in: {folder_data_raw}")

        else:

            target_nc = nc_candidates[0]

            test_out = (
                working_dir
                / "test_outputs"
                / target_nc.stem
                / "ABI-L2-LSTF_fnp02"
            )

            test_out.mkdir(parents=True, exist_ok=True)

            print(f"[INFO] FILE   : {target_nc}")
            print(f"[INFO] OUTPUT : {test_out}")
            print("-" * 80)

            dict_output_file_name = gen_dict_output_file_name(
                nc_path=str(target_nc)
            )

            dict_output_file_path = {
                key: str(test_out / file_name)
                for key, file_name in dict_output_file_name.items()
            }

            success = run_proc_ABI_L2_LSTF_fnp02(
                nc_path=str(target_nc),
                **dict_output_file_path,
            )

            if success:
                print("-" * 80)
                print("[OK] TEST COMPLETED SUCCESSFULLY")
                print("=" * 80)
            else:
                print("-" * 80)
                print("[ERROR] TEST FAILED")
                print("=" * 80)