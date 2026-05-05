# =============================================================================
# FILE PATH: legion_goes/sot/folders_hardcoded/access/create_SOT_folder_structure.py
# Version: 1.0.7 (Path-Integrity & Environment-Agnostic)
# Description: Handles automated creation and verification of the GOES folder 
#              structure based on the SOT immutable definitions.
# =============================================================================
import os
from pathlib import Path
from types import MappingProxyType

# --- LEGION SOT IMPORTS ---
from legion_goes.sot.folders_hardcoded.access.get_SOT_LEGION_Work_Directory import get_SOT_LEGION_Work_Directory
from legion_goes.sot.folders_hardcoded.access.get_full_SOT_folder_structure import get_full_SOT_folder_structure

def create_SOT_folder_structure(
    verbose: bool = True
) -> dict:
    """
    Creates the default folder structure under the current working directory or 
    the directory defined by the SOT Work Directory getter.

    - Prevents absolute path collisions by using Pathlib joins.
    - Ensures all parent directories are created (mkdir -p).
    - Returns a dictionary mapping keys to verified absolute path strings.
    """
    # 1. Resolve Base Directory
    base_dir = Path(get_SOT_LEGION_Work_Directory())
    
    # 2. Retrieve Immutable Folder Definitions
    dict_folders = get_full_SOT_folder_structure()

    # Safety Check: Ensure base exists or create it
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)

    created_paths = {}

    def ensure_folder(folder_rel_path: str) -> Path:
        """
        Safely joins relative path to base and creates the directory.
        Returns the resolved Path object.
        """
        # We use the / operator to intelligently join paths.
        # If folder_rel_path is 'data_raw', it stays relative to base_dir.
        full_path = base_dir / folder_rel_path
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    # 3. Process Structure (Top-level and Nested)
    for key, value in dict_folders.items():
        if isinstance(value, str):
            # Standard folder
            f_path = ensure_folder(value)
            created_paths[key] = str(f_path.resolve())
            if verbose: 
                print(f"Verified Path [{key}]: {f_path}")
            
        elif isinstance(value, (dict, MappingProxyType)):  
            # Nested dictionary structure
            for subkey, subvalue in value.items():
                f_path = ensure_folder(subvalue)
                composite_key = f"{key}/{subkey}"
                created_paths[composite_key] = str(f_path.resolve())
                if verbose: 
                    print(f"Verified Path [{composite_key}]: {f_path}")

    return created_paths

# ===================================================================
# UNIT TESTING (Path Integrity & Validation)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: SOT FOLDER STRUCTURE INTEGRITY TEST ".center(80, "="))
    
    # We test relative to the Current Working Directory to ensure no hardcoded leaks
    current_cwd = os.getcwd()
    print(f"Current Execution Context (CWD): {current_cwd}\n")
    
    try:
        # Run creation logic
        results = create_SOT_folder_structure(verbose=True)
        
        print("\n" + " PATH ANALYSIS ".center(40, "-"))
        
        # Validation Logic: Ensure paths do not contain redundant system roots
        # (e.g., prevent /home/legion/the_factory/home/legion/data_raw)
        integrity_errors = []
        for key, path_str in results.items():
            # Check for "Path Nesting" (common error when joining two absolute paths)
            # We count how many times the user root appears in the string.
            if path_str.count("/home/") > 1:
                integrity_errors.append(f"Redundant root detected in {key}: {path_str}")
        
        if not integrity_errors:
            print("✅ [SUCCESS]: All paths are correctly resolved and non-redundant.")
        else:
            print("❌ [FAILURE]: Path resolution leaks detected:")
            for error in integrity_errors:
                print(f"   ! {error}")

    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Test failed: {e}")
        
    print("\n" + "=" * 80 + "\n")
