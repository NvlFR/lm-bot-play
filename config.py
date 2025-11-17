# File: config.py
import os
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()

# --- Kunci API & Proxy ---
API_KEY_2CAPTCHA = os.getenv("TWO_CAPTCHA_API_KEY")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")

# Format proxy string untuk Playwright (jika diperlukan)
PROXY_STRING = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# --- Pengaturan File ---
ACCOUNTS_FILE = "accounts.json"

# Cek apakah API key ada
if not API_KEY_2CAPTCHA:
    # Ini hanya print, tidak menghentikan program
    print("PERINGATAN: TWO_CAPTCHA_API_KEY tidak ditemukan di file .env")

if not PROXY_USER:
    # Ini hanya print, tidak menghentikan program
    print("PERINGATAN: Kredensial proxy tidak lengkap di file .env")