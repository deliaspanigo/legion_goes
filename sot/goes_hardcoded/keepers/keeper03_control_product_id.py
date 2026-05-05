# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/keepers/keeper03_control_product_id.py
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

# -------------------------------------------------------------------
# TRY 02: Project-specific libraries / modules
# -------------------------------------------------------------------
try:
    from legion_goes.sot.goes_hardcoded.core.goes_info_product import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SOT - {current_file}]")
    print("="*80)
    print(f" Failed to load project modules: {e}")
    print(" Please verify that your virtual environment (venv) is active and paths are correct.")
    print(" Check if 'goes_info_product.py' exists in goes_hardcoded/core/.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# CONTROL FUNCTIONS (The Guards)
# ===================================================================
def control_product_id(product_id: str):
    """
    GUARD: Validates the product_id against the SoT.
    Does NOT return anything. Raises an error if validation fails.
    """
    ctx = sys._getframe().f_code.co_name

    if product_id is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'product_id' is None. A valid product_id is required.")

    if not isinstance(product_id, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'product_id' must be a string, not {type(product_id).__name__}.")

    if " " in product_id:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'product_id' '{product_id}' contains spaces. Provide a clean string.")

    if product_id not in AVAILABLE_GOES_PRODUCTS:
        options = ", ".join(AVAILABLE_GOES_PRODUCTS)
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Product '{product_id}' not registered.\nAllowed IDs: {options}")

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " ADUANA CONTROL GOES: PRODUCT ID GUARD TEST ".center(80, "="))
    print("Testing control_product_id()...\n")

    tests_passed = 0
    total_tests = 5

    try:
        print("Test 1: Valid product ID")
        control_product_id("ABI-L2-LSTF")
        print("   ✅ OK: Valid ID passed")
        tests_passed += 1

        print("\nTest 2: None input")
        try:
            control_product_id(None)
            print("   ❌ FAILED: should have raised error")
        except ValueError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        print("\nTest 3: Invalid type (int)")
        try:
            control_product_id(123)
            print("   ❌ FAILED: should have raised error")
        except TypeError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        print("\nTest 4: With spaces")
        try:
            control_product_id("ABI-L2-LSTF ")
            print("   ❌ FAILED: should have raised error")
        except ValueError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        print("\nTest 5: Invalid product (not registered)")
        try:
            control_product_id("INVALID-PROD")
            print("   ❌ FAILED: should have raised error")
        except ValueError as e:
            print(f"   ✅ OK: Caught expected error:\n      {e}")
            tests_passed += 1

        print("\n" + f" TESTS SUMMARY: {tests_passed}/{total_tests} PASSED ".center(80, "="))
        if tests_passed == total_tests:
            print("   🎉 ALL TESTS PASSED SUCCESSFULLY 🎉")
        else:
            print("   ❌ Some tests failed - review above")

    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
