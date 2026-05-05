# =============================================================================
# FILE PATH: legion_goes/sot/folders_hardcoded/core/goes_hardcoded_folders.py
# Version: 1.0.1 (Immutable Default Folder Structure)
# =============================================================================
import os
from types import MappingProxyType

# -------------------------------------------------------------------
# PRIVATE DEFAULT FOLDERS (internal only)
# -------------------------------------------------------------------
_PRIVATE_DEFAULT_FOLDERS = {
    "data_plan": "data_plan",           # JSON plan files
    "data_raw": "data_raw",             # Raw .nc files
    "data_proc": {
        "sp01_single": "data_proc/sp01_single",
    },
    "logs": "logs",
    "config": "config",
    "output": "output",
    "tests": "tests",
}

# -------------------------------------------------------------------
# IMMUTABILITY ENGINE (same as your stones)
# -------------------------------------------------------------------
def _make_deep_immutable(obj):
    if isinstance(obj, dict):
        return MappingProxyType({k: _make_deep_immutable(v) for k, v in obj.items()})
    elif isinstance(obj, (list, tuple)):
        return tuple(_make_deep_immutable(i) for i in obj)
    return obj

# -------------------------------------------------------------------
# IMMUTABLE PUBLIC OBJECT (incorruptible)
# -------------------------------------------------------------------
DEFAULT_FOLDERS = _make_deep_immutable(_PRIVATE_DEFAULT_FOLDERS)

# Optional: runtime immutability check (debug only)
if __debug__:
    try:
        DEFAULT_FOLDERS["data_proc"]["sp01_single"] = "hacked"
    except TypeError:
        pass
    else:
        raise RuntimeError("Immutability check failed: DEFAULT_FOLDERS is mutable!")

# -------------------------------------------------------------------
# UNIT TESTING (Main Execution)
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + " LEGION GOES: DEFAULT FOLDERS INTEGRITY TEST ".center(80, "="))
    print("Testing immutability and structure of DEFAULT_FOLDERS...\n")

    tests_passed = 0
    total_tests = 4

    try:
        # Test 1: Check if DEFAULT_FOLDERS is immutable proxy (root level)
        assert isinstance(DEFAULT_FOLDERS, MappingProxyType), "DEFAULT_FOLDERS must be MappingProxyType"
        print("Test 1: DEFAULT_FOLDERS is immutable proxy → ✅ OK")
        tests_passed += 1

        # Test 2: Check nested structure immutability
        assert isinstance(DEFAULT_FOLDERS["data_proc"], MappingProxyType), "Nested 'data_proc' must be MappingProxyType"
        print("Test 2: Nested 'data_proc' is immutable → ✅ OK")
        tests_passed += 1

        # Test 3: Check number of top-level keys
        expected_keys = 7
        assert len(DEFAULT_FOLDERS) == expected_keys, f"Expected {expected_keys} top-level folders, got {len(DEFAULT_FOLDERS)}"
        print(f"Test 3: {len(DEFAULT_FOLDERS)} top-level folders found → ✅ OK")
        tests_passed += 1

        # Test 4: Runtime immutability check (attempt to modify nested)
        try:
            DEFAULT_FOLDERS["data_proc"]["sp01_single"] = "hacked"
            print("Test 4: Nested modification attempt → ❌ FAILED (no error)")
        except TypeError:
            print("Test 4: Nested modification blocked → ✅ OK")
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
