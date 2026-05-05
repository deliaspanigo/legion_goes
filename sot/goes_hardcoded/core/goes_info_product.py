# =============================================================================
# FILE PATH: src/legion_goes/sot/goes_hardcoded/core/goes_info_product.py
# Version: 1.0.6 (Fully Immutable SoT - Data Only)
# =============================================================================

# -------------------------------------------------------------------
# IMPORT DIRECT - ONLY os
# -------------------------------------------------------------------
import os

# -------------------------------------------------------------------
# TRY 01: System libraries (Python standard library)
# -------------------------------------------------------------------
try:
    import sys
    from types import MappingProxyType
except ImportError as e:
    file_name = "unknown_file.py"
    full_path = "unknown_path"
    try:
        file_name = os.path.basename(__file__)
        full_path = os.path.relpath(__file__, start=os.getcwd())
    except NameError:
        file_name = "interactive session"
        full_path = "notebook or interactive environment"
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SOT - {file_name}]")
    print("="*80)
    print(f" Failed to load base system libraries: {e}")
    print(f" File/Path: {full_path}")
    print(" This is a core Python module. Your Python installation may be broken.")
    print(" Please reinstall Python or check your environment.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# REQUIRED KEYS (Mandatory for all products)
# ===================================================================
_REQUIRED_KEYS = frozenset({
    "id", "full_name", "description", "level", "init_file_name",
    "units", "typical_range", "main_use", "notes",
    "total_files_one_day", "time_lapse", "time_lapse_label",
    "type", "default_time", "time_format"
})
_REQUIRED_RASTER_KEYS = frozenset({
    "cadence_full_disk", "resolution_nominal", "shape_full_disk"
})
_REQUIRED_VECTORIAL_KEYS = frozenset({
    "cadence_full_disk", "cadence_grouped", "resolution_spatial", "shape"
})

# ===================================================================
# PRIVATE SOURCE OF TRUTH
# ===================================================================
_PRIVATE_PRODUCTS = {
    "ABI-L2-LSTF": {
        "id": "ABI-L2-LSTF",
        "full_name": "Land Surface Temperature",
        "description": "Land Surface Temperature product (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-LSTF-M6_G",
        "units": "Kelvin (original) → Celsius (post-processed)",
        "typical_range": "-100 °C to +100 °C",
        "main_use": "Drought monitoring, vegetation thermal stress",
        "notes": "Values outside disk = fill (NaN).",
        "total_files_one_day": 24,
        "time_lapse": "01hour",
        "time_lapse_label": "time_lapse_01hour",
        "type": "raster",
        "cadence_full_disk": "1 hour",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": [""],
            "seconds": [""]
        },
        "time_format": "YYYYDDDHH"
    },
    "ABI-L2-MCMIPF": {
        "id": "ABI-L2-MCMIPF",
        "full_name": "Cloud and Moisture Imagery",
        "description": "Multiband imagery product (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-MCMIPF-M6_G",
        "units": "Reflectance/Brightness Temp",
        "typical_range": "0-100% / 0-400K",
        "main_use": "General forecasting and imagery",
        "notes": "Full Disk, contains all ABI bands",
        "total_files_one_day": 144,
        "time_lapse": "10minutes",
        "time_lapse_label": "time_lapse_10minutes",
        "type": "raster",
        "cadence_full_disk": "10 minutes",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": [f"{m:02d}" for m in range(0, 60, 10)],
            "seconds": [""]
        },
        "time_format": "YYYYDDDHHMM"
    },
    "ABI-L2-FDCF": {
        "id": "ABI-L2-FDCF",
        "full_name": "Fire Detection and Characterization",
        "description": "Fire hot spot detection and characterization (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-FDCF-M6_G",
        "units": "Kelvin (Fire Temp), Megawatts (Fire Power)",
        "typical_range": "300K - 1200K",
        "main_use": "Wildfire detection and monitoring",
        "notes": "Includes Fire Temperature, Area, and Power (FRP).",
        "total_files_one_day": 144,
        "time_lapse": "10minutes",
        "time_lapse_label": "time_lapse_10minutes",
        "type": "raster",
        "cadence_full_disk": "10 minutes",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": [f"{m:02d}" for m in range(0, 60, 10)],
            "seconds": [""]
        },
        "time_format": "YYYYDDDHHMM"
    },
    "GLM-L2-LCFA": {
        "id": "GLM-L2-LCFA",
        "full_name": "Lightning Detection",
        "description": "Geostationary Lightning Mapper events",
        "level": "L2",
        "init_file_name": "OR_GLM-L2-LCFA_G",
        "units": "Events/Flashes",
        "typical_range": "N/A",
        "main_use": "Storm intensification monitoring",
        "notes": "Vectorial data",
        "total_files_one_day": 4320,
        "time_lapse": "20sec",
        "time_lapse_label": "time_lapse_20sec",
        "type": "vectorial",
        "cadence_full_disk": "20 seconds",
        "cadence_grouped": "1 min",
        "resolution_spatial": "8 km",
        "shape": None,
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": [f"{m:02d}" for m in range(0, 60, 1)],
            "seconds": [f"{m:02d}" for m in range(0, 60, 20)],
        },
        "time_format": "YYYYDDDHHMMSS"
    }
}

