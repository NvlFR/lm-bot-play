# File: bot_core.py (Perbaikan Timeout networkidle)
import asyncio
import os
import random
import time
from patchright.async_api import async_playwright
from rich.console import Console

# --- 1. IMPOR LENGKAP ---
import config
import constants
import captcha_solver
import account_manager
# -------------------------

console = Console()

# Path untuk menyimpan status login (cookies)
STORAGE_STATE_DIR = "browser_states"
os.makedirs(STORAGE_STATE_DIR, exist_ok=True)


NAVIGATION_DELAYS = {
    'page_load': (3000, 8000), 'after_fill': (800, 2000), 'after_click': (1500, 4000),
    'before_submit': (3000, 6000), 'human_pause': (10000, 20000)
}

async def handle_cloudflare_blocking(page):
    """
    Menangani mekanisme blokir Cloudflare.
    """
    try:
        error_content = await page.content()
        if "Error 1020" in error_content or "access denied" in error_content.lower():
            console.print("[bold red]DETEKSI ERROR 1020: Akses ditolak oleh Cloudflare WAF![/bold red]")
            return False
            
        if "Checking your browser" in error_content or "Attention Required" in error_content:
            console.print("[yellow]Mendeteksi halaman 'Checking your browser'... Menunggu...[/yellow]")
            await asyncio.sleep(random.randint(15, 30))
            new_content = await page.content()
            if "Checking your browser" in new_content:
                console.print("[red]Challenge CF belum terselesaikan otomatis[/red]")
                return False
            return True
            
        return True
    except Exception as e:
        console.print(f"[red]Error saat menangani Cloudflare blocking: {e}[/red]")
        return False

