# File: bot_core.py (Versi FINAL - Perbaikan Logika Tunggu)
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
    Login menggunakan alur baru: reCAPTCHA -> Turnstile
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
            
            # 4. Tunggu Form Login
            console.print("Menunggu form login muncul...")
            await page.wait_for_selector('input[name="username"]', timeout=90000)
            console.print("[green]Form login terdeteksi.[/green]")
            
            # 5. Ambil KEDUA Token CSRF
            console.print("Mengambil token CSRF...")
            csrf_token_element = page.locator('input[name="token"]').first
            csrf_token = await csrf_token_element.get_attribute('value')
            
            csrf_name_element = page.locator('input[name="csrf_test_name"]').first
            csrf_name_token = await csrf_name_element.get_attribute('value')
            
            if not csrf_token or not csrf_name_token:
                raise Exception("Gagal menemukan semua token CSRF")
                
            console.print(f"[green]Token 1 (token) didapat: {csrf_token[:10]}...[/green]")
            console.print(f"[green]Token 2 (csrf_test_name) didapat: {csrf_name_token[:10]}...[/green]")

            # 6. Selesaikan reCAPTCHA
            console.print("Memulai penyelesaian CAPTCHA #1 (reCAPTCHA)...")
            captcha_token = await captcha_solver.solve_recaptcha_v2(constants.LOGIN_URL, None) # Pakai IP Lokal
            if not captcha_token:
                raise Exception("Gagal mendapatkan token reCAPTCHA")

            console.print("[green]Token reCAPTCHA didapat.[/green] Mengisi form...")
            
            # 7. Isi Form
            await page.fill('input[name="username"]', email)
            await page.fill('input[name="password"]', password)

            # 8. (PERBAIKAN) Suntikkan SEMUA token (menggunakan .evaluate)
            await page.evaluate(f"""document.getElementById('g-recaptcha-response').value = '{captcha_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="token"]').value = '{csrf_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="csrf_test_name"]').value = '{csrf_name_token}';""")

            # 9. Klik Tombol Login
            console.print("Mengklik tombol login...")
            await page.click('button[type="submit"]')
            
            # 10. (PERBAIKAN) Tunggu Halaman Berikutnya (Bisa Turnstile atau /users)
            console.print("Menunggu hasil login... (Mengecek Turnstile pasca-login)")
            
            try:
                # Tunggu hingga URL berubah DARI /login
                await page.wait_for_url(lambda url: url != constants.LOGIN_URL, timeout=20000)
            except Exception:
                # Jika tidak berubah, berarti password/captcha salah
                console.print(f"[bold red]GAGAL LOGIN: {email} (Halaman tidak berubah setelah login)[/bold red]")
                return False

            # 11. Cek Halaman Challenge SETELAH klik
            content = await page.content()
            if "Verify you are human" in content:
                console.print("[yellow]Mendeteksi Cloudflare Turnstile Challenge (pasca-login)...[/yellow]")
                
                # Panggil solver Turnstile
                turnstile_token = await captcha_solver.solve_turnstile_async(page.url, None) # Pakai IP Lokal
                if not turnstile_token:
                    raise Exception("Gagal menyelesaikan Turnstile")
                
                # Suntikkan token Turnstile
                try:
                    response_element = page.locator('[name="cf-turnstile-response"]')
                    await response_element.fill(turnstile_token) # .fill() OK untuk Turnstile
                    console.print("[green]Token Turnstile disuntikkan. Menunggu redirect...[/green]")
                    await page.wait_for_timeout(5000) # Beri waktu untuk submit
                except Exception as e:
                    console.print(f"[red]Gagal menyuntikkan token Turnstile: {e}[/red]")
                    pass
            
            # 12. Tunggu Hasil Akhir (kita HARUS ada di /users sekarang)
            console.print("Menunggu hasil login final...")
            try:
                await page.wait_for_url(lambda url: constants.PROFILE_URL in url, timeout=20000)
            except Exception:
                console.print(f"[bold red]GAGAL LOGIN: {email} (Gagal melewati Turnstile)[/bold red]")
                console.print(f"URL Saat Ini: {page.url}")
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
    (FUNGSI MASTER) Melakukan alur reCAPTCHA -> Turnstile -> Daftar
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
            
            # === BAGIAN 1: LOGIN (DENGAN reCAPTCHA -> TURNSTILE) ===
            console.print("Membuka halaman login...")
            await page.goto(constants.LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
            
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
            captcha_token = await captcha_solver.solve_recaptcha_v2(constants.LOGIN_URL, None) # Pakai IP Lokal
            
            if not captcha_token:
                raise Exception("Gagal mendapatkan token reCAPTCHA")

            console.print("[green]Token reCAPTCHA #1 didapat.[/green] Mengisi form...")
            
            await page.fill('input[name="username"]', email)
            await page.fill('input[name="password"]', password)
            
            # (PERBAIKAN) Gunakan .evaluate()
            await page.evaluate(f"""document.getElementById('g-recaptcha-response').value = '{captcha_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="token"]').value = '{csrf_token}';""")
            await page.evaluate(f"""document.querySelector('input[name="csrf_test_name"]').value = '{csrf_name_token}';""")

            console.print("Mengklik tombol login...")
            await page.click('button[type="submit"]')
            
            # (PERBAIKAN) Tunggu Halaman Berikutnya (Bisa Turnstile atau /users)
            console.print("Menunggu hasil login... (Mengecek Turnstile pasca-login)")
            
            try:
                # Tunggu hingga URL berubah DARI /login
                await page.wait_for_url(lambda url: url != constants.LOGIN_URL, timeout=20000)
            except Exception:
                # Jika tidak berubah, berarti password/captcha salah
                console.print(f"[bold red]GAGAL LOGIN: {email} (Halaman tidak berubah setelah login)[/bold red]")
                return False
            
            # Cek Halaman Challenge SETELAH klik
            content = await page.content()
            if "Verify you are human" in content:
                console.print("[yellow]Mendeteksi Cloudflare Turnstile Challenge (pasca-login)...[/yellow]")
                
                # Panggil solver Turnstile (TANPA PROXY)
                turnstile_token = await captcha_solver.solve_turnstile_async(page.url, None) # Pakai IP Lokal
                if not turnstile_token:
                    raise Exception("Gagal menyelesaikan Turnstile")
                
                try:
                    response_element = page.locator('[name="cf-turnstile-response"]')
                    await response_element.fill(turnstile_token) # .fill() OK untuk Turnstile
                    console.print("[green]Token Turnstile disuntikkan. Menunggu redirect...[/green]")
                    await page.wait_for_timeout(5000)
                except Exception as e:
                    console.print(f"[red]Gagal menyuntikkan token Turnstile: {e}[/red]")
                    pass
            
            # Tunggu Hasil Akhir (kita HARUS ada di /users sekarang)
            console.print("Menunggu hasil login final...")
            try:
                await page.wait_for_url(lambda url: constants.PROFILE_URL in url, timeout=20000)
            except Exception:
                console.print(f"[bold red]GAGAL LOGIN: {email} (Gagal melewati Turnstile)[/bold red]")
                console.print(f"URL Saat Ini: {page.url}")
                return False

            console.print(f"[bold green]BERHASIL LOGIN: {email}[/bold green]")
            storage_state_path = os.path.join(STORAGE_STATE_DIR, f"state_{email.replace('@', '_').replace('.', '_')}.json")
            await context.storage_state(path=storage_state_path)
            console.print(f"Status login disimpan ke {storage_state_path}")
            
            # === BAGIAN 2: DAFTAR (DALAM SESI YANG SAMA) ===
            
            console.print("Mencari dan mengklik tombol 'Menu Antrean'...")
            try:
                # Perbaikan: Gunakan selector yang lebih spesifik
                menu_button_selector = f'a.btn.btn-primary[href="{constants.QUEUE_PAGE_URL}"]'
                
                # Tunggu tombolnya sampai bisa diklik
                await page.wait_for_selector(menu_button_selector, state="visible", timeout=10000)
                
                # Klik dan TUNGGU navigasi (cara normal)
                async with page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
                    await page.locator(menu_button_selector).click()

            except Exception as e:
                console.print(f"[bold red]GAGAL: Tidak bisa mengklik 'Menu Antrean'.[/bold red] {e}")
                return False
            
            if constants.QUEUE_PAGE_URL not in page.url:
                 console.print(f"[bold red]GAGAL: Setelah klik, tidak mendarat di /antrean. URL: {page.url}[/bold red]")
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
                await page.click(f'form[action="{constants.QUEUE_PAGE_URL}"] button')
            
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
                captcha_token_2 = await captcha_solver.solve_recaptcha_v2(page.url, None) # Pakai IP Lokal
                if not captcha_token_2:
                    raise Exception("Gagal mendapatkan token CAPTCHA #2")
                
                console.print("[green]Token CAPTCHA #2 didapat.[/green]")
                
                token_form_2 = await page.locator(f'form[action*="{constants.QUEUE_SUBMIT_URL}"] input[name="token"]').get_attribute('value')
                
                # (PERBAIKAN) Gunakan .evaluate()
                await page.evaluate(f"""document.querySelector('form[action*="{constants.QUEUE_SUBMIT_URL}"] textarea[name="g-recaptcha-response"]').value = '{captcha_token_2}';""")
                await page.evaluate(f"""document.querySelector('form[action*="{constants.QUEUE_SUBMIT_URL}"] input[name="token"]').value = '{token_form_2}';""")

                
                console.print("Mengklik tombol 'Ambil Antrean'...")
                async with page.expect_navigation(wait_until="domcontentloaded"):
                    await page.click(f'form[action*="{constants.QUEUE_SUBMIT_URL}"] button')
                    
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