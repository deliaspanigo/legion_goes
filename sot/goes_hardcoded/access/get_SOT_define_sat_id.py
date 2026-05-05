# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/access/get_SOT_define_sat_id.py
# Version: 1.1.1 (Atomic Object-Driven SoT - Access Layer)
# =============================================================================

import sys
from datetime import datetime

# -------------------------------------------------------------------
# TRY: Import guards from keepers (project-specific)
# -------------------------------------------------------------------
try:
    from legion_goes.sot.goes_hardcoded.keepers.keeper02_control_position import control_position
    from legion_goes.sot.goes_hardcoded.keepers.keeper04_control_year import control_year
    from legion_goes.sot.goes_hardcoded.keepers.keeper05_control_day import control_day
    from legion_goes.sot.goes_hardcoded.keepers.keeper01_control_sat_id import control_sat_id
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [ACCESS - get_SOT_define_sat_id.py]")
    print("="*80)
    print(f" Failed to load guard functions from keepers/: {e}")
    print(" Please verify that the keepers folder contains the control files.")
    print(" Check the package structure and __init__.py files.")
    print("="*80 + "\n")
    raise SystemExit(1)

def get_SOT_define_sat_id(position: str, year: str, day: str) -> str:
    """
    Determines the active satellite ID for a given position ('east' or 'west') at a specific year and Julian day.
    Uses strict TRANSITIONS logic to resolve the historical/operational satellite.
   
    Extremely strict: inputs must be exactly as validated by control_* guards.
    Returns the resolved satellite ID ('16', '17', '18', or '19') as string.
    """
    ctx = sys._getframe().f_code.co_name
    try:
        control_position(position)
        control_year(year)
        control_day(day)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Invalid input arguments. Details: {e}"
        raise type(e)(error_msg) from None
    date_str = f"{year}-{day}"
    try:
        date_obj = datetime.strptime(date_str, "%Y-%j")
    except ValueError as ve:
        raise ValueError(f"❌ [DATE PARSE ERROR in {ctx}()]: Invalid year-day combination '{date_str}'. Details: {ve}") from None
    if position == "east":
        resolved_sat_id = "19" if date_obj >= TRANSITIONS["east_16_to_19"] else "16"
    elif position == "west":
        resolved_sat_id = "18" if date_obj >= TRANSITIONS["west_17_to_18"] else "17"
    else:
        raise RuntimeError(f"❌ [🛡️🛡️🛡️ INTEGRITY ERROR in {ctx}()]: Unknown position '{position}' after guard validation - possible logic bypass.")
    try:
        control_sat_id(resolved_sat_id)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Resolved sat_id '{resolved_sat_id}' is invalid according to Source of Truth. Details: {e}"
        raise type(e)(error_msg) from None
    return resolved_sat_id

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GET_SOT_DEFINE_SAT_ID TEST ".center(80, "="))
    print("Testing get_SOT_define_sat_id() with strict validation...\n")

    tests_passed = 0
    total_tests = 4

    try:
        # Test 1: Valid case - before transition (should return '16')
        sat_before = get_SOT_define_sat_id("east", "2025", "090")  # Before April 7, 2025
        assert sat_before == "16", f"Expected '16' before transition, got '{sat_before}'"
        print("Test 1: Before transition (east, 2025-090) → ✅ OK ('16')")
        tests_passed += 1

        # Test 2: Valid case - after transition (should return '19')
        sat_after = get_SOT_define_sat_id("east", "2025", "100")  # After April 7, 2025
        assert sat_after == "19", f"Expected '19' after transition, got '{sat_after}'"
        print("Test 2: After transition (east, 2025-100) → ✅ OK ('19')")
        tests_passed += 1

        # Test 3: Valid west case (should return '18')
        sat_west = get_SOT_define_sat_id("west", "2025", "050")
        assert sat_west == "18", f"Expected '18' for west, got '{sat_west}'"
        print("Test 3: West position → ✅ OK ('18')")
        tests_passed += 1

        # Test 4: Invalid position (uppercase)
        try:
            get_SOT_define_sat_id("EAST", "2026", "001")
            print("Test 4: Invalid position 'EAST' → ❌ FAILED (no error)")
        except Exception as e:
            print(f"Test 4: Invalid position 'EAST' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        print("\n" + f" TESTS SUMMARY: {tests_passed}/{total_tests} PASSED ".center(80, "="))
        if tests_passed == total_tests:
            print("   🎉 ALL TESTS PASSED SUCCESSFULLY 🎉")
        else:
            print("   ❌ Some tests failed - review above")

    except AssertionError as ae:
        print(f"\n❌ [ASSERTION FAILED]: {ae}")
    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
