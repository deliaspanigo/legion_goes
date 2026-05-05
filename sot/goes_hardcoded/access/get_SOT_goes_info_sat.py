# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/access/get_SOT_goes_info_sat.py
# Version: 1.1.2 (Atomic Object-Driven SoT - Access Layer)
# =============================================================================

import os
import sys
from types import MappingProxyType

# -------------------------------------------------------------------
# TRY: Critical imports (system and project modules)
# -------------------------------------------------------------------
try:
    from types import MappingProxyType
    from legion_goes.sot.goes_hardcoded.core.goes_info_sat import SAVED_INFO_SAT_GOES
    from legion_goes.sot.goes_hardcoded.keepers.keeper01_control_sat_id import control_sat_id
except ImportError as e:
    # Dynamic file name for accurate error reporting
    current_file = "unknown_file.py"
    try:
        current_file = os.path.basename(__file__)
    except NameError:
        current_file = "notebook cell (Jupyter/IPython)"

    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SOT - {current_file}]")
    print("="*80)
    print(f" Failed to load required modules: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print(" Check if 'goes_info_sat.py' exists in goes_hardcoded/core/.")
    print(" And 'keeper01_control_sat_id.py' in keepers/.")
    print(" Ensure the package structure and __init__.py files are correct.")
    print("="*80 + "\n")
    raise SystemExit(1)

# -------------------------------------------------------------------
# FUNCTION
# -------------------------------------------------------------------

def get_SOT_goes_info_sat(sat_id: str = None) -> MappingProxyType:
    """
    Retrieves satellite metadata from the Source of Truth (SoT).
    Extremely strict access to the immutable master object.
   
    - If sat_id is None: returns the full immutable dictionary of all satellites.
    - If sat_id is provided: returns the metadata for that exact satellite ID.
   
    Includes strict integrity checks:
    - Master object must exist, not be None, not be empty.
    - Master object MUST be exactly a MappingProxyType (immutable proxy).
   
    Validates sat_id using control_sat_id() before access.
    Raises explicit RuntimeError on ANY integrity violation.
    """
    ctx = sys._getframe().f_code.co_name
    if not hasattr(sys.modules[__name__], 'SAVED_INFO_SAT_GOES'):
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' does not exist in module namespace. Source of Truth initialization failed.")
   
    master_obj = SAVED_INFO_SAT_GOES
   
    if master_obj is None:
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' is None. Source of Truth is not initialized.")
   
    from types import MappingProxyType
    if not isinstance(master_obj, MappingProxyType):
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' is of type {type(master_obj).__name__}, but MUST be exactly MappingProxyType (immutable proxy). Source of Truth integrity violated - possible code tampering, import error, or concurrent modification.")
   
    if not master_obj:
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' is empty. Source of Truth has no satellite data.")
   
    if sat_id is None:
        return master_obj
   
    try:
        control_sat_id(sat_id)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Failed to resolve satellite ID. Details from guard: {e}"
        raise type(e)(error_msg) from None
   
    return master_obj[sat_id]

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GET_SOT_GOES_INFO_SAT TEST ".center(80, "="))
    print("Testing get_SOT_goes_info_sat() with strict validation...\n")

    tests_passed = 0
    total_tests = 4

    try:
        # Test 1: Full catalog retrieval (no sat_id)
        all_sats = get_SOT_goes_info_sat()
        assert isinstance(all_sats, MappingProxyType), "Full SoT must be MappingProxyType"
        assert len(all_sats) == 4, f"Expected 4 satellites, got {len(all_sats)}"
        print("Test 1: Full catalog retrieval → ✅ OK (4 satellites, immutable)")
        tests_passed += 1

        # Test 2: Specific satellite metadata (valid)
        g19_meta = get_SOT_goes_info_sat("19")
        assert g19_meta["bucket"] == "noaa-goes19", "GOES-19 bucket mismatch"
        assert g19_meta["position"] == "east", "GOES-19 position mismatch"
        print("Test 2: Specific satellite metadata ('19') → ✅ OK")
        tests_passed += 1

        # Test 3: Invalid sat_id (should raise)
        try:
            get_SOT_goes_info_sat("20")
            print("Test 3: Invalid sat_id '20' → ❌ FAILED (no error)")
        except Exception as e:
            print(f"Test 3: Invalid sat_id '20' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 4: Invalid type input (should raise)
        try:
            get_SOT_goes_info_sat(123)
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
