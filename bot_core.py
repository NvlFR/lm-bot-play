# File: bot_core.py (Versi FINAL - Turnstile + reCAPTCHA)
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

# -----------------------------------------------------------------
# --- FUNGSI UNTUK OPSI 1 (LOGIN) ---
# -----------------------------------------------------------------
async def login_account(account):
    """
    Login menggunakan alur baru: Turnstile -> reCAPTCHA
    (Dipanggil oleh Opsi 1)
    """
    email = account['email']
    password = account['password']
    console.print(f"\n[bold yellow]--- Mencoba Login Akun: {email} ---[/bold yellow]")

    is_headless = config.HEADLESS_MODE
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
            
            # 3. Navigasi ke Halaman Login
            console.print("Membuka halaman login...")
            await page.goto(constants.LOGIN_URL, timeout=90000, wait_until="domcontentloaded")
            
            # 4. (BARU) Cek Halaman Challenge
            content = await page.content()
            if "Just a moment" in content or "Verify you are human" in content:
                console.print("[yellow]Mendeteksi Cloudflare Turnstile Challenge...[/yellow]")
                
                # Panggil solver Turnstile
                turnstile_token = await captcha_solver.solve_turnstile_async(constants.LOGIN_URL, proxy_settings)
                if not turnstile_token:
                    raise Exception("Gagal menyelesaikan Turnstile")
                
                # Suntikkan token Turnstile
                try:
                    # Temukan elemen input tersembunyi Turnstile
                    response_element = page.locator('[name="cf-turnstile-response"]')
                    await response_element.evaluate(f"(el, token) => el.value = token", turnstile_token)
                    console.print("[green]Token Turnstile disuntikkan. Menunggu redirect...[/green]")
                    
                    # Beri waktu 5 detik bagi skrip Turnstile untuk memverifikasi dan mengirim
                    await page.wait_for_timeout(5000) 
                    
                except Exception as e:
                    console.print(f"[red]Gagal menyuntikkan token Turnstile: {e}[/red]")
                    pass
            
            # 5. Tunggu Form Login (Setelah Turnstile)
            console.print("Menunggu form login muncul...")
            await page.wait_for_selector('input[name="username"]', timeout=90000)
            console.print("[green]Form login terdeteksi.[/green]")
            
            # 6. Ambil KEDUA Token CSRF
            console.print("Mengambil token CSRF...")
            csrf_token_element = page.locator('input[name="token"]').first
            csrf_token = await csrf_token_element.get_attribute('value')
            
            csrf_name_element = page.locator('input[name="csrf_test_name"]').first
            csrf_name_token = await csrf_name_element.get_attribute('value')
            
            if not csrf_token or not csrf_name_token:
                raise Exception("Gagal menemukan semua token CSRF")
                
            console.print(f"[green]Token 1 (token) didapat: {csrf_token[:10]}...[/green]")
            console.print(f"[green]Token 2 (csrf_test_name) didapat: {csrf_name_token[:10]}...[/green]")

            # 7. Selesaikan reCAPTCHA
            console.print("Memulai penyelesaian reCAPTCHA...")
            captcha_token = await captcha_solver.solve_recaptcha_v2(constants.LOGIN_URL, proxy_settings)
            if not captcha_token:
                raise Exception("Gagal mendapatkan token reCAPTCHA")

            console.print("[green]Token reCAPTCHA didapat.[/green] Mengisi form...")
            
            # 8. Isi Form
            await page.fill('input[name="username"]', email)
            await page.fill('input[name="password"]', password)

            # 9. Suntikkan SEMUA token
            await page.evaluate(f"""document.getElementById('g-recaptcha-response').value = '{captcha_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="token"]').value = '{csrf_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="csrf_test_name"]').value = '{csrf_name_token}';""")

            # 10. Klik Tombol Login
            console.print("Mengklik tombol login...")
            await page.click('button[type="submit"]')
            
            # 11. Tunggu Hasil
            console.print("Menunggu hasil login...")
            try:
                await page.wait_for_url(lambda url: constants.PROFILE_URL in url, timeout=20000)
            except Exception:
                console.print(f"[bold red]GAGAL LOGIN: {email}[/bold red]")
                return False

            # 12. Sukses
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