# -----------------------------------------------------------------
# --- FUNGSI LOGIN ---
# -----------------------------------------------------------------
async def login_account(account):
    """
    Login menggunakan Patchright murni, sesuai "Best Practice".
    """
    email = account['email']
    password = account['password']
    console.print(f"\n[bold yellow]--- Mencoba Login Akun: {email} ---[/bold yellow]")

    is_headless = False # Hardcode ke False untuk testing
    browser = None
    
    # Siapkan Proxy
    proxy_settings = None
    if config.USE_PROXY:
        if config.PROXY_HOST:
            proxy_settings = {
                "server": f"http://{config.PROXY_HOST}:{config.PROXY_PORT}",
                "username": config.PROXY_USER, "password": config.PROXY_PASS
            }
            console.print("[green]Menggunakan Jaringan Proxy.[/green]")
        else:
            console.print("[yellow]PERINGATAN: USE_PROXY=true tapi data proxy tidak ada. Menggunakan Jaringan Lokal.[/yellow]")
    else:
        console.print("[cyan]Menggunakan Jaringan Lokal (Tanpa Proxy).[/cyan]")

    # (BARU) Gunakan context manager patch_playwright
    async with async_playwright() as p:
        try:
            # 1. Luncurkan browser
            browser = await p.chromium.launch(
                headless=is_headless,
                proxy=proxy_settings,
                channel="chrome" 
            )
            
            # 2. Buat Context
            console.print("[cyan]Membuat context (menggunakan stealth Patchright)...[/cyan]")
            context = await browser.new_context(
                no_viewport=True # Sesuai "Best Practice"
            )
            page = await context.new_page()
            
            # 4. Navigasi ke Halaman Login
            console.print("Membuka halaman login...")
            
            # --- (PERUBAHAN DI SINI) ---
            # Kita ganti 'networkidle' ke 'domcontentloaded'
            # Ini akan menyelesaikan timeout
            await page.goto(constants.LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
            # --- (AKHIR PERUBAHAN) ---

            await asyncio.sleep(random.randint(1, 3)) # Jeda singkat
            
            # 5. Tangani Blokir CF
            if not await handle_cloudflare_blocking(page):
                raise Exception("Diblokir oleh Cloudflare (Error 1020 atau 'Checking')")
                
            # 6. Tunggu Form
            console.print("Menunggu form login muncul...")
            await page.wait_for_selector('input[name="username"]', timeout=60000)
            console.print("[green]Form login terdeteksi.[/green]")
            
            # 7. Ambil KEDUA Token CSRF
            console.print("Mengambil token CSRF...")
            csrf_token_element = page.locator('input[name="token"]').first
            csrf_token = await csrf_token_element.get_attribute('value')
            
            csrf_name_element = page.locator('input[name="csrf_test_name"]').first
            csrf_name_token = await csrf_name_element.get_attribute('value')
            
            if not csrf_token or not csrf_name_token:
                raise Exception("Gagal menemukan semua token CSRF")
                
            console.print(f"[green]Token 1 (token) didapat: {csrf_token[:10]}...[/green]")
            console.print(f"[green]Token 2 (csrf_test_name) didapat: {csrf_name_token[:10]}...[/green]")

            # 8. Selesaikan CAPTCHA
            console.print("Memulai penyelesaian CAPTCHA...")
            captcha_token = captcha_solver.solve_recaptcha_v2(proxy_settings)
            if not captcha_token:
                raise Exception("Gagal mendapatkan token CAPTCHA")

            console.print("[green]Token CAPTCHA didapat.[/green] Mengisi form...")
            
            # 9. Isi Form
            await page.fill('input[name="username"]', email)
            await asyncio.sleep(random.uniform(0.5, 2))
            await page.fill('input[name="password"]', password)
            await asyncio.sleep(random.uniform(0.5, 2))

            # 10. Suntikkan SEMUA token
            await page.evaluate(f"""document.getElementById('g-recaptcha-response').value = '{captcha_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="token"]').value = '{csrf_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="csrf_test_name"]').value = '{csrf_name_token}';""")

            try:
                await page.click('label[for="customCheckb1"]')
                console.print("Mencentang 'Remember Me'...")
            except Exception:
                console.print(f"[yellow]Peringatan: Gagal mencentang 'Remember Me' (lanjut).[/yellow]")

            # 11. Scroll dan Submit
            await page.evaluate("""() => { document.querySelector('button[type="submit"]').scrollIntoView(); }""")
            await asyncio.sleep(random.uniform(2, 5))

            console.print("Mengklik tombol login...")
            await page.click('button[type="submit"]')
            
            # 12. Tunggu Hasil
            console.print("Menunggu hasil login...")
            try:
                await page.wait_for_url(lambda url: constants.PROFILE_URL in url, timeout=20000)
            except Exception:
                # Gagal login, cari tahu kenapa
                console.print(f"[bold red]GAGAL LOGIN: {email}[/bold red]")
                console.print(f"URL saat ini: {page.url}")
                try:
                    error_title = await page.locator(".swal2-title").text_content(timeout=3000)
                    error_body = await page.locator(".swal2-html-container").text_content(timeout=3000)
                    console.print(f"[bold yellow]Pesan Error: {error_title.strip()} - {error_body.strip()}[/bold yellow]")
                except:
                    content = await page.content()
                    if "Error 1020" in content or "Akses ditolak" in content or "blocked" in content.lower():
                        console.print("[bold red]TERDETEKSI: Cloudflare WAF Error 1020 (Access Denied)[/bold red]")
                    else:
                        console.print("[bold red]Tidak dapat menemukan pesan error. Kemungkinan besar email/password salah.[/bold red]")
                return False

            # 13. Sukses
            console.print(f"[bold green]BERHASIL LOGIN: {email}[/bold green]")
            
            storage_state_path = os.path.join(STORAGE_STATE_DIR, f"state_{email.replace('@', '_').replace('.', '_')}.json")
            await context.storage_state(path=storage_state_path)
            console.print(f"Status login disimpan ke {storage_state_path}")
            
            if browser and not is_headless:
                console.print("[cyan]Login sukses! Menutup browser dalam 5 detik...[/cyan]")
                await asyncio.sleep(5)
            await browser.close()
            return True

        except Exception as e:
            console.print(f"[bold red]Error saat login {email}: {str(e)}[/bold red]")
            if browser and not is_headless:
                console.print("[cyan]Terjadi error. Menutup browser dalam 5 detik...[/cyan]")
                await asyncio.sleep(5)
            if browser:
                await browser.close()
            return False
    

# --- BLOK TES ---
async def main_test():
    console.print("[bold]--- Menjalankan Tes Login (Fase 3 - Perbaikan Timeout) ---[/bold]")
    
    accounts = account_manager.get_all_accounts()
    
    if not accounts:
        console.print("[bold red]Tidak ada akun di accounts.json.[/bold red]")
        console.print("Silakan jalankan 'python main.py' dan pilih opsi 4 untuk menambah akun.")
        return

    akun_tes = accounts[0]
    sukses = await login_account(akun_tes)
    
    if sukses:
        console.print("\n[green]Tes Login Berhasil.[/green]")
    else:
        console.print("\n[red]Tes Login Gagal.[/red]")

if __name__ == "__main__":
    asyncio.run(main_test())