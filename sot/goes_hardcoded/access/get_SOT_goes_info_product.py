# =============================================================================
# FILE PATH: legion_goes/sot/goes_hardcoded/access/get_SOT_goes_info_product.py
# Version: 1.1.2 (Atomic Object-Driven SoT - Access Layer)
# =============================================================================

# -------------------------------------------------------------------
# IMPORTS NECESARIOS
# -------------------------------------------------------------------
import sys
import os
from types import MappingProxyType

try:
    from legion_goes.sot.goes_hardcoded.core.goes_info_product import (
        SAVED_INFO_PROD_GOES,
        AVAILABLE_GOES_PRODUCTS
    )
    from legion_goes.sot.goes_hardcoded.keepers.keeper03_control_product_id import control_product_id
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
    print(" Check if 'goes_info_product.py' exists in goes_hardcoded/core/.")
    print(" And 'keeper01_control_sat_id.py' in keepers/.")
    print(" Ensure the package structure and __init__.py files are correct.")
    print("="*80 + "\n")
    raise SystemExit(1)

def get_SOT_goes_info_product(product_id: str = None) -> MappingProxyType:
    """
    Returns specific product metadata or the full catalog from the Source of Truth (SoT).
    Extremely strict access with validation.
    """
    if product_id is None:
        return SAVED_INFO_PROD_GOES
    try:
        control_product_id(product_id)
        return SAVED_INFO_PROD_GOES[product_id]
    except Exception as e:
        ctx = sys._getframe().f_code.co_name
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Failed to resolve product '{product_id}'. Details: {e}"
        raise type(e)(error_msg) from None

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GET_SOT_GOES_INFO_PRODUCT TEST ".center(80, "="))
    print("Testing get_SOT_goes_info_product() with strict validation...\n")

    tests_passed = 0
    total_tests = 5

    try:
        # Test 1: Full catalog retrieval (no product_id)
        catalog = get_SOT_goes_info_product()
        assert isinstance(catalog, MappingProxyType), "Catalog must be MappingProxyType"
        assert len(catalog) == 4, f"Expected 4 products, got {len(catalog)}"
        print("Test 1: Full catalog retrieval → ✅ OK (4 products, immutable)")
        tests_passed += 1

        # Test 2: Specific product metadata (valid)
        lstf_info = get_SOT_goes_info_product("ABI-L2-LSTF")
        assert lstf_info["type"] == "raster", "ABI-L2-LSTF type mismatch"
        assert lstf_info["cadence_full_disk"] == "1 hour", "ABI-L2-LSTF cadence mismatch"
        print("Test 2: Specific product 'ABI-L2-LSTF' → ✅ OK")
        tests_passed += 1

        # Test 3: Vectorial product check (valid)
        glm_info = get_SOT_goes_info_product("GLM-L2-LCFA")
        assert glm_info["type"] == "vectorial", "GLM-L2-LCFA type mismatch"
        assert glm_info["total_files_one_day"] == 4320, "GLM-L2-LCFA files per day mismatch"
        print("Test 3: Vectorial product 'GLM-L2-LCFA' → ✅ OK")
        tests_passed += 1

        # Test 4: Invalid product ID (should raise)
        try:
            get_SOT_goes_info_product("INVALID-PROD")
            print("Test 4: Invalid product ID → ❌ FAILED (no error)")
        except Exception as e:
            print(f"Test 4: Invalid product ID → ✅ OK (caught expected error): {e}")
            tests_passed += 1

        # Test 5: Invalid type input (should raise)
        try:
            get_SOT_goes_info_product(123)
            print("Test 5: Invalid type (int) → ❌ FAILED (no error)")
        except TypeError as e:
            print(f"Test 5: Invalid type → ✅ OK (caught expected error): {e}")
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
