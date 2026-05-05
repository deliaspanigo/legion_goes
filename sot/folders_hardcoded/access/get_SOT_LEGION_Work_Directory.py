# =============================================================================
# FILE PATH: legion_goes/sot/folders_hardcoded/access/get_SOT_LEGION_Work_Directory.py
# Version: 1.0.3 (Get Current Work Directory - Configurable)
# =============================================================================
import os

def get_SOT_LEGION_Work_Directory() -> str:
    """
    Returns the absolute path of the current working directory (LEGION work directory).
    
    This is the base path where the script/notebook is being executed.
    
    Returns:
        str: Absolute path to the current working directory.
    
    Raises:
        RuntimeError: If the directory does not exist or is not accessible (very rare for cwd).
    """
    work_dir = os.getcwd()
    
    # Optional safety check (rarely needed for cwd, but good practice)
    if not os.path.exists(work_dir):
        raise RuntimeError(f"Current working directory '{work_dir}' does not exist.")
    if not os.access(work_dir, os.W_OK):
        raise PermissionError(f"No write permission in current working directory '{work_dir}'.")
    
    return work_dir

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: WORK DIRECTORY TEST ".center(80, "="))
    print("Testing get_SOT_LEGION_Work_Directory()...\n")

    try:
        # Test 1: Get current directory
        work_dir = get_SOT_LEGION_Work_Directory()
        print(f"Test 1: Current work directory → ✅ OK")
        print(f"   Path: {work_dir}")

        # Test 2: Check if path exists and is writable
        assert os.path.exists(work_dir), f"Path '{work_dir}' does not exist"
        assert os.access(work_dir, os.W_OK), f"No write permission in '{work_dir}'"
        print("Test 2: Path exists and is writable → ✅ OK")

        print("\n 🎉 ALL TESTS PASSED SUCCESSFULLY 🎉")

    except AssertionError as ae:
        print(f"\n❌ [ASSERTION FAILED]: {ae}")
    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