# -----------------------------------------------------------------
# --- FUNGSI UNTUK OPSI 7 (CEK COOKIE) ---
# -----------------------------------------------------------------
async def check_cookie_validity(account):
    """
    Mengecek apakah cookie yang tersimpan masih valid.
    (Dipanggil oleh Opsi 7)
    """
    email = account['email']
    console.print(f"\n[cyan]Mengecek status cookie untuk: {email}...[/cyan]")

    storage_state_path = os.path.join(STORAGE_STATE_DIR, f"state_{email.replace('@', '_').replace('.', '_')}.json")
    if not os.path.exists(storage_state_path):
        console.print(f"[bold red]HASIL: KEDALUWARSA (File cookie tidak ditemukan)[/bold red]")
        return False

    is_headless = config.HEADLESS_MODE
    browser = None

    proxy_settings = None
    if config.USE_PROXY:
        if config.PROXY_HOST:
            proxy_settings = {
                "server": f"http://{config.PROXY_HOST}:{config.PROXY_PORT}",
                "username": config.PROXY_USER, "password": config.PROXY_PASS
            }
        else:
            console.print("[yellow]Peringatan: Cek cookie tanpa proxy.[/yellow]")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=is_headless,
                proxy=proxy_settings,
                channel="chrome" 
            )
            
            context = await browser.new_context(
                no_viewport=True,
                storage_state=storage_state_path 
            )
            page = await context.new_page()

            # Coba kunjungi /login, tunggu redirect
            await page.goto(constants.LOGIN_URL, timeout=30000, wait_until="domcontentloaded")
            
            # Cek hasilnya
            if "login" in page.url:
                console.print(f"[bold red]HASIL: KEDALUWARSA (Sesi habis, tetap di /login)[/bold red]")
                await browser.close()
                return False
            else:
                console.print(f"[bold green]HASIL: VALID (Berhasil redirect ke {page.url})[/bold green]")
                await browser.close()
                return True

        except Exception as e:
            console.print(f"[bold red]Error saat mengecek cookie: {str(e)}[/bold red]")
            if browser:
                await browser.close()
            return False

