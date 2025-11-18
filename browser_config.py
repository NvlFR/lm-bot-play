# File: browser_config.py (Enhanced & Functional Version)
import random

# --- DATA STATIS (KONSTAN) ---
TIMEZONE = "Asia/Jakarta"

# Daftar data untuk diacak
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 1024}
]

LOCALES = [
    "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,id;q=0.8",
    "id-ID,id;q=1.0,en-US;q=0.9,en;q=0.8"
]

PLATFORMS = ["Win32", "Win64"]
HARDWARE_CONCURRENCY = [4, 8, 16]
DEVICE_MEMORY = [4, 8, 16]

# --- FUNGSI UTAMA ---

def get_random_config():
    """
    Menghasilkan satu set lengkap fingerprint browser yang diacak
    untuk setiap sesi login baru.
    """
    
    # Pilih item acak
    user_agent = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)
    locale = random.choice(LOCALES)
    platform = random.choice(PLATFORMS)
    hardware_concurrency = random.choice(HARDWARE_CONCURRENCY)
    device_memory = random.choice(DEVICE_MEMORY)
    device_scale_factor = random.choice([1, 1.25, 1.5])

    # Hasilkan dict konfigurasi
    config = {
        # Opsi untuk Context
        "context_options": {
            "user_agent": user_agent,
            "viewport": viewport,
            "screen": {
                "width": viewport["width"],
                "height": viewport["height"],
                "device_scale_factor": device_scale_factor
            },
            "timezone_id": TIMEZONE,
            "locale": locale,
            "accept_downloads": False,
            "is_mobile": False,
            "has_touch": False
        },
        
        # Opsi untuk Header HTTP
        "extra_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": locale,
            "Accept-Encoding": "gzip, deflate, br",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        },
        
        # Opsi untuk disuntikkan ke JavaScript (Init Script)
        "device_params": {
            "platform": platform,
            "hardwareConcurrency": hardware_concurrency,
            "deviceMemory": device_memory
        }
    }
    
    return config