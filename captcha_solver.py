# File: captcha_solver.py (Versi Proxy - Sesuai Tes Sukses)
import requests
import time
from rich.console import Console

# Impor variabel dari file config dan constants kita
import config
import constants

# Inisialisasi console
console = Console()

def solve_recaptcha_v2(proxy_settings=None):
    """
    Mengirim tugas reCAPTCHA V2 ke 2Captcha dan menunggu solusinya.
    Menggunakan proxy jika disediakan.
    """
    
    API_KEY = config.API_KEY_2CAPTCHA
    if not API_KEY or API_KEY == "KEY_ANDA_DISINI":
        console.print("[bold red]ERROR: API Key 2Captcha belum diatur di file .env[/bold red]")
        return None

    PAGE_URL = constants.LOGIN_URL 
    SITE_KEY = constants.RECAPTCHA_SITE_KEY

    console.print(f"Mengirim tugas CAPTCHA ke 2Captcha untuk {PAGE_URL}...")

    # 1. Kirim permintaan awal ke 2Captcha (in.php)
    try:
        url_in = "http://2captcha.com/in.php"
        payload_in = {
            'key': API_KEY,
            'method': 'userrecaptcha',
            'googlekey': SITE_KEY,
            'pageurl': PAGE_URL,
            'json': 1  # Minta respons dalam format JSON
        }
        
        # --- (INI BAGIAN PENTING) ---
        # Jika kita punya proxy, kirimkan ke 2Captcha
        if proxy_settings:
            console.print("[cyan]Mengirim informasi proxy ke 2Captcha...[/cyan]")
            # Format: user:pass@host:port
            host_port = proxy_settings['server'].replace('http://', '')
            proxy_string = (
                f"{proxy_settings['username']}:{proxy_settings['password']}@"
                f"{host_port}"
            )
            payload_in['proxy'] = proxy_string
            payload_in['proxytype'] = 'HTTP'
        else:
            console.print("[yellow]Menyelesaikan CAPTCHA tanpa proxy (mungkin gagal)...[/yellow]")
        # --- (AKHIR BAGIAN PENTING) ---

        response_in = requests.post(url_in, data=payload_in, timeout=30)
        response_in.raise_for_status()
        
        result_in = response_in.json()

        if result_in['status'] == 0:
            console.print(f"[bold red]2Captcha Error: {result_in['request']}[/bold red]")
            return None
        
        request_id = result_in['request']
        console.print(f"[green]Tugas CAPTCHA berhasil dikirim. ID Tugas: {request_id}[/green]")
        console.print("Menunggu hasil solusi (maks 180 detik)...")

    except requests.RequestException as e:
        console.print(f"[bold red]Gagal mengirim tugas ke 2Captcha: {e}[/bold red]")
        return None

    # 2. Polling hasil
    url_res = "http://2captcha.com/res.php"
    payload_res = {
        'key': API_KEY,
        'action': 'get',
        'id': request_id,
        'json': 1
    }
    
    start_time = time.time()
    while True:
        time.sleep(5) # Jeda 5 detik

        if time.time() - start_time > 180: # Timeout 3 menit
            console.print("[bold red]Gagal: Timeout 180 detik menunggu solusi CAPTCHA.[/bold red]")
            return None
        
        try:
            response_res = requests.get(url_res, params=payload_res, timeout=30)
            response_res.raise_for_status()
            
            result_res = response_res.json()

            if result_res['status'] == 1:
                solution_token = result_res['request']
                console.print(f"[bold green]Solusi CAPTCHA Ditemukan![/bold green]")
                return solution_token
            
            elif result_res['request'] == 'CAPCHA_NOT_READY':
                console.print("...Solusi belum siap, mencoba lagi...")
                continue
                
            else:
                console.print(f"[bold red]2Captcha Error: {result_res['request']}[/bold red]")
                return None

        except requests.RequestException as e:
            console.print(f"[bold red]Gagal mengecek hasil CAPTCHA: {e}[/bold red]")
            time.sleep(5)


# --- Bagian ini untuk testing ---
if __name__ == "__main__":
    console.print("[bold]--- Menjalankan Tes Solver CAPTCHA (Versi Proxy) ---[/bold]")
    
    proxy_settings_test = None
    if config.USE_PROXY:
         proxy_settings_test = {
            "server": f"http://{config.PROXY_HOST}:{config.PROXY_PORT}",
            "username": config.PROXY_USER,
            "password": config.PROXY_PASS
        }

    token = solve_recaptcha_v2(proxy_settings_test)
    
    if token:
        console.print("\n[green]Tes Berhasil.[/green]")
        console.print(f"Token yang didapat (awal): {token[:20]}...")
    else:
        console.print("\n[red]Tes Gagal.[/red]")