# ===================================================================
# IMMUTABILITY ENGINE
# ===================================================================
def _make_deep_immutable(obj):
    if isinstance(obj, dict):
        return MappingProxyType({k: _make_deep_immutable(v) for k, v in obj.items()})
    elif isinstance(obj, (list, tuple)):
        return tuple(_make_deep_immutable(i) for i in obj)
    return obj

# ===================================================================
# IMMUTABLE OBJECTS (final exports)
# ===================================================================
SAVED_INFO_PROD_GOES = _make_deep_immutable(_PRIVATE_PRODUCTS)
AVAILABLE_GOES_PRODUCTS = tuple(SAVED_INFO_PROD_GOES.keys())

# ===================================================================
# INTERNAL INTEGRITY CHECK (moved AFTER defining the objects)
# ===================================================================
def _validate_module_integrity():
    """Checks internal product dictionary consistency and required fields."""
    ctx = "[CRITICAL - goes_info_product.py - _validate_module_integrity]"
    for product_id, data in SAVED_INFO_PROD_GOES.items():
        missing_common = _REQUIRED_KEYS - data.keys()
        if missing_common:
            raise ImportError(f"\n{ctx} Product '{product_id}' missing common keys: {missing_common}")
        p_type = data.get("type")
        if p_type == "raster":
            missing = _REQUIRED_RASTER_KEYS - data.keys()
        elif p_type == "vectorial":
            missing = _REQUIRED_VECTORIAL_KEYS - data.keys()
        else:
            raise ImportError(f"\n{ctx} Product '{product_id}' has invalid type: '{p_type}'.")
        if missing:
            raise ImportError(f"\n{ctx} Type '{p_type}' mismatch in '{product_id}'. Missing: {missing}")


# ===================================================================
# UNIT INTERNAL COCNTROL Auto Excecution)
# ===================================================================
_validate_module_integrity()


        
# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: PRODUCT SOT INTEGRITY TEST ".center(80, "="))
    print("Testing SoT immutability and integrity...\n")

    try:
        # Test 1: Check if SAVED_INFO_PROD_GOES is immutable proxy
        assert isinstance(SAVED_INFO_PROD_GOES, MappingProxyType), "SAVED_INFO_PROD_GOES must be MappingProxyType"
        print("Test 1: SAVED_INFO_PROD_GOES is immutable proxy → ✅ OK")

        # Test 2: Check number of products
        assert len(SAVED_INFO_PROD_GOES) == 4, f"Expected 4 products, got {len(SAVED_INFO_PROD_GOES)}"
        print("Test 2: Catalog has 4 products → ✅ OK")

        # Test 3: Check if AVAILABLE_GOES_PRODUCTS is a tuple
        assert isinstance(AVAILABLE_GOES_PRODUCTS, tuple), "AVAILABLE_GOES_PRODUCTS must be tuple"
        assert len(AVAILABLE_GOES_PRODUCTS) == 4, f"Expected 4 products in tuple, got {len(AVAILABLE_GOES_PRODUCTS)}"
        print("Test 3: AVAILABLE_GOES_PRODUCTS is valid tuple → ✅ OK")

        # Test 4: Runtime immutability check on root
        try:
            SAVED_INFO_PROD_GOES["ABI-L2-LSTF"] = "test"
            print("Test 4: Root modification → ❌ FAILED (no error)")
        except TypeError:
            print("Test 4: Root modification blocked → ✅ OK")
        tests_passed += 1

        # Test 5: Runtime immutability check on nested dict
        try:
            SAVED_INFO_PROD_GOES["ABI-L2-LSTF"]["type"] = "test"
            print("Test 5: Nested modification → ❌ FAILED (no error)")
        except TypeError:
            print("Test 5: Nested modification blocked → ✅ OK")
        tests_passed += 1

        print("\n" + " ALL INTEGRITY TESTS PASSED ".center(80, "="))
        print("   🎉 SoT is fully immutable and valid 🎉")

    except AssertionError as ae:
        print(f"\n❌ [ASSERTION FAILED]: {ae}")
    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
