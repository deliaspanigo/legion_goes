"""
LSTF FNP01 - WGS84 products.

This function generates WGS84 PNGs and GeoTIFFs. The grey GeoTIFF keeps the
Celsius raster in a GIS-friendly form, while the PNGs are lightweight visual
products for Leaflet and Shiny.
"""

import time

import numpy as np
import rasterio
from rasterio.transform import from_origin
from satpy import Scene

from legion_goes.pycode_01_products.common import (
    area_wgs84,
    ensure_input_file,
    ensure_output_files,
    satpy_reader_chunks,
    satpy_resample_kwargs,
)
from legion_goes.pycode_01_products.ABI_L2_LSTF.sp_lstf_fnp01_schema import (
    sp_lstf_fnp01_output_schema,
)


def _write_wgs84_celsius_geotiff(data_array, output_path):
    """
    Write the WGS84 Celsius DataArray as a real float GeoTIFF.

    Satpy's GeoTIFF writer is excellent for visual products, but for the LSTF
    operative workflow we need a data raster: Celsius values must remain
    Celsius values, and pixels outside the valid swath must remain nodata.
    """

    data = data_array.data
    if hasattr(data, "compute"):
        data = data.compute()

    data = np.ma.filled(data, np.nan).astype("float32", copy=False)

    nodata_value = np.float32(-9999.0)
    data_to_write = np.where(np.isfinite(data), data, nodata_value).astype(
        "float32",
        copy=False,
    )

    height, width = data_to_write.shape
    transform = from_origin(-180.0, 90.0, 360.0 / width, 180.0 / height)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=float(nodata_value),
        compress="deflate",
    ) as dst:
        dst.write(data_to_write, 1)


def sp_lstf_fnp01_wgs84(nc_path, output_dir):
    """
    Generate LSTF FNP01 products in global WGS84.
    """

    start_time = time.time()
    file_path = ensure_input_file(nc_path)
    outputs = sp_lstf_fnp01_output_schema(file_path, output_dir)

    print("[LSTF FNP01 WGS84] Loading LSTF scene...", flush=True)

    scn = Scene(
        filenames=[str(file_path)],
        reader="abi_l2_nc",
        reader_kwargs={"chunks": satpy_reader_chunks()},
    )

    scn.load(["LST"])
    scn["LST"] = scn["LST"] - 273.15
    scn["LST"].attrs["units"] = "Celsius"
    scn.load(["lst_celsius_color01"])

    print("[LSTF FNP01 WGS84] Resampling to EPSG:4326...", flush=True)

    scn_wgs84 = scn.resample(
        area_wgs84(),
        resampler="kd_tree",
        fill_value=np.nan,
        **satpy_resample_kwargs(),
    )

    print("[LSTF FNP01 WGS84] Writing GeoTIFFs...", flush=True)

    _write_wgs84_celsius_geotiff(
        scn_wgs84["LST"],
        str(outputs["wgs84_grey_tif"]),
    )
    scn_wgs84.save_dataset(
        "lst_celsius_color01",
        filename=str(outputs["wgs84_color_tif"]),
        writer="geotiff",
    )

    print("[LSTF FNP01 WGS84] Writing PNGs...", flush=True)

    scn_wgs84.save_dataset(
        "LST",
        filename=str(outputs["wgs84_grey_png"]),
        writer="simple_image",
    )
    scn_wgs84.save_dataset(
        "lst_celsius_color01",
        filename=str(outputs["wgs84_color_png"]),
    )

    result = {
        "wgs84_grey_png": outputs["wgs84_grey_png"],
        "wgs84_color_png": outputs["wgs84_color_png"],
        "wgs84_grey_tif": outputs["wgs84_grey_tif"],
        "wgs84_color_tif": outputs["wgs84_color_tif"],
    }
    ensure_output_files(result)

    print(
        f"[LSTF FNP01 WGS84] Finished in {round(time.time() - start_time, 2)}s",
        flush=True,
    )

    return result
