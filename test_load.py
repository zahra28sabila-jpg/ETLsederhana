import pytest
import os
import csv
from unittest.mock import patch, MagicMock
from utils.load import load_data_to_csv, load_data_to_sheets

@pytest.fixture
def sample_clean_data():
    return [
        {
            "Title": "T-shirt 2",
            "Price": 1634400,
            "Rating": 3.9,
            "Colors": 3,
            "Size": "M",
            "Gender": "Women",
            "timestamp": "2026-05-17 12:00:00"
        }
    ]

# 1. Simpan ke CSV
def test_load_data_to_csv_success(sample_clean_data):
    test_filename = "test_products_output.csv"
    
    # Jalankan fungsi load csv
    result = load_data_to_csv(sample_clean_data, filename=test_filename)
    
    # Pastikan fungsi mengembalikan nilai True (sukses)
    assert result is True
    # Pastikan file fisiknya beneran terbuat
    assert os.path.exists(test_filename)

    # Baca kembali file CSV untuk memastikan isinya tidak korup
    with open(test_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]["Title"] == "T-shirt 2"
        assert int(rows[0]["Price"]) == 1634400

    # Bersihkan file sampah hasil test agar tidak mengotori direktori
    if os.path.exists(test_filename):
        os.remove(test_filename)

# 2. Test Error Handling jika data kosong
def test_load_data_to_csv_empty_data():
    result = load_data_to_csv([])
    assert result == False

# 3. Test Mocking Google Sheets Load
@patch('utils.load.gspread.authorize')
@patch('utils.load.ServiceAccountCredentials.from_json_keyfile_name')
@patch('utils.load.os.path.exists')
def test_load_data_to_sheets_success(mock_exists, mock_creds, mock_authorize, sample_clean_data):
    # Simulasikan bahwa file json kredensial itu "ada"
    mock_exists.return_value = True
    
    # Buat tiruan struktur gspread client, spreadsheet, dan worksheet
    mock_client = MagicMock()
    mock_spreadsheet = MagicMock()
    mock_worksheet = MagicMock()
    
    mock_authorize.return_value = mock_client
    mock_client.open.return_value = mock_spreadsheet
    mock_spreadsheet.sheet1 = mock_worksheet

    # Jalankan fungsi load sheets
    result = load_data_to_sheets(sample_clean_data, json_key_file="fake-key.json")

    # Verifikasi sukses 
    assert result is True
    mock_client.open.assert_called_once_with("ETL_Products_Data")
    mock_worksheet.insert_rows.assert_called_once()