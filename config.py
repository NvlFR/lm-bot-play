# File: config.py
import os
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()

# --- Pengaturan Jaringan & Proxy ---
# Membaca pengaturan USE_PROXY dari .env
# .lower() == "true" akan mengubah string "true" menjadi boolean True
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"

PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")

# --- Kunci API ---
API_KEY_2CAPTCHA = os.getenv("TWO_CAPTCHA_API_KEY")

# Format proxy string (hanya jika akan dipakai)
PROXY_STRING = ""
if USE_PROXY and PROXY_HOST:
    PROXY_STRING = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# --- Pengaturan File ---
ACCOUNTS_FILE = "accounts.json"

# Cek konfigurasi
if USE_PROXY and not PROXY_HOST:
    print("PERINGATAN: USE_PROXY=true tapi data proxy (HOST/PORT) tidak ada di .env")

if not API_KEY_2CAPTCHA:
    print("PERINGATAN: TWO_CAPTCHA_API_KEY tidak ditemukan di file .env")