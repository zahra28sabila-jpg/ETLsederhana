import pytest
from unittest.mock import patch, MagicMock
from utils.extract import extract_product_data
import re

SAMPLE_PAGE_HTML = """
<html>
  <body>
    <div class="collection-card">
      <div class="product-details">
        <h3 class="product-title">T-shirt 2</h3>
        <span class="price">$102.15</span>
        <p>3 Colors</p>
        <p>Size: M</p>
        <p>Gender: Women</p>
      </div>
    </div>
  </body>
</html>
"""

@patch('utils.extract.requests.get')
def test_extract_product_data_includes_timestamp(mock_get):
    # Menyusun mock response ]
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_PAGE_HTML
    mock_get.return_value = mock_response

    # Jalankan fungsi uji coba untuk 1 halaman saja
    result = extract_product_data("https://fashion-studio.dicoding.dev", max_pages=1)

    assert len(result) == 1
    
    # 1. Pastikan key 'timestamp' ada di dalam output data
    assert "timestamp" in result[0]
    
    # 2. Validasi format timestamp menggunakan Regex (YYYY-MM-DD HH:MM:SS)
    timestamp_val = result[0]["timestamp"]
    timestamp_pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    assert re.match(timestamp_pattern, timestamp_val) is not None

@patch('utils.extract.requests.get')
def test_extract_product_data_network_error_handling(mock_get):
    # Menguji mekanisme error handling jika koneksi internet terputus / timeout
    mock_get.side_effect = Exception("Simulated Network Timeout Error")

    # Fungsi harus menangani error di dalam blok try-except dan mengembalikan list kosong
    result = extract_product_data("https://fashion-studio.dicoding.dev", max_pages=1)
    
    assert isinstance(result, list)
    assert result == []