# -----------------------------------------------------------------
# --- FUNGSI UNTUK OPSI 3 (DAFTAR OTOMATIS) ---
# -----------------------------------------------------------------
async def login_and_register(account):
    """
    (FUNGSI MASTER) Melakukan alur Turnstile -> reCAPTCHA -> Daftar
    (Dipanggil oleh Opsi 3)
    """
    email = account['email']
    password = account['password']
    location_id = account['location_id']
    console.print(f"\n[bold purple]--- Memulai Alur Penuh: {email} ke Butik ID {location_id} ---[/bold purple]")

    is_headless = config.HEADLESS_MODE
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

    # Gunakan context manager patch_playwright
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
            
            # === BAGIAN 1: LOGIN (DENGAN TURNSTILE) ===
            console.print("Membuka halaman login...")
            await page.goto(constants.LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
            
            # (BARU) Cek Halaman Challenge
            content = await page.content()
            if "Just a moment" in content or "Verify you are human" in content:
                console.print("[yellow]Mendeteksi Cloudflare Turnstile Challenge...[/yellow]")
                
                # Panggil solver Turnstile
                turnstile_token = await captcha_solver.solve_turnstile_async(constants.LOGIN_URL, proxy_settings)
                if not turnstile_token:
                    raise Exception("Gagal menyelesaikan Turnstile")
                
                # Suntikkan token Turnstile
                try:
                    response_element = page.locator('[name="cf-turnstile-response"]')
                    await response_element.evaluate(f"(el, token) => el.value = token", turnstile_token)
                    console.print("[green]Token Turnstile disuntikkan. Menunggu redirect...[/green]")
                    await page.wait_for_timeout(5000)
                except Exception:
                    pass
            
            console.print("Menunggu form login muncul...")
            await page.wait_for_selector('input[name="username"]', timeout=90000)
            console.print("[green]Form login terdeteksi.[/green]")
            
            console.print("Mengambil token CSRF...")
            csrf_token_element = page.locator('input[name="token"]').first
            csrf_token = await csrf_token_element.get_attribute('value')
            csrf_name_element = page.locator('input[name="csrf_test_name"]').first
            csrf_name_token = await csrf_name_element.get_attribute('value')
            
            if not csrf_token or not csrf_name_token:
                raise Exception("Gagal menemukan semua token CSRF")
            
            console.print("Memulai penyelesaian CAPTCHA #1 (reCAPTCHA)...")
            captcha_token = await captcha_solver.solve_recaptcha_v2(constants.LOGIN_URL, proxy_settings)
            if not captcha_token:
                raise Exception("Gagal mendapatkan token reCAPTCHA")

            console.print("[green]Token reCAPTCHA #1 didapat.[/green] Mengisi form...")
            
            await page.fill('input[name="username"]', email)
            await page.fill('input[name="password"]', password)
            await page.evaluate(f"""document.getElementById('g-recaptcha-response').value = '{captcha_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="token"]').value = '{csrf_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="csrf_test_name"]').value = '{csrf_name_token}';""")

            console.print("Mengklik tombol login...")
            await page.click('button[type="submit"]')
            
            console.print("Menunggu hasil login...")
            try:
                await page.wait_for_url(lambda url: constants.PROFILE_URL in url, timeout=20000)
            except Exception:
                console.print(f"[bold red]GAGAL LOGIN: {email}[/bold red]")
                return False

            console.print(f"[bold green]BERHASIL LOGIN: {email}[/bold green]")
            storage_state_path = os.path.join(STORAGE_STATE_DIR, f"state_{email.replace('@', '_').replace('.', '_')}.json")
            await context.storage_state(path=storage_state_path)
            console.print(f"Status login disimpan ke {storage_state_path}")
            
            # === BAGIAN 2: DAFTAR (DALAM SESI YANG SAMA) ===
            
            console.print("Mencari dan mengklik tombol 'Menu Antrean'...")
            try:
                await page.locator('a[href="https://antrean.logammulia.com/antrian"]').first.click()
                await page.wait_for_load_state("domcontentloaded", timeout=15000)

            except Exception as e:
                console.print(f"[bold red]GAGAL: Tidak bisa mengklik 'Menu Antrean'.[/bold red] {e}")
                return False
            
            if constants.QUEUE_PAGE_URL not in page.url:
                 console.print(f"[bold red]GAGAL: Setelah klik, tidak mendarat di /antrian. URL: {page.url}[/bold red]")
                 return False
            
            console.print("[green]Berhasil menavigasi ke halaman antrean.[/green]")

            try:
                butik = next(item for item in constants.BUTIK_DATA if item["id"] == location_id)
            except StopIteration:
                console.print(f"[bold red]GAGAL: ID Butik {location_id} tidak ditemukan di constants.py[/bold red]")
                return False

            console.print(f"Target Butik: {butik['nama']}")
            
            await page.wait_for_selector('select[name="site"]')
            await page.select_option('select[name="site"]', butik['id'])
            secret_t = await page.locator('input[name="t"]').get_attribute('value')
            await page.fill('input[name="t"]', secret_t)
            await asyncio.sleep(random.uniform(0.5, 1.5))

            console.print("Mengklik 'Tampilkan Butik'...")
            async with page.expect_navigation(wait_until="domcontentloaded"):
                await page.click('form[action="https://antrean.logammulia.com/antrian"] button')
            
            console.print("Mencari slot waktu yang tersedia...")
            await page.wait_for_selector('select[name="wakda"]', timeout=30000)

            options = await page.locator('select[name="wakda"] option').all()
            
            slot_ditemukan = None
            for opt in options:
                value = await opt.get_attribute('value')
                is_disabled = await opt.is_disabled()
                text = await opt.text_content()
                
                if value and not is_disabled:
                    slot_ditemukan = value
                    console.print(f"[bold green]SLOT DITEMUKAN: {text.strip()} (Value: {slot_ditemukan})[/bold green]")
                    break 

            if slot_ditemukan:
                await page.select_option('select[name="wakda"]', slot_ditemukan)
                
                console.print("Memulai penyelesaian CAPTCHA #2 (reCAPTCHA Halaman Slot)...")
                # Kita panggil reCAPTCHA, BUKAN Turnstile
                captcha_token_2 = await captcha_solver.solve_recaptcha_v2(page.url, proxy_settings)
                if not captcha_token_2:
                    raise Exception("Gagal mendapatkan token CAPTCHA #2")
                
                console.print("[green]Token CAPTCHA #2 didapat.[/green]")
                
                token_form_2 = await page.locator('form[action*="/antrian/ambil"] input[name="token"]').get_attribute('value')
                
                await page.evaluate(f"""document.querySelector('form[action*="/antrian/ambil"] textarea[name="g-recaptcha-response"]').value = '{captcha_token_2}';""")
                await page.evaluate(f"""document.querySelector('form[action*="/antrian/ambil"] input[name="token"]').value = '{token_form_2}';""")

                
                console.print("Mengklik tombol 'Ambil Antrean'...")
                async with page.expect_navigation(wait_until="domcontentloaded"):
                    await page.click('form[action*="/antrian/ambil"] button')
                    
                console.print(f"URL Akhir: {page.url}")
                try:
                    sukses_title = await page.locator(".swal2-title").text_content(timeout=5000)
                    if "berhasil" in sukses_title.lower():
                        console.print(f"[bold green]+++ PENDAFTARAN BERHASIL UNTUK {email}! +++[/bold green]")
                        return True
                    else:
                        console.print(f"[bold red]--- PENDAFTARAN GAGAL UNTUK {email} ---[/bold red]")
                        return False
                except Exception:
                    console.print(f"[bold green]+++ PENDAFTARAN DIKIRIM UNTUK {email}! (Verifikasi manual) +++[/bold green]")
                    return True
                    
            else:
                console.print(f"[bold yellow]--- KUOTA PENUH ---[/bold yellow]")
                return False

        except Exception as e:
            console.print(f"[bold red]Terjadi error besar saat alur penuh {email}: {str(e)}[/bold red]")
            return False
        
        finally:
            if browser and not is_headless:
                 console.print("[cyan]Menutup browser dalam 10 detik...[/cyan]")
                 await asyncio.sleep(10)
            if browser:
                await browser.close()