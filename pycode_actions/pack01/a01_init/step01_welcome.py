# =============================================================================
# FILE PATH: legion_goes/tasks/task01_init/actions/action01_welcome.py
# Version: 1.9.1 (Bugfix: Timezone Import & Precise Dashboard)
# =============================================================================

import os
import sys
import psutil
import shutil
import platform
from datetime import datetime, timezone  


#from legion_goes.sot.folders_hardcoded.access.get_SOT_LEGION_Work_Directory import get_SOT_LEGION_Work_Directory
#LEGION_CURRENT_WORK_DIR = get_SOT_LEGION_Work_Directory()
LEGION_CURRENT_WORK_DIR = os.getcwd()

# --- ANSI COLOR PALETTE ---
C_LGN   = "\033[96m"  # Cyan (LEGION)
C_GOS   = "\033[92m"  # Green (GOES)
C_WHT   = "\033[97m"  # White (Bridge)
C_RST   = "\033[0m"   # Reset
C_BLD   = "\033[1m"   # Bold

# =============================================================================
# LEGION VISUAL ASSETS
# =============================================================================

BANNER_01 = r"""
      _      ______ _____ _____ ____  _   _ 
     | |    |  ____/ ____|_   _/ __ \| \ | |
     | |    | |__ | |  __  | || |  | |  \| |
     | |    |  __|| | |_ | | || |  | | . ` |
     | |____| |___| |__| |_| || |__| | |\  |
     |______|______\_____|_____\____/|_| \_|
"""

BANNER_02 = r"""
  _      ______ _____ _____ ____  _   _               _____  ____  ______  _____ 
 | |    |  ____/ ____|_   _/ __ \| \ | |             / ____|/ __ \|  ____|/ ____|
 | |    | |__ | |  __  | || |  | |  \| |  _______   | |  __| |  | | |__  | (___  
 | |    |  __|| | |_ | | || |  | | . ` | |_______|  | | |_ | |  | |  __|  \___ \ 
 | |____| |___| |__| |_| || |__| | |\  |            | |__| | |__| | |____ ____) |
 |______|______\_____|_____\____/|_| \_|             \_____|\____/|______|_____/ 
"""

# =============================================================================
# COLOR ENGINE
# =============================================================================

def get_colored_output(text: str, is_alt: bool = False) -> str:
    if not text: return ""
    lines = text.splitlines()
    colored_lines = []
    split_point = 46 

    for line in lines:
        if not line.strip():
            colored_lines.append("")
            continue
        left = line[:split_point]
        right = line[split_point:]
        if "_______" in right:
            bridge_split = right.split("_______")
            final_line = f"{C_LGN}{left}{C_GOS}{bridge_split[0]}{C_WHT}_______"
            final_line += f"{C_GOS}{bridge_split[1]}{C_RST}"
        else:
            final_line = f"{C_LGN}{left}{C_GOS}{right}{C_RST}"
        colored_lines.append(final_line)
    return "\n".join(colored_lines)

# =============================================================================
# CORE ORCHESTRATOR
# =============================================================================

def show_welcome_banner(use_alt: bool = False):
    """Displays the colored welcome banner and detailed system diagnostics."""
    # 1. Tiempos
    now_local = datetime.now()
    now_utc = datetime.now(timezone.utc)
    
    # 2. RAM (Free of Total | % Free)
    ram = psutil.virtual_memory()
    ram_total_gb = ram.total / (1024**3)
    ram_avail_gb = ram.available / (1024**3)
    ram_free_pct = (ram.available / ram.total) * 100
    
    # 3. DISCO (Free of Total | % Free)
    total, used, free = shutil.disk_usage(LEGION_CURRENT_WORK_DIR)
    disk_total_gb = total / (1024**3)
    disk_free_gb = free / (1024**3)
    disk_free_pct = (free / total) * 100

    raw_art = BANNER_01 if use_alt else BANNER_02
    
    print("\n" + "="*95)
    print(get_colored_output(raw_art, is_alt=use_alt))
    print("="*95)
    
    # --- DASHBOARD TÉCNICO ---
    print(f"  {C_BLD}SYSTEM DATE:{C_RST}           {now_local.strftime('%Y-%m-%d %H:%M:%S')} (Local)")
    print(f"  {C_BLD}UTC SYSTEM DATE:{C_RST}       {now_utc.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    print(f"  {C_BLD}OPERATING SYSTEM:{C_RST}      {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"  {C_BLD}WORKSPACE:{C_RST}             {LEGION_CURRENT_WORK_DIR }")
    
    # RAM: 10.00 GB of 32.00 GB (31.2% free)
    print(f"  {C_BLD}SYSTEM RAM:{C_RST}            {ram_avail_gb:.2f} GB of {ram_total_gb:.2f} GB ({ram_free_pct:.1f}% free)")
    
    # STORAGE: 100.00 GB of 1000.00 GB (10.0% free)
    print(f"  {C_BLD}SYSTEM STORAGE:{C_RST}        {disk_free_gb:.2f} GB of {disk_total_gb:.2f} GB ({disk_free_pct:.1f}% free)")
    
    print("="*95 + "\n")


def run_action():
    show_welcome_banner()
    
    
    
if __name__ == "__main__":
    run_action()
