# File: captcha_solver.py (Versi BARU - reCAPTCHA + Turnstile)
import asyncio
from twocaptcha import AsyncTwoCaptcha, ValidationException, NetworkException, ApiException, TimeoutException
from rich.console import Console

# Impor dari file kita yang lain
import config
import constants

# Inisialisasi console
console = Console()

# Inisialisasi solver. Kita buat satu kali saja.
solver = AsyncTwoCaptcha(
    apiKey=config.API_KEY_2CAPTCHA,
    defaultTimeout=180,  # Waktu tunggu polling (detik)
    pollingInterval=5      # Jeda antar cek
)

async def solve_recaptcha_v2(page_url, proxy_settings=None):
    """
    Menyelesaikan reCAPTCHA V2 (Kotak "I'm not a robot").
    """
    
    # 1. Siapkan konfigurasi proxy (jika ada)
    proxy_dict = None
    if proxy_settings:
        try:
            host_port = proxy_settings['server'].replace('http://', '')
            proxy_string = f"{proxy_settings['username']}:{proxy_settings['password']}@{host_port}"
            proxy_dict = {'type': 'HTTP', 'uri': proxy_string}
        except Exception as e:
            console.print(f"[red]Gagal memformat string proxy: {e}[/red]")
            proxy_dict = None

    # 2. Kirim tugas ke 2Captcha
    try:
        console.print(f"Mengirim tugas reCAPTCHA V2 ke 2Captcha...")
        
        result = await solver.recaptcha(
            sitekey=constants.RECAPTCHA_SITE_KEY, # Sitekey reCAPTCHA
            url=page_url,
            proxy=proxy_dict
        )
        
        token = result.get('code')
        if token:
            console.print(f"[bold green]Solusi reCAPTCHA V2 Ditemukan![/bold green]")
            return token
        else:
            console.print(f"[bold red]2Captcha Error: Hasil reCAPTCHA tidak mengandung 'code'.[/bold red]")
            return None

    # 3. Tangani Error
    except TimeoutException as e:
        console.print(f"[bold red]2Captcha Timeout Error (reCAPTCHA): Gagal solve dalam 180 detik. {e}[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]Error tidak diketahui di reCAPTCHA solver: {e}[/bold red]")
        return None

# -----------------------------------------------------------------
# --- FUNGSI BARU UNTUK TURNSTILE ---
# -----------------------------------------------------------------
async def solve_turnstile_async(page_url, proxy_settings=None):
    """
    (FUNGSI BARU) Menyelesaikan Cloudflare Turnstile.
    """
    
    # 1. Siapkan konfigurasi proxy (jika ada)
    proxy_dict = None
    if proxy_settings:
        try:
            host_port = proxy_settings['server'].replace('http://', '')
            proxy_string = f"{proxy_settings['username']}:{proxy_settings['password']}@{host_port}"
            proxy_dict = {'type': 'HTTP', 'uri': proxy_string}
        except Exception as e:
            console.print(f"[red]Gagal memformat string proxy: {e}[/red]")
            proxy_dict = None

    # 2. Kirim tugas ke 2Captcha
    try:
        console.print(f"Mengirim tugas Turnstile ke 2Captcha...")
        
        result = await solver.turnstile(
            sitekey=constants.TURNSTILE_SITE_KEY, # Sitekey Turnstile
            url=page_url,
            proxy=proxy_dict
        )
        
        token = result.get('code')
        if token:
            console.print(f"[bold green]Solusi Turnstile Ditemukan![/bold green]")
            return token
        else:
            console.print(f"[bold red]2Captcha Error: Hasil Turnstile tidak mengandung 'code'.[/bold red]")
            return None

    # 3. Tangani Error
    except TimeoutException as e:
        console.print(f"[bold red]2Captcha Timeout Error (Turnstile): Gagal solve dalam 180 detik. {e}[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]Error tidak diketahui di Turnstile solver: {e}[/bold red]")
        return None