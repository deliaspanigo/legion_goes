"""
Small helpers for MCMIPF FNP01.
"""


def apply_dark_pixel_mask(data_array, threshold=0.05):
    """
    Keep only pixels bright enough for a simple day-only True Color layer.
    """

    avg_intensity = data_array.mean(dim="bands")
    return data_array.where(avg_intensity > threshold)

