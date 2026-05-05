# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/keepers/keeper05_control_day.py
# Version: 1.1.1 (Atomic Object-Driven SoT with Separate Critical Import Checks)
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
# TRY 01: System libraries (Python standard library)
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

# ===================================================================
# CONTROL FUNCTIONS (The Guards)
# ===================================================================
def control_day(day):
    """
    GUARD: Validates Julian day (day of year) against strict format for the Legion GOES system.
    Extremely strict validation.
    
    Accepts **only** exactly 3-digit strings like '001', '065', '366' 
    (padded with zeros, only digits, no spaces, range 001-366).
    Rejects any deviation (wrong length, non-digits, out-of-range, None, etc.).
    """
    ctx = sys._getframe().f_code.co_name

    if day is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' is None. A valid Julian day is required.")

    if not isinstance(day, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' is '{day}' ({type(day).__name__}). Expected string of exactly 3 digits (e.g., '065').")

    if " " in day:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' '{day}' contains spaces. Provide a clean 3-digit string (e.g., '065').")

    if len(day) != 3:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' '{day}' does not have exactly 3 characters. Expected format: 'DDD' (e.g., '001' or '366').")

    if not day.isdigit():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' '{day}' contains non-digit characters. Expected exactly 3 digits.")

    int_day = int(day)
    if not (1 <= int_day <= 366):
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Day '{day}' ({int_day}) is out of valid Julian day range. Must be between 001 and 366.")

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: CONTROL_DAY GUARD TEST ".center(80, "="))
    print("Testing control_day() with strict validation...\n")

    tests_passed = 0
    total_tests = 6

    try:
        # Test 1: Valid Julian day (string 3 digits)
        control_day("065")
        print("Test 1: Valid day '065' → ✅ OK")
        tests_passed += 1

        # Test 2: Valid edge case (min)
        control_day("001")
        print("Test 2: Valid day '001' → ✅ OK")
        tests_passed += 1

        # Test 3: Valid edge case (max)
        control_day("366")
        print("Test 3: Valid day '366' → ✅ OK")
        tests_passed += 1

        # Test 4: Invalid - None
        try:
            control_day(None)
            print("Test 4: None input → ❌ FAILED (no error raised)")
        except ValueError as e:
            print(f"Test 4: None input → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 5: Invalid - wrong length
        try:
            control_day("65")
            print("Test 5: Wrong length '65' → ❌ FAILED (no error)")
        except ValueError as e:
            print(f"Test 5: Wrong length '65' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 6: Invalid - out of range
        try:
            control_day("367")
            print("Test 6: Out of range '367' → ❌ FAILED (no error)")
        except ValueError as e:
            print(f"Test 6: Out of range '367' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        print("\n" + f" TESTS SUMMARY: {tests_passed}/{total_tests} PASSED ".center(80, "="))
        if tests_passed == total_tests:
            print("   🎉 ALL TESTS PASSED SUCCESSFULLY 🎉")
        else:
            print("   ❌ Some tests failed - review above")

    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
