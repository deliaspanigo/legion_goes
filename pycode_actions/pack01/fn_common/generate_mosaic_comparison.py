# legion_goes/pycode_actions/pack01/fn_common/generate_mosaic_png.py
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.fn_common.generate_mosaic_png
# ==================================================================================

import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

def generate_mosaic_comparison(dict_paths):
    """
    Genera un mosaico vertical de los PNGs en el diccionario.
    El nombre del archivo está hardcodeado: 'MOSAIC_comparison.png'
    Se guarda en la misma carpeta que el primer PNG del diccionario.
    """
    # 1. Nombre hardcodeado del producto final
    MOSAIC_NAME = "MOSAIC_comparison.png"

    # 2. Extraer paths que son PNG y existen físicamente
    png_files = []
    for val in dict_paths.values():
        p = Path(val)
        if p.suffix.lower() == '.png' and p.exists():
            # Evitar que el propio mosaico se incluya si se re-ejecuta el script
            if p.name != MOSAIC_NAME:
                png_files.append(p)
    
    if not png_files:
        print("⚠️ No se encontraron archivos PNG válidos para el mosaico.")
        return

    # 3. Definir ruta de salida (Carpeta del primer PNG + nombre hardcodeado)
    output_dir = png_files[0].parent
    output_path = output_dir / MOSAIC_NAME

    # 4. Verificación de existencia (No generar si ya existe)
    if output_path.exists():
        print(f"  [SKIPPED] El mosaico ya existe: {output_path.name}")
        return

    print(f"  [GENERATING] Creando mosaico en: {output_dir}")

    # 5. Configurar la figura (n filas, 1 columna)
    n_images = len(png_files)
    # 15 de ancho y 8 de alto por cada imagen encontrada
    fig, axes = plt.subplots(n_images, 1, figsize=(15, 8 * n_images))
    
    # Manejo de caso con una sola imagen
    if n_images == 1:
        axes = [axes]

    # 6. Loop de ploteo
    for ax, img_path in zip(axes, png_files):
        try:
            img = Image.open(img_path)
            ax.imshow(img)
            # Título con el nombre del archivo original
            ax.set_title(f"FILE: {img_path.name}", fontsize=14, fontweight='bold', pad=15)
            ax.axis('off')
        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {img_path.name}\n{e}", ha='center', va='center')
            ax.axis('off')

    # 7. Guardado final y liberación de memoria
    plt.tight_layout()
    try:
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"  ✅ Mosaico guardado con éxito: {output_path.name}")
    except Exception as e:
        print(f"  ❌ Error al guardar el mosaico: {e}")
    finally:
        plt.close(fig) # Vital para no agotar la RAM en procesos masivos

# --- Ejemplo de ejecución ---
if __name__ == "__main__":
    # La función detectará que debe guardar en 'data_proc/sp01/test/'
    mis_outputs = {
        "img_native": "data_proc/sp01/test/G19_FixedGrid_Celsius.png",
        "img_wgs84": "data_proc/sp01/test/G19_WGS84_Celsius.png",
        "log": "data_proc/sp01/test/process.log"
    }
    
    generate_mosaic_comparison(mis_outputs)
