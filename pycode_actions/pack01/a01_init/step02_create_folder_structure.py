# =============================================================================
# FILE PATH: legion_goes/tasks/task01_init/actions/action02_create_folder_structure.py
# Version: 1.0.0 (Folder Management Action)
# =============================================================================

import os
from legion_goes.sot.folders_hardcoded.access.create_SOT_folder_structure import create_SOT_folder_structure



def run_action(verbose: bool = True):
    """Verifica y crea la estructura de directorios necesaria."""
    
    create_SOT_folder_structure(verbose = verbose)
    
    print(f"[SUCCESS] LEGION-GOES Environment ready for processing.\n")



if __name__ == "__main__":
    run_action()
