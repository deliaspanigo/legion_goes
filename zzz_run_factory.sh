#!/bin/bash

# ==============================================================================
# LEGION GOES - RUN FACTORY v0.0.1
# ==============================================================================
# bash legion_goes/zzz_run_factory.sh
# ==============================================================================

# 1. Configuración de la tarea
export YEAR="2026"
export DAY="003"
export HOUR="ALL"
export POS="WEST"

# 2. Obtener la ruta raíz (un nivel arriba de donde está este script)
# Esto hace que el script funcione sin importar desde dónde lo llames.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")

# 3. Preparar el entorno de trabajo
# Creamos the_factory al mismo nivel que legion_goes
mkdir -p "$ROOT_DIR/the_factory"
cd "$ROOT_DIR/the_factory"

echo "------------------------------------------------------------------"
echo "🚀 Ejecutando desde: $ROOT_DIR"
echo "📂 Carpeta de trabajo: $(pwd)"
echo "------------------------------------------------------------------"

# 4. Ejecutar con el PYTHONPATH apuntando a la raíz del proyecto
# Esto le dice a Python: "Busca los módulos en la carpeta superior"
export PYTHONPATH="$ROOT_DIR"

echo "📡 PASO 1: DESCARGA"
python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_01_download

echo ""
echo "⚙️ PASO 2: PROCESAMIENTO"
python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_02_processing

echo "------------------------------------------------------------------"
echo "✅ PROCESO FINALIZADO"
