"""
Reference information for LSTF FNP01.

These values are used by apps to draw a stable temperature reference. Keeping
them in Python makes the processing code the source of truth.
"""


def sp_lstf_fnp01_reference():
    """
    Return the standard LSTF Celsius reference used by LegionGOES.
    """

    return {
        "product": "ABI-L2-LSTF",
        "fnp": "fnp01",
        "unit": "Celsius",
        "scale_min": -60,
        "scale_max": 60,
        "zero_line": 0,
        "description": (
            "Land surface temperature converted from Kelvin to Celsius. "
            "The reference is fixed so the same temperature keeps the same "
            "color across different images."
        ),
    }
