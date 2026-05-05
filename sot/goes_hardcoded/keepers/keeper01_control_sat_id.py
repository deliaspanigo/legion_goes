# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/keepers/keeper01_control_sat_id.py
# Version: 1.1.0 (Atomic Object-Driven SoT)
# =============================================================================

# -------------------------------------------------------------------
# IMPORT DIRECT - ONLY os and file name
# -------------------------------------------------------------------
import os

# Safe detection of the current file name
try:
    current_file = os.path.basename(__file__)
except NameError:
    # We are likely in a Jupyter Notebook or Interactive Session
    current_file = "Jupyter_Notebook_Session"

# -------------------------------------------------------------------
# TRY: System libreries
# -------------------------------------------------------------------
try:
    import sys
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SOT - {current_file}]")
    print("="*80)
    print(f" Failed to load system library 'sys': {e}")
    print(" This is a core Python module. Your Python installation may be broken.")
    print(" Please reinstall Python or check your environment.")
    print("="*80 + "\n")
    raise SystemExit(1)

# -------------------------------------------------------------------
# TRY 02: Project-specific libraries / modules
# -------------------------------------------------------------------
try:
    from legion_goes.sot.goes_hardcoded.core.goes_info_sat import AVAILABLE_GOES_ID
except ImportError as e:
    # Dynamic file name (safe for Jupyter/notebook)
    
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SOT - {current_file}]")
    print("="*80)
    print(f" Failed to load project module: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print(" Check if 'goes_info_sat.py' exists in goes_hardcoded/core/ and is importable.")
    print(" Ensure the package structure and __init__.py files are correct.")
    print("="*80 + "\n")
    raise SystemExit(1)
    
def control_sat_id(sat_id):
    """
    GUARD: Validates 'sat_id' against the Source of Truth (SoT).
    Extremely strict validation for the Legion GOES system.
   
    Accepts **only** exactly '16', '17', '18' or '19' (exactly 2 digits, no spaces, only numeric).
    Any deviation raises an immediate and explicit error.
    """
    ctx = sys._getframe().f_code.co_name
    if sat_id is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is None. A valid satellite ID is required.")
   
    if not isinstance(sat_id, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' ({type(sat_id).__name__}). Expected type: str.")
   
    if " " in sat_id:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' and contains spaces. Provide a clean string (exactly '16', '17', '18' or '19').")
   
    if len(sat_id) != 2:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' and does not have exactly 2 characters (must be exactly '16', '17', '18' or '19').")
   
    if not sat_id.isdigit():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' and contains non-digit characters. Expected exactly 2 digits (e.g., '19').")
   
    if sat_id not in AVAILABLE_GOES_ID:
        valid_options = ", ".join(AVAILABLE_GOES_ID)
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' '{sat_id}' is not found in the Source of Truth.\n💡 Available satellite IDs: {valid_options}")

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: CONTROL_SAT_ID GUARD TEST ".center(80, "="))
    print("Testing control_sat_id() with strict validation...\n")

    tests_passed = 0
    total_tests = 5

    try:
        # Test 1: Valid sat_id
        control_sat_id("19")
        print("Test 1: Valid sat_id '19' → ✅ OK")
        tests_passed += 1

        # Test 2: Valid edge case
        control_sat_id("16")
        print("Test 2: Valid sat_id '16' → ✅ OK")
        tests_passed += 1

        # Test 3: Invalid - None
        try:
            control_sat_id(None)
            print("Test 3: None input → ❌ FAILED (no error raised)")
        except ValueError as e:
            print(f"Test 3: None input → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 4: Invalid type (int)
        try:
            control_sat_id(19)
            print("Test 4: Invalid type (int) → ❌ FAILED (no error)")
        except TypeError as e:
            print(f"Test 4: Invalid type (int) → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 5: Invalid sat_id (not registered)
        try:
            control_sat_id("20")
            print("Test 5: Invalid sat_id '20' → ❌ FAILED (no error)")
        except ValueError as e:
            print(f"Test 5: Invalid sat_id '20' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        print("\n" + f" TESTS SUMMARY: {tests_passed}/{total_tests} PASSED ".center(80, "="))
        if tests_passed == total_tests:
            print("   🎉 ALL TESTS PASSED SUCCESSFULLY 🎉")
        else:
            print("   ❌ Some tests failed - review above")

    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
