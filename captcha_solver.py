# File: captcha_solver.py
import requests
import time
from rich.console import Console

# Impor variabel dari file config dan constants kita
import config
import constants

# Inisialisasi console
console = Console()

def solve_recaptcha_v2():
    """
    Mengirim tugas reCAPTCHA V2 ke 2Captcha dan menunggu solusinya.
    """
    
    API_KEY = config.API_KEY_2CAPTCHA
    if not API_KEY or API_KEY == "KEY_ANDA_DISINI":
        console.print("[bold red]ERROR: API Key 2Captcha belum diatur di file .env[/bold red]")
        return None

    # URL target dan site key dari constants.py
    # Kita asumsikan site key di halaman login dan register sama
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
        
        response_in = requests.post(url_in, data=payload_in, timeout=30)
        response_in.raise_for_status() # Cek jika ada error HTTP
        
        result_in = response_in.json()

        if result_in['status'] == 0:
            console.print(f"[bold red]2Captcha Error: {result_in['request']}[/bold red]")
            return None
        
        request_id = result_in['request']
        console.print(f"[green]Tugas CAPTCHA berhasil dikirim. ID Tugas: {request_id}[/green]")
        console.print("Menunggu hasil solusi (bisa 30-90 detik)...")

    except requests.RequestException as e:
        console.print(f"[bold red]Gagal mengirim tugas ke 2Captcha: {e}[/bold red]")
        return None

    # 2. Polling (mengecek) hasil ke 2Captcha (res.php)
    url_res = "http://2captcha.com/res.php"
    payload_res = {
        'key': API_KEY,
        'action': 'get',
        'id': request_id,
        'json': 1
    }
    
    start_time = time.time()
    while True:
        # Beri jeda 5 detik sebelum mengecek lagi
        time.sleep(5)

        # Cek timeout (misal: 120 detik / 2 menit)
        if time.time() - start_time > 120:
            console.print("[bold red]Gagal: Timeout 120 detik menunggu solusi CAPTCHA.[/bold red]")
            return None
        
        try:
            response_res = requests.get(url_res, params=payload_res, timeout=30)
            response_res.raise_for_status()
            
            result_res = response_res.json()

            if result_res['status'] == 1:
                # --- BERHASIL ---
                solution_token = result_res['request']
                console.print(f"[bold green]Solusi CAPTCHA Ditemukan![/bold green]")
                # console.print(f"Token: {solution_token[:20]}...") # Jangan print token penuh
                return solution_token
            
            elif result_res['request'] == 'CAPCHA_NOT_READY':
                # Belum siap, biarkan loop berlanjut
                console.print("...Solusi belum siap, mencoba lagi...")
                continue
                
            else:
                # Ada error lain
                console.print(f"[bold red]2Captcha Error: {result_res['request']}[/bold red]")
                return None

        except requests.RequestException as e:
            console.print(f"[bold red]Gagal mengecek hasil CAPTCHA: {e}[/bold red]")
            time.sleep(5) # Coba lagi setelah jeda


# --- Bagian ini untuk testing ---
if __name__ == "__main__":
    console.print("[bold]--- Menjalankan Tes Solver CAPTCHA ---[/bold]")
    
    # Pastikan file .env Anda sudah diisi API Key 2Captcha
    token = solve_recaptcha_v2()
    
    if token:
        console.print("\n[green]Tes Berhasil.[/green]")
        console.print(f"Token yang didapat (awal): {token[:20]}...")
    else:
        console.print("\n[red]Tes Gagal.[/red]")