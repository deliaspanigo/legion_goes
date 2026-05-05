# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/access/get_SOT_define_position.py
# Version: 1.1.1 (Atomic Object-Driven SoT - Access Layer)
# =============================================================================

import sys

# Import guards from the keepers folder (according to your structure)
try:
    from legion_goes.sot.goes_hardcoded.keepers.keeper01_control_sat_id import control_sat_id
    from legion_goes.sot.goes_hardcoded.keepers.keeper02_control_position import control_position
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [ACCESS - get_SOT_define_position.py]")
    print("="*80)
    print(f" Failed to load guard functions: {e}")
    print(" Please verify that the keepers folder contains the control files.")
    print(" Check the package structure and __init__.py files.")
    print("="*80 + "\n")
    raise SystemExit(1)

# Import SoT data from core
try:
    from legion_goes.sot.goes_hardcoded.core.goes_info_sat import SAVED_INFO_SAT_GOES
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [ACCESS - get_SOT_define_position.py]")
    print("="*80)
    print(f" Failed to load SoT data from core: {e}")
    print(" Ensure 'goes_info_sat.py' exists in goes_hardcoded/core/.")
    print("="*80 + "\n")
    raise SystemExit(1)

def get_SOT_define_position(sat_id: str) -> str:
    """
    Returns the operational position ('east' or 'west') for a specific satellite ID.
    Resolves directly from the Source of Truth (SoT) metadata.
   
    Extremely strict: validates input, retrieves metadata, and checks stored position.
    """
    ctx = sys._getframe().f_code.co_name
    try:
        control_sat_id(sat_id)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Invalid satellite ID. Details: {e}"
        raise type(e)(error_msg) from None
    try:
        sat_metadata = SAVED_INFO_SAT_GOES[sat_id]
    except KeyError:
        raise KeyError(f"❌ [INTEGRITY ERROR in {ctx}()]: Satellite '{sat_id}' not found in SoT.")
    if "position" not in sat_metadata:
        raise RuntimeError(f"❌ [INTEGRITY ERROR in {ctx}()]: Satellite metadata for '{sat_id}' missing required field 'position' in Source of Truth.")
   
    resolved_position = sat_metadata["position"]
    try:
        control_position(resolved_position)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Resolved position '{resolved_position}' for satellite '{sat_id}' is invalid according to guards. Details: {e}"
        raise type(e)(error_msg) from None
    return resolved_position

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GET_SOT_DEFINE_POSITION TEST ".center(80, "="))
    print("Testing get_SOT_define_position() with strict validation...\n")

    tests_passed = 0
    total_tests = 4

    try:
        # Test 1: Valid satellite ID (should return 'west')
        pos_18 = get_SOT_define_position("18")
        assert pos_18 == "west", f"Expected 'west' for sat 18, got '{pos_18}'"
        print("Test 1: Position for sat '18' → ✅ OK ('west')")
        tests_passed += 1

        # Test 2: Valid satellite ID (should return 'east')
        pos_19 = get_SOT_define_position("19")
        assert pos_19 == "east", f"Expected 'east' for sat 19, got '{pos_19}'"
        print("Test 2: Position for sat '19' → ✅ OK ('east')")
        tests_passed += 1

        # Test 3: Invalid sat_id (should raise)
        try:
            get_SOT_define_position("20")
            print("Test 3: Invalid sat_id '20' → ❌ FAILED (no error)")
        except Exception as e:
            print(f"Test 3: Invalid sat_id '20' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 4: Invalid type input (should raise)
        try:
            get_SOT_define_position(123)
            print("Test 4: Invalid type (int) → ❌ FAILED (no error)")
        except TypeError as e:
            print(f"Test 4: Invalid type → ✅ OK (caught expected error): {e}")
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
