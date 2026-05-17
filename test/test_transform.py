import pytest
from utils.transform import transform_product_data

def test_transform_product_data_success():
    # Data mentah buatan yang sukses diekstrak dari web 
    mock_raw_data = [
        # Data Valid 1
        {
            "Title": "T-shirt 2",
            "Price": "$100.00",
            "Rating": "3.9 / 5",
            "Colors": "3 Colors",
            "Size": "Size: M",
            "Gender": "Gender: Women",
            "timestamp": "2026-05-17 12:00:00"
        },
        # Drop Data Invalid: Title Unknown Product 
        {
            "Title": "Unknown Product",
            "Price": "$50.00",
            "Rating": "4.0 / 5",
            "Colors": "1 Colors",
            "Size": "Size: S",
            "Gender": "Gender: Men"
        },
        # Drop Data Invalid: Price Unavailable 
        {
            "Title": "Pants 16",
            "Price": "Price Unavailable",
            "Rating": "4.5 / 5",
            "Colors": "2 Colors",
            "Size": "Size: L",
            "Gender": "Gender: Men"
        },
        # Drop Data Invalid: Rating Not Rated 
        {
            "Title": "Shoes 5",
            "Price": "$120.00",
            "Rating": "Not Rated",
            "Colors": "5 Colors",
            "Size": "Size: XL",
            "Gender": "Gender: Unisex"
        }
    ]

    result = transform_product_data(mock_raw_data)

    # ASSERTION 1: Dari 4 data, hanya 1 data yang valid (sisanya harus ke-filter/drop)
    assert len(result) == 1

    # ASSERTION 2: Verifikasi hasil pembersihan kolom data valid pertama
    product = result[0]
    assert product["Title"] == "T-shirt 2"
    
    # Price: $100.00 * 16000 = 1600000
    assert product["Price"] == 1600000
    assert isinstance(product["Price"], int)

    # Rating: "3.9 / 5" -> 3.9
    assert product["Rating"] == 3.9
    assert isinstance(product["Rating"], float)

    # Colors: "3 Colors" -> 3
    assert product["Colors"] == 3
    assert isinstance(product["Colors"], int)

    # Size: "Size: M" -> "M"
    assert product["Size"] == "M"
    assert isinstance(product["Size"], str)

    # Gender: "Gender: Women" -> "Women"
    assert product["Gender"] == "Women"
    assert isinstance(product["Gender"], str)


def test_transform_handle_invalid_input_type():
    # Menguji mekanisme error handling jika input ke fungsi bukan berupa list
    result = transform_product_data("Bukan sebuah list data")
    assert result == []
