#!/bin/bash

# ==============================================================================
# LEGION GOES - LOCAL RUNNER (Ejecutar desde the_factory)
# ==============================================================================
# bash ./zzz_run_pack01.sh
# ==============================================================================
# 1. Configuración de la tarea
export YEAR="2026"
export DAY="003"
export HOUR="ALL"
export POS="EAST"

# 2. Definir rutas relativas
# Como estamos en 'the_factory', la raíz está un nivel arriba
ROOT_DIR=".."

# 3. Activar el entorno virtual (subiendo un nivel)
if [ -f "$ROOT_DIR/venv/bin/activate" ]; then
    source "$ROOT_DIR/venv/bin/activate"
    echo "🐍 venv activo"
else
    echo "❌ Error: No se encontró el venv en $ROOT_DIR/venv"
    exit 1
fi

# 4. Configurar el PYTHONPATH para que Python encuentre 'legion_goes'
export PYTHONPATH="$ROOT_DIR"

echo "------------------------------------------------------------------"
echo "🏭 TRABAJANDO EN: $(pwd)"
echo "🚀 PROCESANDO: $YEAR-$DAY ($HOUR)"
echo "------------------------------------------------------------------"

# 5. Ejecutar los módulos
echo "📡 Paso 1: Descarga"
python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_01_download

echo ""
echo "⚙️ Paso 2: Procesamiento"
python3 -m legion_goes.pycode_actions.pack01.zzz_run_pack01_02_processing

echo "------------------------------------------------------------------"
echo "✅ Finalizado"
