
"""
Module untuk melakukan ekstraksi (scraping) data katalog produk fashion.
Mendukung penarikan data hingga 50 halaman secara asinkronus menggunakan session.
"""

from __future__ import annotations
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://fashion-studio.dicoding.dev"
TOTAL_PAGES = 50
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    )
}

def fetch_page(session: requests.Session, page_number: int) -> BeautifulSoup | None:
    """Mengambil dokumen HTML dari satu halaman spesifik."""
    try:
        # Penentuan URL halaman
        target_url = f"{BASE_URL}/" if page_number == 1 else f"{BASE_URL}/page{page_number}"
        
        response = session.get(target_url, headers=BROWSER_HEADERS, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
        
    except requests.exceptions.RequestException as exc:
        print(f"Request error saat mengambil halaman {page_number}: {exc}")
        return None
    except Exception as exc:
        print(f"Error tak terduga saat mengambil halaman {page_number}: {exc}")
        return None

def extract_product_data(product_card) -> dict | None:
    """Mengekstrak informasi esensial dari satu kartu produk."""
    try:
        # Menggunakan pencarian berbasis kelas tag
        title_element = product_card.find(class_="product-title")
        price_element = product_card.find(class_="price")
        
        if title_element is None or price_element is None:
            raise ValueError("Elemen utama (Title/Price) produk tidak ditemukan.")

        # Ambil semua tag <p> di dalam detail produk
        detail_elements = product_card.find_all("p")
        
        # Inisialisasi variabel penampung string mentah
        rating_text = None
        colors_text = None
        size_text = None
        gender_text = None

        # Ekstraksi berbasis pencarian teks di dalam paragraf
        for element in detail_elements:
            text_content = element.get_text(strip=True)
            if text_content.startswith("Rating:"):
                rating_text = text_content
            elif "Colors" in text_content:
                colors_text = text_content
            elif text_content.startswith("Size:"):
                size_text = text_content
            elif text_content.startswith("Gender:"):
                gender_text = text_content

        # Validasi kelengkapan atribut produk sebelum dimasukkan ke pipeline
        if not all([rating_text, colors_text, size_text, gender_text]):
            raise ValueError("Atribut pendukung produk tidak lengkap.")

        # Pembersihan teks (menghilangkan prefix dan simbol bintang)
        rating = rating_text.replace("Rating:", "", 1).replace("\u2b50", "", 1).strip()
        size = size_text.replace("Size:", "", 1).strip()
        gender = gender_text.replace("Gender:", "", 1).strip()

        return {
            "Title": title_element.get_text(strip=True),
            "Price": price_element.get_text(strip=True),
            "Rating": rating,
            "Colors": colors_text,
            "Size": size,
            "Gender": gender,
            "Timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as exc:
        # Log error dilewati agar tidak memenuhi terminal saat mendeteksi data cacat biasa
        return None

def extract_page_products(soup: BeautifulSoup) -> list[dict]:
    """Mengumpulkan seluruh data produk yang valid dari satu halaman BeautifulSoup."""
    try:
        collected_products = []
        # Menggunakan find_all untuk mendapatkan semua kartu koleksi
        cards = soup.find_all("div", class_="collection-card")

        for card in cards:
            parsed_item = extract_product_data(card)
            if parsed_item is not None:
                collected_products.append(parsed_item)

        return collected_products
    except Exception as exc:
        print(f"Error saat mengekstrak list produk halaman: {exc}")
        return []

def scrape_main() -> list[dict]:
    """Eksekutor utama untuk scraping data halaman 1 sampai 50."""
    try:
        final_product_list = []

        with requests.Session() as session:
            for page in range(1, TOTAL_PAGES + 1):
                soup_document = fetch_page(session, page)
                if soup_document is None:
                    continue

                page_data = extract_page_products(soup_document)
                final_product_list.extend(page_data)

        return final_product_list
    except Exception as exc:
        print(f"Gagal menjalankan core engine scraping: {exc}")
        return []