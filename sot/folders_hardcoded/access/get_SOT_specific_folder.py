# =============================================================================
# FILE PATH: legion_goes/sot/folders_hardcoded/access/get_SOT_specific_folder.py
# Version: 1.1.2 (Dynamic Absolute Path Resolver)
# =============================================================================
import os
import sys
from pathlib import Path

# --- LEGION IMPORTS ---
from legion_goes.sot.folders_hardcoded.access.get_SOT_LEGION_Work_Directory import get_SOT_LEGION_Work_Directory
from legion_goes.sot.folders_hardcoded.access.get_full_SOT_folder_structure import get_full_SOT_folder_structure

def get_SOT_specific_folder(key: str, subkey: str = None) -> str:
    """
    Returns the absolute path for a specific folder, dynamically anchored 
    to the current LEGION Work Directory (usually the CWD).
    
    Examples:
        If CWD is '/home/user/the_factory':
        get_SOT_specific_folder("data_raw") -> /home/user/the_factory/data_raw
    """
    ctx = sys._getframe().f_code.co_name

    # 1. Validation: Key must exist
    if key is None:
        raise ValueError(f"\n❌ [🛡️ GUARD ERROR - {ctx}()]: Argument 'key' is None.")

    # 2. Get the Work Directory (the dynamic anchor)
    # This usually returns os.getcwd(), so it follows you to 'the_factory'
    base_root = Path(get_SOT_LEGION_Work_Directory())

    # 3. Get the relative structure from SOT
    folders = get_full_SOT_folder_structure()

    if key not in folders:
        valid_keys = ", ".join(folders.keys())
        raise KeyError(f"\n❌ [🛡️ GUARD ERROR - {ctx}()]: Key '{key}' not found. Available: {valid_keys}")

    # 4. Extract relative name/path from SOT definitions
    if subkey is not None:
        if subkey not in folders[key]:
            valid_subkeys = ", ".join(folders[key].keys())
            raise KeyError(f"\n❌ [🛡️ GUARD ERROR - {ctx}()]: Subkey '{subkey}' not found for '{key}'.")
        relative_path = folders[key][subkey]
    else:
        relative_path = folders[key]

    # ✨ THE FIX: We join the dynamic base_root with the relative SOT path.
    # We use .resolve() to clean up any redundant separators.
    final_abs_path = (base_root / relative_path).resolve()

    return str(final_abs_path)

# ===================================================================
# MAIN EXECUTION (Diagnostic Test)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: DYNAMIC PATH RESOLVER TEST ".center(80, "="))
    
    # Simulating execution context
    print(f"Current Base Anchor: {get_SOT_LEGION_Work_Directory()}")
    
    try:
        raw_path = get_SOT_specific_folder("data_raw")
        proc_path = get_SOT_specific_folder("data_proc", "sp01_single")
        
        print(f"\n✅ Resolved Paths:")
        print(f" > data_raw: {raw_path}")
        print(f" > data_proc: {proc_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 80 + "\n")
