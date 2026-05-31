"""
Path: legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f01_code/GLM_L2_LCFA/run_proc_GLM_L2_LCFA_fnp01.py
Version: 0.2.5 (Strict Pixel Dimensions)
Description: Forced pixel resolution by removing bbox_inches='tight'.
Last modification: 07-05-2026 22:45
"""
# ========================================================================================================================================
#  Execution: python3 -m  legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.GLM_L2_LCFA.proc_GLM_L2_LCFA_fnp01
# ========================================================================================================================================

import os
import time
import json
import re
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path

# --- SOT LIBRARIES ---
from legion_goes.pycode_actions.pack01.fn_common.get_position_by_sat_id import get_position_by_sat_id

def gen_dict_output_file_name(nc_path): 
    nc_file_name = Path(nc_path).name
    match = re.search(r"OR_(?P<prod>GLM-L2-LCFA)_(?P<sat>G\d{2})_s(?P<start>\d{14})", nc_file_name)
    if not match:
        raise ValueError(f"Could not parse GLM file format: {nc_file_name}")

    str_sat_num = match.group("sat")[1:] 
    str_stimestamp = match.group("start") 
    str_pos_label = get_position_by_sat_id(sat_id = str_sat_num)
    str_name = f"SP-01-simple_G{str_sat_num}-{str_pos_label}-s{str_stimestamp}"
    
    return {
        "glm_json":  f"{str_name}_LCFA-fnp01.json",
        "plot_goes": f"{str_name}_LCFA-fnp01_VIEW-GOES.png",
        "plot_w84":  f"{str_name}_LCFA-fnp01_VIEW-WGS84.png"
    }

def run_proc_GLM_L2_LCFA_fnp01(nc_path, **kwargs):
    start_time = time.time()
    file_path = Path(nc_path)
    
    match_sat = re.search(r"_G(?P<num>\d{2})_", file_path.name)
    str_sat_num = match_sat.group("num") if match_sat else "16"
    pos_map = {"16": -75.0, "17": -137.2, "18": -137.0, "19": -75.0}
    lon_cen = pos_map.get(str_sat_num, -75.0) 

    try:
        # [Step 01] Reading
        print(f"\n      [Step 01/04]  Reading NetCDF (GOES-{str_sat_num})...", end=" ", flush=True)
        with nc.Dataset(file_path) as ds:
            qf = ds.variables['flash_quality_flag'][:]
            mask = (qf == 0)
            lats = ds.variables['flash_lat'][:][mask]
            lons = ds.variables['flash_lon'][:][mask]
            energies = ds.variables['flash_energy'][:][mask]
        print(f"Done. ({len(lats)} flashes)")

        # [Step 02] GeoJSON
        print(f"      [Step 02/04]   Building GeoJSON...", end=" ", flush=True)
        features = []
        for lat, lon, en in zip(lats, lons, energies):
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(float(lon), 5), round(float(lat), 5)]},
                "properties": {"energy": round(float(en), 2)}
            })
        with open(kwargs.get("glm_json"), 'w') as f:
            json.dump({"type": "FeatureCollection", "features": features}, f)
        print("Done.")

        # [Step 03] Plots
        print(f"      [Step 03/04]  Generating Stackable Plots...", end=" ", flush=True)
        
        # 1. GOES VIEW: 5424 x 5424 px
        fig_g = plt.figure(figsize=(18.08, 18.08), facecolor='black')
        # Rect [0,0,1,1] asegura que el mapa ocupe TODO el canvas
        ax_g = fig_g.add_axes([0, 0, 1, 1], projection=ccrs.Geostationary(central_longitude=lon_cen))
        ax_g.set_axis_off()
        ax_g.set_global() 
        ax_g.add_feature(cfeature.COASTLINE, edgecolor='cyan', linewidth=1.5)
        
        if len(lons) > 0:
            ax_g.scatter(lons, lats, c=energies, s=35, cmap='plasma', transform=ccrs.PlateCarree(), zorder=10)
        
        # ELIMINADO bbox_inches='tight' para mantener resolucion exacta
        fig_g.savefig(kwargs.get("plot_goes"), dpi=300, facecolor='black')
        plt.close(fig_g)

        # 2. WGS84 VIEW: 3600 x 1800 px
        fig_w = plt.figure(figsize=(36, 18), facecolor='black')
        ax_w = fig_w.add_axes([0, 0, 1, 1], projection=ccrs.PlateCarree())
        ax_w.set_axis_off()
        ax_w.set_global() 
        ax_w.add_feature(cfeature.COASTLINE, edgecolor='cyan', linewidth=1.0)
        
        if len(lons) > 0:
            ax_w.scatter(lons, lats, c=energies, s=25, cmap='plasma', transform=ccrs.PlateCarree(), zorder=10)
            
        # ELIMINADO bbox_inches='tight' para mantener resolucion exacta
        fig_w.savefig(kwargs.get("plot_w84"), dpi=100, facecolor='black')
        plt.close(fig_w)
        print("Done.")

        # [Step 04] Summary
        duration = round(time.time() - start_time, 2)
        print(f"      [Step 04/04]  Finished in {duration}s")
        return True

    except Exception as e:
        print(f"\n       [ERROR] {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + " FNP01: STRICT RESOLUTION TEST ".center(80, "="))
    current_dir = Path.cwd() / "test_one_image"
    nc_candidates = sorted(list(current_dir.glob("*LCFA*.nc")))

    if not nc_candidates:
        print(f" Error: No .nc files found.")
    else:
        target_nc = nc_candidates[0]
        test_out = current_dir / "test_outputs" / target_nc.stem
        test_out.mkdir(parents=True, exist_ok=True)
        print(f" TARGET: {target_nc.name}")
        output_paths = {k: str(test_out / v) for k, v in gen_dict_output_file_name(str(target_nc)).items()}

        if run_proc_GLM_L2_LCFA_fnp01(str(target_nc), **output_paths):
            print("-" * 80 + f"\n SUCCESS. WGS84 is exactly 3600x1800. Results in: {test_out}")
    print("=" * 80 + "\n")
