from __future__ import annotations
from pathlib import Path
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def load_data_to_csv(df: pd.DataFrame, filename: str = "products.csv") -> bool:
    """Menyimpan DataFrame ke file CSV."""
    try:
        output_path = Path(filename)
        df.to_csv(output_path, index=False)
        print(f"Load Sukses: Data berhasil disimpan ke {filename}")
        return True
    except Exception as exc:
        print(f"Gagal menyimpan data ke CSV: {exc}")
        return False
def load_data_to_sheets(
    df: pd.DataFrame,
    spreadsheet_name: str,
    json_key_file: str = "google-sheets-api.json",
) -> bool:
    """Mengunggah DataFrame ke Google Sheets menggunakan service account.
    
    Mendukung fleksibilitas pembukaan file via Spreadsheet ID (Key), 
    URL penuh, maupun nama teks biasa untuk meningkatkan portabilitas.
    """
    try:
        credentials_path = Path(json_key_file)
        if not credentials_path.exists():
            raise FileNotFoundError(f"File kredensial tidak ditemukan: {json_key_file}")

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            str(credentials_path), scope
        )
        client = gspread.authorize(credentials)

        # ====== PERBAIKAN PORTABILITAS: MEMBUKA BERDASARKAN ID / KEY ======
        try:
            if spreadsheet_name.startswith("http://") or spreadsheet_name.startswith("https://"):
                spreadsheet = client.open_by_url(spreadsheet_name)
            elif len(spreadsheet_name) > 30:  # Jika string panjang, deteksi sebagai Spreadsheet ID/Key
                spreadsheet = client.open_by_key(spreadsheet_name)
            else:
                spreadsheet = client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            # Jika ID atau nama tidak ditemukan di Drive robot, robot akan membuat file baru
            spreadsheet = client.create(spreadsheet_name)

        worksheet = spreadsheet.sheet1
        worksheet.clear()

        # ====== FIX EROR TIMESTAMP: Jinakkan Tipe Data Datetime64 ======
        # Buat salinan aman khusus untuk Google Sheets agar tidak merusak data asli untuk PostgreSQL
        sheet_ready_df = df.copy()
        
        # Deteksi otomatis kolom bertipe waktu/datetime, ubah menjadi teks string standar ISO
        for col in sheet_ready_df.columns:
            if pd.api.types.is_datetime64_any_dtype(sheet_ready_df[col]):
                sheet_ready_df[col] = sheet_ready_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Bersihkan data kosong (NaN/None) menjadi string kosong agar aman ditransfer via JSON API
        sheet_ready_df = sheet_ready_df.astype(object).where(pd.notna(sheet_ready_df), "")
        
        # Susun kolom dan baris menjadi format List of List
        rows = [sheet_ready_df.columns.tolist()] + sheet_ready_df.values.tolist()
        
        # Kirim data secara massal ke Google Sheets
        worksheet.append_rows(rows, value_input_option='RAW')
        
        print(f"Load Sukses: Data berhasil diunggah ke Google Sheets '{spreadsheet_name}'")
        return True
    except Exception as exc:
        print(f"Gagal terhubung atau mengunggah ke Google Sheets: {exc}")
        return False    

def load_data_to_postgresql(df: pd.DataFrame, db_config: dict) -> bool:
    """Menyimpan DataFrame ke tabel PostgreSQL menggunakan konfigurasi koneksi."""
    connection = None
    try:
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extras import execute_batch

        # 1. Membangun koneksi ke database PostgreSQL
        connection = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
        )

        table_name = db_config.get("table", "fashion_products")

        with connection:
            with connection.cursor() as cursor:
                # 2. Membuat tabel jika belum ada di database
                create_table_query = sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        title TEXT,
                        price DOUBLE PRECISION,
                        rating DOUBLE PRECISION,
                        colors INTEGER,
                        size TEXT,
                        gender TEXT,
                        timestamp TEXT
                    )
                    """
                ).format(table_name=sql.Identifier(table_name))
                cursor.execute(create_table_query)

                # 3. Kosongkan tabel lama agar data tidak menumpuk (TRUNCATE)
                truncate_query = sql.SQL("TRUNCATE TABLE {table_name}").format(
                    table_name=sql.Identifier(table_name)
                )
                cursor.execute(truncate_query)

                # 4. Ambil record dari DataFrame (Nama kolom disesuaikan dengan huruf besar kapital)
                records = [
                    (
                        row["Title"],
                        float(row["Price"]) if pd.notna(row["Price"]) else None,
                        float(row["Rating"]) if pd.notna(row["Rating"]) else None,
                        int(row["Colors"]) if pd.notna(row["Colors"]) else None,
                        row["Size"],
                        row["Gender"],
                        row["Timestamp"],
                    )
                    for _, row in df.iterrows()
                ]

                # 5. Eksekusi batch insert secara massal (sangat cepat untuk 867 data)
                if records:
                    insert_query = sql.SQL(
                        """
                        INSERT INTO {table_name}
                        (title, price, rating, colors, size, gender, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                    ).format(table_name=sql.Identifier(table_name))
                    execute_batch(
                        cursor,
                        insert_query.as_string(connection),
                        records,
                    )
        
        print(f"Load Sukses: Data berhasil disimpan ke PostgreSQL tabel '{table_name}'")
        return True
    except ModuleNotFoundError as exc:
        print(f"Library PostgreSQL belum tersedia: {exc}")
        return False
    except Exception as exc:
        print(f"Gagal terhubung atau menyimpan ke PostgreSQL: {exc}")
        return False
    finally:
        if connection is not None:
            connection.close()
