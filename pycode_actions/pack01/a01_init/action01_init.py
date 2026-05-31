# legion_goes/pycode_actions/pack01/a01_init/action01_init.py
# ===================================================================
#  python3 -m legion_goes.pycode_actions.pack01.a01_init.action01_init
# ===================================================================


import os  # <-- No te olvides de importar os, que lo usas en el print final
from .step01_welcome import run_action as action01_welcome
from .step02_create_folder_structure import run_action as action02_create_folder_structure

def run_action01_init(verbose: bool = True):
    """
    Runs the full project initialization:
    - Muestra bienvenida
    - Creates/verifies default folders
    """
    action01_welcome()
    action02_create_folder_structure(verbose=verbose)  # Passes verbose to the folder action
    if verbose:
        print("\nInitialization complete. Project ready to use!")

# ===================================================================
# MAIN EXECUTION (Entry point)
# ===================================================================


if __name__ == "__main__":
    print("\n" + "=== LEGION GOES - TASK 01: PROJECT INITIALIZATION ===".center(80, "="))
    print("Running full project initialization...\n")
    
    try:
        # Runs the initialization function
        run_action01_init(verbose=True)  #  Pass verbose=True here
        
        print("\n" + "=== INICIALIZACION FINALIZADA EXITOSAMENTE ===".center(80, "="))
        print("Puedes continuar trabajando en notebooks o scripts.")
        print("Carpeta actual: " + os.getcwd())
    
    except Exception as e:
        print("\n" + "=== ERROR DURANTE LA INICIALIZACION ===".center(80, "="))
        print(f"Detalles: {e}")
        print("Revisa los logs o la consola para mas informacion.")
        raise  # Keep the full traceback visible if there is an error
    
    print("=" * 80 + "\n")
