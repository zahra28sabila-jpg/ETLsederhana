import sys
import pandas as pd
from utils.extract import scrape_main
from utils.transform import transform_data
from utils.load import load_data_to_csv, load_data_to_sheets, load_data_to_postgresql

# KONTROL KREDENSIAL POSTGRESQL
POSTGRES_CONFIG = {
    "host": "ep-empty-pine-ap3gvf86-pooler.c-7.us-east-1.aws.neon.tech",
    "port": 5432,
    "database": "neondb",
    "user": "neondb_owner",
    "password": "npg_vP8LcGrp5VIh",
    "table": "fashion_products"
}

def run_etl_pipeline():
    print("=" * 50)
    print("STARTING COMPLETE SCRIPT-BASED ETL PIPELINE")
    print("=" * 50)

    # 1. EXTRACT
    print("\n[1/3] Menjalankan Tahap Ekstraksi (Extract)...")
    raw_data = scrape_main()
    if not raw_data:
        print("[ERROR] Tahap Extract gagal. Pipeline dihentikan.")
        sys.exit(1)
    print(f"[SUCCESS] Berhasil mengekstrak {len(raw_data)} data kotor dari website.")

    # 2. TRANSFORM
    print("\n[2/3] Menjalankan Tahap Pembersihan Data (Transform)...")
    clean_df = transform_data(raw_data)
    if clean_df is None or clean_df.empty:
        print("[ERROR] Tahap Transform tidak menghasilkan data valid. Pipeline dihentikan.")
        sys.exit(1)
    print(f"[SUCCESS] Proses pembersihan selesai. {len(clean_df)} data bersih siap dimuat.")

    # 3. LOAD
    print("\n[3/3] Menjalankan Tahap Penyimpanan Data (Load)...")
    
    # 3a. CSV
    csv_success = load_data_to_csv(clean_df, filename="products.csv")
    
    # 3b. Google Sheets
    sheets_success = load_data_to_sheets(
        df=clean_df,
        spreadsheet_name="https://docs.google.com/spreadsheets/d/1TY9gWCdZQvRKYD02dgi-3LGWziChaBo37Z3rtM8xIfo/edit?usp=sharing", 
        json_key_file="google-sheets-api.json"
    )
    # 3c. PostgreSQL
    postgres_success = load_data_to_postgresql(clean_df, db_config=POSTGRES_CONFIG)

    print("\n" + "=" * 50)
    print("ETL PIPELINE EXECUTION SUMMARY")
    print("=" * 50)
    print(f"Status CSV Load          : {'SUKSES' if csv_success else 'GAGAL'}")
    print(f"Status Google Sheets Load: {'SUKSES' if sheets_success else 'GAGAL'}")
    print(f"Status PostgreSQL Load   : {'SUKSES' if postgres_success else 'GAGAL'}")
    print("=" * 50)
    print("ETL PIPELINE FINISHED.")
    print(clean_df.dtypes)
    

if __name__ == "__main__":
    run_etl_pipeline()