"""
Small helpers for MCMIPF FNP02.
"""

import numpy as np
from PIL import Image


def apply_grayscale_transparency(input_path, output_path, saturation_threshold=20):
    """
    Convert nearly grayscale pixels to transparent pixels.

    Satpy's colorized IR image carries useful color information for clouds, while
    much of the neutral grayscale background is not useful as a transparent
    overlay. This helper keeps the colored pixels and removes the gray ones.
    """

    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    rgb = data[:, :, :3].astype(np.int16)
    diff = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    gray_pixels = diff <= saturation_threshold
    data[gray_pixels, 3] = 0
    Image.fromarray(data).save(output_path)


def apply_white_clouds_vibrant(input_path, output_path):
    """
    Create a white cloud overlay while preserving alpha and texture.
    """

    img = Image.open(input_path).convert("RGBA")
    data = np.array(img).astype(np.float32)

    luminance = (
        data[:, :, 0] * 0.299
        + data[:, :, 1] * 0.587
        + data[:, :, 2] * 0.114
    )
    visible_pixels = data[:, :, 3] > 0

    vibrant_white = np.clip((luminance * 1.2) + 60, 0, 255)

    for channel in range(3):
        data[visible_pixels, channel] = vibrant_white[visible_pixels]

    Image.fromarray(data.astype(np.uint8)).save(output_path)
