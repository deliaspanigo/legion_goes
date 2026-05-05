# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/core/goes_info_sat.py
# Version: 1.1.0 (Atomic Object-Driven SoT)
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
    from datetime import datetime
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
# CONFIGURATION & HISTORICAL TRANSITIONS
# ===================================================================
_AVAILABLE_GOES_POSITIONS = ("east", "west")
# Exact operational transition dates (Source: NOAA)
_TRANSITIONS = {
    "east_16_to_19": datetime(2025, 4, 7), # GOES-19 declared operational GOES-East on April 7, 2025
    "west_17_to_18": datetime(2023, 1, 4), # GOES-18 assumed GOES-West
    "east_13_to_16": datetime(2017, 12, 18) # Historical GOES-13 to GOES-16
}
_SAVED_INFO_SAT_GOES = {
    "16": {"id": "16", "bucket": "noaa-goes16", "name01": "16", "name02": "G16", "name03": "GOES16", "position": "east"},
    "17": {"id": "17", "bucket": "noaa-goes17", "name01": "17", "name02": "G17", "name03": "GOES17", "position": "west"},
    "18": {"id": "18", "bucket": "noaa-goes18", "name01": "18", "name02": "G18", "name03": "GOES18", "position": "west"},
    "19": {"id": "19", "bucket": "noaa-goes19", "name01": "19", "name02": "G19", "name03": "GOES19", "position": "east"}
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
# IMMUTABLE OBJECTS (Closed objects)
# ===================================================================
SAVED_INFO_SAT_GOES = _make_deep_immutable(_SAVED_INFO_SAT_GOES)
AVAILABLE_GOES_ID = tuple(SAVED_INFO_SAT_GOES.keys())
AVAILABLE_GOES_POSITIONS = _make_deep_immutable(_AVAILABLE_GOES_POSITIONS)

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: SATELLITE SOT INTEGRITY TEST ".center(80, "="))
    print("Testing SoT immutability and integrity...\n")

    tests_passed = 0
    total_tests = 5

    try:
        # Test 1: Check if SAVED_INFO_SAT_GOES is immutable proxy
        assert isinstance(SAVED_INFO_SAT_GOES, MappingProxyType), "SAVED_INFO_SAT_GOES must be MappingProxyType"
        print("Test 1: SAVED_INFO_SAT_GOES is immutable proxy → ✅ OK")
        tests_passed += 1

        # Test 2: Check number of satellites
        assert len(SAVED_INFO_SAT_GOES) == 4, f"Expected 4 satellites, got {len(SAVED_INFO_SAT_GOES)}"
        print("Test 2: Catalog has 4 satellites → ✅ OK")
        tests_passed += 1

        # Test 3: Check if AVAILABLE_GOES_ID and AVAILABLE_GOES_POSITIONS are tuples
        assert isinstance(AVAILABLE_GOES_ID, tuple), "AVAILABLE_GOES_ID must be tuple"
        assert len(AVAILABLE_GOES_ID) == 4, f"Expected 4 IDs, got {len(AVAILABLE_GOES_ID)}"
        assert isinstance(AVAILABLE_GOES_POSITIONS, tuple), "AVAILABLE_GOES_POSITIONS must be tuple"
        assert len(AVAILABLE_GOES_POSITIONS) == 2, f"Expected 2 positions, got {len(AVAILABLE_GOES_POSITIONS)}"
        print("Test 3: AVAILABLE_GOES_ID and AVAILABLE_GOES_POSITIONS are valid tuples → ✅ OK")
        tests_passed += 1

        # Test 4: Runtime immutability check on root
        try:
            SAVED_INFO_SAT_GOES["16"] = "test"
            print("Test 4: Root modification → ❌ FAILED (no error)")
        except TypeError:
            print("Test 4: Root modification blocked → ✅ OK")
            tests_passed += 1

        # Test 5: Runtime immutability check on nested dict
        try:
            SAVED_INFO_SAT_GOES["16"]["bucket"] = "test"
            print("Test 5: Nested modification → ❌ FAILED (no error)")
        except TypeError:
            print("Test 5: Nested modification blocked → ✅ OK")
            tests_passed += 1

        print("\n" + f" TESTS SUMMARY: {tests_passed}/{total_tests} PASSED ".center(80, "="))
        if tests_passed == total_tests:
            print("   🎉 ALL INTEGRITY TESTS PASSED SUCCESSFULLY 🎉")
        else:
            print("   ❌ Some tests failed - review above")

    except AssertionError as ae:
        print(f"\n❌ [ASSERTION FAILED]: {ae}")
    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
