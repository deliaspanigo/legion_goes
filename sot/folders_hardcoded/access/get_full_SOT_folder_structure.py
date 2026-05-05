# =============================================================================
# FILE PATH: legion_goes/sot/folders_hardcoded/access/get_SOT_folder_structure.py
# Version: 1.0.1 (Immutable Default Folder Structure)
# =============================================================================
from legion_goes.sot.folders_hardcoded.core.goes_hardcoded_folders import DEFAULT_FOLDERS

def get_full_SOT_folder_structure():
    """
    Returns the complete immutable dictionary of default folder structure.
   
    Returns:
        MappingProxyType: The full DEFAULT_FOLDERS (read-only, cannot be modified)
    """
    return DEFAULT_FOLDERS

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: FULL FOLDER STRUCTURE ACCESS TEST ".center(80, "="))
    print("Testing get_full_SOT_folder_structure()...\n")

    tests_passed = 0
    total_tests = 5

    try:
        # Test 1: Retrieve full structure
        full_structure = get_full_SOT_folder_structure()
        assert isinstance(full_structure, MappingProxyType), "Full structure must be MappingProxyType"
        print("Test 1: Full structure retrieved as immutable proxy → ✅ OK")
        tests_passed += 1

        # Test 2: Check top-level keys count
        expected_keys = 7
        assert len(full_structure) == expected_keys, f"Expected {expected_keys} top-level folders, got {len(full_structure)}"
        print(f"Test 2: {len(full_structure)} top-level folders found → ✅ OK")
        tests_passed += 1

        # Test 3: Check nested structure access
        assert "sp01_single" in full_structure["data_proc"], "Nested 'sp01_single' not found"
        print("Test 3: Nested structure access → ✅ OK")
        tests_passed += 1

        # Test 4: Attempt root modification (should fail)
        try:
            full_structure["data_raw"] = "hacked"
            print("Test 4: Root modification attempt → ❌ FAILED (no error)")
        except TypeError:
            print("Test 4: Root modification blocked → ✅ OK")
            tests_passed += 1

        # Test 5: Attempt nested modification (should fail)
        try:
            full_structure["data_proc"]["sp01_single"] = "hacked"
            print("Test 5: Nested modification attempt → ❌ FAILED (no error)")
        except TypeError:
            print("Test 5: Nested modification blocked → ✅ OK")
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
