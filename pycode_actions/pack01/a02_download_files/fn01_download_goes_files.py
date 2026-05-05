"""
Path: legion_goes/pycode_actions/pack01/a02_download/download_goes_files.py
Version: 2.2.0
Description: Downloader with centralized path management and size-based check.
Last modification: 05-05-2026 18:18
"""
# =========================================================================================================================
#  python3 -m legion_goes.pycode_actions.pack01.a02_download_files.fn01_download_goes_files
# =========================================================================================================================

# Libreries
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path
import os

# Local libreries
from legion_goes.pycode_actions.pack01.fn_common.get_sat_id_by_date import get_sat_id_by_date
from legion_goes.pycode_actions.pack01.fn_common.gen_str_path_folder_raw_until_hour import gen_str_path_folder_raw_until_hour


# =================================================================================================================================
# 1. DOWNLOAD CORE
# Description: La funcion descargara todos los archivos disponbiles para la posicion, produto,year, day y hora.
# La hora puede ser un valor unico o ser ALL.
# Si el archivo existe localmente, verifica que el peso del  archivo local sea igual al archivo online.
# Si son iguales los pesos, no lo d escarga. SI hay diferentecias, borrael local y  realiza l a d escarga.
# Si el archivo no e xiste  localemtne, inicia la d escarga.
# =================================================================================================================================

def download_goes_files(position: str, product: str, year: str, day: str, hour: str):
    """
    Downloads files from S3 respecting the hourly folder hierarchy.
    Size check: if file exists but size differs, it re-downloads it.
    """
    # Type validation
    args = {"position": position, "product": product, "year": year, "day": day, "hour": hour}
    for name, value in args.items():
        if not isinstance(value, str):
            raise TypeError(f"Argument '{name}' must be a string, received {type(value).__name__}")

    # Basics
    sat_id = get_sat_id_by_date(position=position, year=year, day=day)
    
    # S3 Client Configuration (Public Access)
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    bucket_name = f"noaa-goes{sat_id}"
    
    # Build S3 search prefix
    base_prefix = f"{product}/{year}/{day}/"
    if hour.upper() == "ALL":
        search_prefix = base_prefix
    else:
        search_prefix = f"{base_prefix}{hour.zfill(2)}/"
    
    print("\n" + "="*80)
    print(f"📡 SCANNING S3: s3://{bucket_name}/{search_prefix}")
    print("="*80)
    
    # List objects storing Key and Size using Paginator
    files_metadata = []
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=search_prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.nc'):
                    files_metadata.append({
                        'key': obj['Key'],
                        'size': obj['Size']  # Size in bytes from AWS
                    })

    if not files_metadata:
        print(f"⚠️ No files found for: {product} | {year}-{day} | Hour: {hour}")
        return

    print(f"📦 Total files found: {len(files_metadata)}")

    # File download loop
    for meta in files_metadata:
        s3_key = meta['key']
        s3_size = meta['size']
        
        parts = s3_key.split('/')
        file_hour = parts[-2]
        filename = parts[-1]

        # Generate local output path
        final_output_dir = gen_str_path_folder_raw_until_hour(
            position=position, 
            product=product, 
            year=year, 
            day=day, 
            hour=file_hour
        )
        final_output_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = final_output_dir / filename
        
        # --- Size Verification Logic ---
        if dest_path.exists():
            local_size = dest_path.stat().st_size
            
            if local_size == s3_size:
                print(f"  [SKIPPED] {file_hour}/{filename} (Size OK)")
                continue
            else:
                print(f"  [RE-DOWNLOADING] {file_hour}/{filename} (Size mismatch: Local {local_size} vs S3 {s3_size})")
                dest_path.unlink() # Remove corrupted/incomplete file
        else:
            print(f"  [DOWNLOADING] {file_hour}/{filename}...", end=" ", flush=True)
        
        # --- Actual S3 Download ---
        try:
            s3.download_file(bucket_name, s3_key, str(dest_path))
            print("OK")
        except Exception as e:
            print(f"\n  ❌ Error in {filename}: {e}")

    print("\n" + "="*80)
    print(f"✅ DOWNLOAD COMPLETED")
    print(f"📂 Data stored in: {final_output_dir}")
    print("="*80 + "\n")

# =============================================================================
# 3. EXECUTION
# =============================================================================

if __name__ == "__main__":
    download_goes_files(
        position="WEST", 
        product="ABI-L2-LSTF", 
        year="2026", 
        day="003", 
        hour="ALL"
    )
