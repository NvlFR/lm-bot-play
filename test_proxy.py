# File: test_proxy.py
import requests
import config
from rich.console import Console

console = Console()

def check_proxy():
    """
    Melakukan tes koneksi sederhana menggunakan proxy dari file .env
    """
    
    if not config.USE_PROXY:
        console.print("[yellow]Tes Dibatalkan:[/yellow] USE_PROXY di .env di-set ke 'false'.")
        return

    if not config.PROXY_HOST:
        console.print("[bold red]Tes Gagal:[/bold red] Data proxy tidak ditemukan di .env.")
        return

    console.print(f"[cyan]Mencoba koneksi menggunakan proxy:[/cyan]")
    console.print(f"Host: {config.PROXY_HOST}")
    console.print(f"User: {config.PROXY_USER}")

    # Format proxy untuk library 'requests'
    proxy_url = (
        f"http://{config.PROXY_USER}:{config.PROXY_PASS}@"
        f"{config.PROXY_HOST}:{config.PROXY_PORT}"
    )
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    # Kita akan coba menghubungi 'https://api.ipify.org'
    # Ini adalah layanan yang mengembalikan IP publik Anda
    test_url = "https://api.ipify.org?format=json"
    
    try:
        console.print(f"Menghubungi {test_url}...")
        
        # Buat request dengan timeout 15 detik
        response = requests.get(test_url, proxies=proxies, timeout=15)
        
        response.raise_for_status() # Cek jika ada error HTTP (4xx, 5xx)
        
        # Jika berhasil, cetak IP yang dikembalikan
        ip_data = response.json()
        returned_ip = ip_data.get('ip')
        
        console.print("\n[bold green]--- KONEKSI BERHASIL! ---[/bold green]")
        console.print(f"IP yang dikembalikan oleh server: [bold]{returned_ip}[/bold]")
        console.print("\n[yellow]CATATAN:[/yellow] Pastikan IP ini BUKAN IP lokal Anda.")
        
    except requests.exceptions.HTTPError as e:
        console.print(f"\n[bold red]--- TES GAGAL (Error HTTP) ---[/bold red]")
        console.print(f"Status Code: {e.response.status_code}")
        console.print(f"Respon: {e.response.text}")
    except requests.exceptions.Timeout:
        console.print(f"\n[bold red]--- TES GAGAL (Timeout) ---[/bold red]")
        console.print("Proxy gagal merespon dalam 15 detik.")
    except requests.exceptions.RequestException as e:
        console.print(f"\n[bold red]--- TES GAGAL (Error Koneksi) ---[/bold red]")
        console.print(f"Error: {e}")

if __name__ == "__main__":
    check_proxy()