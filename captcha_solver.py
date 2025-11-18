# File: captcha_solver.py (Versi Jaringan Lokal 2Captcha)
import asyncio
from twocaptcha import AsyncTwoCaptcha, ValidationException, NetworkException, ApiException, TimeoutException
from rich.console import Console

# Impor dari file kita yang lain
import config
import constants

# Inisialisasi console
console = Console()

# (PERBAIKAN) Cek API Key SEBELUM inisialisasi
if not config.API_KEY_2CAPTCHA or config.API_KEY_2CAPTCHA == "KEY_ANDA_DISINI":
    console.print("[bold red]FATAL: API_KEY_2CAPTCHA tidak ditemukan di file config.py atau .env[/bold red]")
    solver = None
else:
    solver = AsyncTwoCaptcha(
        apiKey=config.API_KEY_2CAPTCHA,
        defaultTimeout=180,  # Waktu tunggu polling (detik)
        pollingInterval=5      # Jeda antar cek
    )

async def solve_recaptcha_v2(page_url, proxy_settings=None):
    """
    Menyelesaikan reCAPTCHA V2 (Kotak "I'm not a robot").
    Fungsi ini SENGAJA MENGABAIKAN 'proxy_settings' dan pakai IP lokal.
    """
    if not solver: 
        console.print("[bold red]Solver 2Captcha tidak terinisialisasi (Cek API Key).[/bold red]")
        return None
        
    # 2. Kirim tugas ke 2Captcha
    try:
        console.print(f"Mengirim tugas reCAPTCHA V2 ke 2Captcha...")
        console.print("[cyan]Solver akan menggunakan jaringannya sendiri (bukan proxy)...[/cyan]")
        
        result = await solver.recaptcha(
            sitekey=constants.RECAPTCHA_SITE_KEY, # Sitekey reCAPTCHA
            url=page_url,
            proxy=None # <-- SENGAJA DISET None
        )
        
        token = result.get('code')
        if token:
            console.print(f"[bold green]Solusi reCAPTCHA V2 Ditemukan![/bold green]")
            return token
        else:
            console.print(f"[bold red]2Captcha Error: Hasil reCAPTCHA tidak mengandung 'code'.[/bold red]")
            return None

    # 3. Tangani Error
    except Exception as e:
        console.print(f"[bold red]Error tidak diketahui di reCAPTCHA solver: {repr(e)}[/bold red]") 
        return None

# -----------------------------------------------------------------
# --- FUNGSI BARU UNTUK TURNSTILE ---
# -----------------------------------------------------------------
async def solve_turnstile_async(page_url, proxy_settings=None):
    """
    (FUNGSI BARU) Menyelesaikan Cloudflare Turnstile.
    Fungsi ini SENGAJA MENGABAIKAN 'proxy_settings' dan pakai IP lokal.
    """
    if not solver: 
        console.print("[bold red]Solver 2Captcha tidak terinisialisasi (Cek API Key).[/bold red]")
        return None
        
    # 2. Kirim tugas ke 2Captcha
    try:
        console.print(f"Mengirim tugas Turnstile ke 2Captcha...")
        console.print("[cyan]Solver akan menggunakan jaringannya sendiri (bukan proxy)...[/cyan]")
        
        result = await solver.turnstile(
            sitekey=constants.TURNSTILE_SITE_KEY, # Sitekey Turnstile
            url=page_url,
            proxy=None # <-- SENGAJA DISET None
        )
        
        token = result.get('code')
        if token:
            console.print(f"[bold green]Solusi Turnstile Ditemukan![/bold green]")
            return token
        else:
            console.print(f"[bold red]2Captcha Error: Hasil Turnstile tidak mengandung 'code'.[/bold red]")
            return None

    # 3. Tangani Error
    except Exception as e:
        console.print(f"[bold red]Error tidak diketahui di Turnstile solver: {repr(e)}[/bold red]") 
        return None