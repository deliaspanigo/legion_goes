"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/ABI_L2_FDCF/proc_ABI_L2_FDCF_fnp01.py
Version: 0.0.4 (Explicit Linear Processing)
Description: Core Processing Code - FDCF fnp01 with explicit independent steps.
Last modification: 06-05-2026 21:00
"""
# =========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.ABI_L2_FDCF.proc_ABI_L2_FDCF_fnp01
# =========================================================================================================================================

import os
import sys
import time
import gc
import re
import csv
import json
from pathlib import Path
from satpy import Scene
from pyresample.geometry import AreaDefinition
import numpy as np
import xarray as xr
from pyproj import Proj

# --- Local Libraries
from legion_goes.satpy_config.my_config_satpy import CACHE_DIR   # Cache Folder!
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id

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
FDCF_FIRE_CLASSES = sorted(FDCF_FIRE_CLASS_LABELS.keys())

# =============================================================================
# 1. OUTPUT SCHEMA DEFINITION
# =============================================================================
def gen_dict_output_file_name(nc_path): 
    nc_file_name = Path(nc_path).name
    match = re.search(r"OR_(?P<prod>ABI-L2-[A-Z0-9]+)-.*_(?P<sat>G\d{2})_s(?P<start>\d{14})", nc_file_name)
    
    if not match:
        raise ValueError(f"Could not parse file format: {nc_file_name}")

    str_sat_number = match.group("sat")[1:]
    str_stimestamp = match.group("start") 
    str_position = get_position_by_sat_id(sat_id = str_sat_number)
    str_name = f"SP-01-simple_G{str_sat_number}-{str_position}-s{str_stimestamp}"
    
    return {
        "goes_native_color01_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color01.png",
        "wgs84_color01_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color01.tif",
        "wgs84_color01_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color01.png",
        "mercator_color01_png":    f"{str_name}_CRS-Mercator_FDCF-fnp01-color01.png",
        
        "goes_native_color02_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color02.png",
        "wgs84_color02_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color02.tif",
        "wgs84_color02_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color02.png",
        "mercator_color02_png":    f"{str_name}_CRS-Mercator_FDCF-fnp01-color02.png",
        
        "goes_native_color03_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color03.png",
        "wgs84_color03_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color03.tif",
        "wgs84_color03_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color03.png",
        "mercator_color03_png":    f"{str_name}_CRS-Mercator_FDCF-fnp01-color03.png",
        
        "goes_native_color04_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color04.png",
        "wgs84_color04_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color04.tif",
        "wgs84_color04_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color04.png",
        "mercator_color04_png":    f"{str_name}_CRS-Mercator_FDCF-fnp01-color04.png",
        
        "goes_native_color05_png": f"{str_name}_CRS-Goes{str_position}_FDCF-fnp01-color05.png",
        "wgs84_color05_tif":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color05.tif",
        "wgs84_color05_png":       f"{str_name}_CRS-WGS84_FDCF-fnp01-color05.png",
        "mercator_color05_png":    f"{str_name}_CRS-Mercator_FDCF-fnp01-color05.png",

        "fire_points_csv":         f"{str_name}_CRS-WGS84_FDCF-fnp01-FirePoints.csv",
        "fire_points_geojson":     f"{str_name}_CRS-WGS84_FDCF-fnp01-FirePoints.geojson",
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
        arr = var.values
        vals = arr[rows, cols]
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

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
        "name": output_geojson.stem,
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


def export_fdcf_fire_points(nc_path, output_csv, output_geojson):
    """
    Extracts FDCF fire pixels from the native Mask array and writes WGS84 points.

    Fire classes match the legacy Shiny FDCF app:
    10-15 and 30-35.
    """

    rows_out = []

    with xr.open_dataset(nc_path, mask_and_scale=False) as ds:
        if "Mask" not in ds:
            raise ValueError("Mask variable was not found in the FDCF NetCDF file.")

        mask = ds["Mask"].values
        mask_round = np.rint(mask).astype(np.int16, copy=False)
        fire_mask = np.isin(mask_round, FDCF_FIRE_CLASSES)
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
                    raise ValueError("GOES projection variable was not found in the FDCF NetCDF file.")

                projection_name = projection_candidates[0]

            projection_attrs = ds[projection_name].attrs
            perspective_point_height = float(projection_attrs["perspective_point_height"])
            semi_major_axis = float(projection_attrs["semi_major_axis"])
            semi_minor_axis = float(projection_attrs["semi_minor_axis"])
            longitude_of_projection_origin = float(projection_attrs["longitude_of_projection_origin"])
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
                lon_i = _to_python_scalar(float(lon[i]))
                lat_i = _to_python_scalar(float(lat[i]))

                rows_out.append({
                    "point_id": i + 1,
                    "row": int(rows[i]),
                    "col": int(cols[i]),
                    "lon": lon_i,
                    "lat": lat_i,
                    "x_scan_angle": _to_python_scalar(float(x_scan[i])),
                    "y_scan_angle": _to_python_scalar(float(y_scan[i])),
                    "fdcf_class": fdcf_class,
                    "class_name": FDCF_FIRE_CLASS_LABELS.get(fdcf_class, "Fire pixel"),
                    "area": area_values[i],
                    "temp": temp_values[i],
                    "power": power_values[i],
                    "dqf": dqf_values[i],
                })

    _write_fire_points_csv(rows_out, output_csv)
    _write_fire_points_geojson(rows_out, output_geojson)

    return rows_out

# =============================================================================
# 3. CORE PROCESSING FUNCTION
# =============================================================================

def run_proc_ABI_L2_FDCF_fnp01(nc_path, **kwargs):
    
    start_time = time.time()
    file_path = Path(nc_path)
    
    # Cache path usando SOT
    path_cache = CACHE_DIR
    resample_kwargs = {
        'cache_dir': str(path_cache),
        'nprocs': 4,              # Usa ms ncleos para el clculo inicial
        'static_data': True       # Fuerza a tratar la geometra como fija
    }
    my_chunks = {'y': 1024, 'x': 1024}

    try:
        # 0. Set up output folder and map areas
        first_path = list(kwargs.values())[0]
        Path(first_path).parent.mkdir(parents=True, exist_ok=True)
        
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        web_mercator_max = 20037508.342789244
        area_mercator = AreaDefinition(
            'webmercator',
            'Global Web Mercator',
            'epsg3857',
            'EPSG:3857',
            3600,
            3400,
            [-web_mercator_max, -web_mercator_max, web_mercator_max, web_mercator_max],
        )

        # 1. Inicializar Scene
        ####scn = Scene(filenames=[nc_path], reader='abi_l2_nc')
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc', reader_kwargs={'chunks': my_chunks})
        
        
        # --- BLOQUE INDEPENDIENTE: COLOR 01 ---
        print(f"\n      [Step 01/06]   Processing Color 01 (my_fdc_fn01)...", flush=True)
        prod_01 = 'my_fdc_fn01'
        scn.load([prod_01])
        
        # Guardar Native
        scn.save_dataset(prod_01, filename=kwargs.get("goes_native_color01_png"), writer='simple_image')
        
        # Resample y guardar WGS84 (Tif y Png)
        ##### scn_res_01 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_01 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_01.save_dataset(prod_01, filename=kwargs.get("wgs84_color01_tif"), writer='geotiff')
        scn_res_01.save_dataset(prod_01, filename=kwargs.get("wgs84_color01_png"), writer='simple_image')

        scn_mercator_01 = scn.resample(area_mercator, resampler='kd_tree', **resample_kwargs)
        scn_mercator_01.save_dataset(prod_01, filename=kwargs.get("mercator_color01_png"), writer='simple_image')
        
        # Limpieza Bloque 01
        del scn_res_01
        del scn_mercator_01
        scn.unload(prod_01)
        gc.collect()
        print("      Done and Cleared.")

        # --- BLOQUE INDEPENDIENTE: COLOR 02 ---
        print(f"      [Step 02/06]   Processing Color 02 (my_fdc_fn02)...", flush=True)
        prod_02 = 'my_fdc_fn02'
        scn.load([prod_02])
        
        scn.save_dataset(prod_02, filename=kwargs.get("goes_native_color02_png"), writer='simple_image')
        
        
        ####scn_res_02 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_02 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_02.save_dataset(prod_02, filename=kwargs.get("wgs84_color02_tif"), writer='geotiff')
        scn_res_02.save_dataset(prod_02, filename=kwargs.get("wgs84_color02_png"), writer='simple_image')

        scn_mercator_02 = scn.resample(area_mercator, resampler='kd_tree', **resample_kwargs)
        scn_mercator_02.save_dataset(prod_02, filename=kwargs.get("mercator_color02_png"), writer='simple_image')
        
        del scn_res_02
        del scn_mercator_02
        scn.unload(prod_02)
        gc.collect()
        print("      Done and Cleared.")

        # --- BLOQUE INDEPENDIENTE: COLOR 03 ---
        print(f"      [Step 03/06]   Processing Color 03 (my_fdc_fn03)...", flush=True)
        prod_03 = 'my_fdc_fn03'
        scn.load([prod_03])
        
        scn.save_dataset(prod_03, filename=kwargs.get("goes_native_color03_png"), writer='simple_image')
        
        ######scn_res_03 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_03 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_03.save_dataset(prod_03, filename=kwargs.get("wgs84_color03_tif"), writer='geotiff')
        scn_res_03.save_dataset(prod_03, filename=kwargs.get("wgs84_color03_png"), writer='simple_image')

        scn_mercator_03 = scn.resample(area_mercator, resampler='kd_tree', **resample_kwargs)
        scn_mercator_03.save_dataset(prod_03, filename=kwargs.get("mercator_color03_png"), writer='simple_image')
        
        del scn_res_03
        del scn_mercator_03
        scn.unload(prod_03)
        gc.collect()
        print("      Done and Cleared.")

        # --- BLOQUE INDEPENDIENTE: COLOR 04 ---
        print(f"      [Step 04/06]   Processing Color 04 (my_fdc_fn04)...", flush=True)
        prod_04 = 'my_fdc_fn04'
        scn.load([prod_04])
        
        scn.save_dataset(prod_04, filename=kwargs.get("goes_native_color04_png"), writer='simple_image')
        
        ######scn_res_04 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_04 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_04.save_dataset(prod_04, filename=kwargs.get("wgs84_color04_tif"), writer='geotiff')
        scn_res_04.save_dataset(prod_04, filename=kwargs.get("wgs84_color04_png"), writer='simple_image')

        scn_mercator_04 = scn.resample(area_mercator, resampler='kd_tree', **resample_kwargs)
        scn_mercator_04.save_dataset(prod_04, filename=kwargs.get("mercator_color04_png"), writer='simple_image')
        
        del scn_res_04
        del scn_mercator_04
        scn.unload(prod_04)
        gc.collect()
        print("      Done and Cleared.")
        
        # --- BLOQUE INDEPENDIENTE: COLOR 05 ---
        print(f"      [Step 05/06]   Processing Color 05 (my_fdc_fn05)...", flush=True)
        prod_05 = 'my_fdc_fn05'
        scn.load([prod_05])
        
        scn.save_dataset(prod_05, filename=kwargs.get("goes_native_color05_png"), writer='simple_image')
        
        ######scn_res_05 = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))
        scn_res_05 = scn.resample(area_def, resampler='kd_tree', **resample_kwargs)
        scn_res_05.save_dataset(prod_05, filename=kwargs.get("wgs84_color05_tif"), writer='geotiff')
        scn_res_05.save_dataset(prod_05, filename=kwargs.get("wgs84_color05_png"), writer='simple_image')

        scn_mercator_05 = scn.resample(area_mercator, resampler='kd_tree', **resample_kwargs)
        scn_mercator_05.save_dataset(prod_05, filename=kwargs.get("mercator_color05_png"), writer='simple_image')
        
        del scn_res_05
        del scn_mercator_05
        scn.unload(prod_05)
        gc.collect()
        print("      Done and Cleared.")

        print("      [Step 06/06]   Exporting FDCF fire points...", flush=True)
        fire_points = export_fdcf_fire_points(
            nc_path=str(file_path),
            output_csv=kwargs.get("fire_points_csv"),
            output_geojson=kwargs.get("fire_points_geojson"),
        )
        print(f"      Fire points exported: {len(fire_points)}")
        
        # --- FINALIZACIN ---
        duration = round(time.time() - start_time, 2)
        print(f"\n      [Summary] Total time: {duration}s | Status: Success")
        return True

    except Exception as e:
        print(f"\n       [FNP01 ERROR] {str(e)}")
        return False
        
# =============================================================================
# 3. DIAGNOSTIC MAIN (Local testing)
# =============================================================================
if __name__ == "__main__":
    # Intentar cargar configuracin global de Satpy
    try:
        from legion_goes.satpy_config import my_config_satpy
        print(" Global Satpy Config loaded.")
    except ImportError:
        print("  Global config not found. Using defaults.")

    print("\n" + " ABI L2 FDCF: LINEAR PROCESSING ".center(80, "="))
    
    # Test paths
    working_dir = Path.cwd() 
    test_dir = working_dir / "test_one_image"
    nc_candidates = sorted(list(test_dir.glob("*FDCF*.nc")))

    if not nc_candidates:
        print(f" Error: No .nc files found in {test_dir}")
    else:
        target_nc = nc_candidates[0]
        output_base = test_dir / "test_outputs" / target_nc.stem
        output_base.mkdir(parents=True, exist_ok=True)

        print(f" INPUT : {target_nc.name}")
        print(f" OUTPUT: {output_base}")
        print("-" * 80)

        # Generate names and full paths
        dict_names = gen_dict_output_file_name(nc_path=str(target_nc))
        dict_paths = {k: str(output_base / v) for k, v in dict_names.items()}

        # Ejecucin
        success = run_proc_ABI_L2_FDCF_fnp01(nc_path=str(target_nc), **dict_paths)

        if success:
            print("-" * 80)
            print(f" PROCESS COMPLETED SUCCESSFULLY")
        else:
            print("-" * 80)
            print(f" PROCESS FAILED.")

    print("=" * 80 + "\n")
