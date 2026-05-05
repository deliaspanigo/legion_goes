# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/keepers/keeper04_control_year.py
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
def control_year(year):
    """
    GUARD: Validates 'year' against strict format requirements for the Legion GOES system.
    Extremely strict validation.
    
    Accepts **only** exactly 4-digit strings like '2026' (no spaces, only digits).
    Any deviation raises an immediate and explicit error.
    """
    ctx = sys._getframe().f_code.co_name

    if year is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' is None. A valid year is required.")
    
    if not isinstance(year, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' is '{year}' ({type(year).__name__}). Expected type: str.")
    
    if " " in year:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' '{year}' contains spaces. Provide a clean 4-digit string (exactly 'YYYY').")
    
    if len(year) != 4:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' '{year}' does not have exactly 4 characters. Expected format: 'YYYY' (e.g., '2026').")
    
    if not year.isdigit():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' '{year}' contains non-digit characters. Expected exactly 4 digits (e.g., '2026').")




# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " ADUANA CONTROL GOES: YEAR GUARD TEST ".center(80, "="))
    print(f"File Context: {current_file}")
    print("Testing control_year()...\n")

    tests_passed = 0
    total_tests = 6

    try:
        # Test 1: Valid year string
        print("Test 1: Valid year string ('2026')")
        control_year("2026")
        print("   ✅ OK: Valid year passed")
        tests_passed += 1

        # Test 2: None input
        print("\nTest 2: None input")
        try:
            control_year(None)
            print("   ❌ FAILED: Should have raised ValueError")
        except ValueError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        # Test 3: Invalid type (int) - We are strict on 'str' only
        print("\nTest 3: Invalid type (int 2026)")
        try:
            control_year(2026)
            print("   ❌ FAILED: Should have raised TypeError")
        except TypeError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        # Test 4: Year with spaces
        print("\nTest 4: Year with spaces (' 2026')")
        try:
            control_year(" 2026")
            print("   ❌ FAILED: Should have raised ValueError")
        except ValueError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        # Test 5: Wrong length (3 digits)
        print("\nTest 5: Wrong length ('202')")
        try:
            control_year("202")
            print("   ❌ FAILED: Should have raised ValueError")
        except ValueError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        # Test 6: Non-digit characters
        print("\nTest 6: Non-digit characters ('202A')")
        try:
            control_year("202A")
            print("   ❌ FAILED: Should have raised ValueError")
        except ValueError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        # --- FINAL SUMMARY ---
        print("\n" + f" TESTS SUMMARY: {tests_passed}/{total_tests} PASSED ".center(80, "="))
        if tests_passed == total_tests:
            print("   🎉 ALL YEAR GUARDS PASSED SUCCESSFULLY 🎉")
        else:
            print("   ❌ Some tests failed - Review logical consistency")

    except Exception as e:
        print(f"\n❌ [UNEXPECTED SYSTEM FAILURE]: {e}")

    print("=" * 80 + "\n")
