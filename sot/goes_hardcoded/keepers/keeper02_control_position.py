# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/keepers/keeper02_control_position.py
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
    # Dynamic file name for accurate error reporting
   
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
    from legion_goes.sot.goes_hardcoded.core.goes_info_sat import AVAILABLE_GOES_POSITIONS
except ImportError as e:
    
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SOT - {current_file}]")
    print("="*80)
    print(f" Failed to load project module: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print(" Check if 'goes_info_sat.py' exists in goes_hardcoded/core/ and is importable.")
    print(" Ensure the package structure and __init__.py files are correct.")
    print("="*80 + "\n")
    raise SystemExit(1)
    
# ===================================================================
# CONTROL FUNCTIONS (The Guards)
# ===================================================================
def control_position(position):
    """
    GUARD: Validates 'position' against the Source of Truth (SoT).
    Extremely strict validation for the Legion GOES system.
   
    Accepts **only** exactly 'east' or 'west' (lowercase, no spaces, exactly 4 characters).
    Any deviation raises an immediate and explicit error.
    """
    ctx = sys._getframe().f_code.co_name
    if position is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is None. A valid position is required.")
  
    if not isinstance(position, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' ({type(position).__name__}). Expected type: str.")
  
    if " " in position:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' and contains spaces. Provide a clean string (exactly 'east' or 'west').")
  
    if position != position.lower():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' and contains uppercase letters. Only lowercase is allowed (exactly 'east' or 'west').")
  
    if len(position) != 4:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' and does not have exactly 4 characters (must be exactly 'east' or 'west').")
  
    if position not in AVAILABLE_GOES_POSITIONS:
        valid_options = ", ".join(AVAILABLE_GOES_POSITIONS)
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' '{position}' is not found in the Source of Truth.\n💡 Available positions: {valid_options}")

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: CONTROL_POSITION GUARD TEST ".center(80, "="))
    print("Testing control_position() with strict validation...\n")

    tests_passed = 0
    total_tests = 5

    try:
        # Test 1: Valid position
        control_position("east")
        print("Test 1: Valid position 'east' → ✅ OK")
        tests_passed += 1

        # Test 2: Valid alternative
        control_position("west")
        print("Test 2: Valid position 'west' → ✅ OK")
        tests_passed += 1

        # Test 3: Invalid - None
        try:
            control_position(None)
            print("Test 3: None input → ❌ FAILED (no error raised)")
        except ValueError as e:
            print(f"Test 3: None input → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 4: Invalid - uppercase
        try:
            control_position("East")
            print("Test 4: Uppercase 'East' → ❌ FAILED (no error)")
        except ValueError as e:
            print(f"Test 4: Uppercase 'East' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 5: Invalid - wrong value
        try:
            control_position("north")
            print("Test 5: Invalid 'north' → ❌ FAILED (no error)")
        except ValueError as e:
            print(f"Test 5: Invalid 'north' → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        print("\n" + f" TESTS SUMMARY: {tests_passed}/{total_tests} PASSED ".center(80, "="))
        if tests_passed == total_tests:
            print("   🎉 ALL TESTS PASSED SUCCESSFULLY 🎉")
        else:
            print("   ❌ Some tests failed - review above")

    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
