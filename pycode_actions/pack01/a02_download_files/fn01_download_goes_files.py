"""
Path: legion_goes/pycode_actions/pack01/a02_download/download_goes_files.py
Version: 2.1.0
Description: Downloader con gestión de rutas centralizada para Legion GOES.
"""
# ==================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.a02_download_files.fn01_download_goes_files
# ==================================================================================

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path
import os


# =============================================================================
# 1. GESTIÓN DE RUTAS (CENTRALIZADA)
# =============================================================================
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.gen_str_path_folder_raw_until_hour import gen_str_path_folder_raw_until_hour


# =============================================================================
# 2. CORE DE DESCARGA
# =============================================================================

def download_goes_files(position: str, product: str, year: str, day: str, hour: str):
    """
    Descarga archivos desde S3 respetando la jerarquía de carpetas horarias.
    """
    # Validación de tipos básica
    args = {"position": position, "product": product, "year": year, "day": day, "hour": hour}
    for name, value in args.items():
        if not isinstance(value, str):
            raise TypeError(f"El argumento '{name}' debe ser string, se recibió {type(value).__name__}")

    sat_id = get_sat_id_by_date(position=position, year=year, day=day)
    
    # Configuración de Cliente S3 (Acceso Público)
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    bucket_name = f"noaa-goes{sat_id}"
    
    # Construcción del prefijo para búsqueda en S3
    base_prefix = f"{product}/{year}/{day}/"
    if hour.upper() == "ALL":
        search_prefix = base_prefix
    else:
        search_prefix = f"{base_prefix}{hour.zfill(2)}/"
    
    print("\n" + "="*80)
    print(f"📡 ESCANEANDO S3: s3://{bucket_name}/{search_prefix}")
    print("="*80)
    
    # Listado de objetos usando Paginator para evitar límites de 1000 items
    files_to_download = []
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=search_prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                # Filtramos para evitar carpetas vacías si las hubiera
                if obj['Key'].endswith('.nc'):
                    files_to_download.append(obj['Key'])

    if not files_to_download:
        print(f"⚠️ No se encontraron archivos para: {product} | {year}-{day} | Hora: {hour}")
        return

    print(f"📦 Total archivos encontrados: {len(files_to_download)}")

    # Descarga de archivos
    for s3_key in files_to_download:
        # s3_key: 'ABI-L2-LSTF/2026/003/12/OR_ABI-L2-LSTF-M6_G19_s20260031200230...'
        parts = s3_key.split('/')
        file_hour = parts[-2]  # Extraemos la hora real del objeto en S3
        filename = parts[-1]   # Nombre del archivo NetCDF

        # USAMOS LA FUNCIÓN PARA GENERAR EL PATH DE SALIDA
        final_output_dir = gen_str_path_folder_raw_until_hour(position = position, product=product, year=year, day=day, hour=file_hour)
        final_output_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = final_output_dir / filename
        
        # Lógica de Skip si ya existe
        if dest_path.exists():
            print(f"  [SKIPPED] {file_hour}/{filename}")
            continue
            
        print(f"  [DOWNLOADING] {file_hour}/{filename}...", end=" ", flush=True)
        try:
            s3.download_file(bucket_name, s3_key, str(dest_path))
            print("OK")
        except Exception as e:
            print(f"\n  ❌ Error en {filename}: {e}")

    print("\n" + "="*80)
    print(f"✅ DESCARGA FINALIZADA")
    print(f"📂 Datos en: {Path.cwd() / 'data_raw' / bucket_name}")
    print("="*80 + "\n")

# =============================================================================
# 3. EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    # Ejemplo: Descargar todas las horas del 3 de enero de 2026 para GOES-19
    download_goes_files(
        position="WEST", 
        product="ABI-L2-LSTF", 
        year="2026", 
        day="003", 
        hour="ALL"
    )
