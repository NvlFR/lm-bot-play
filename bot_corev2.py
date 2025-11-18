# Enhanced Cloudflare bypass techniques
import asyncio
import os
import random
import time
from playwright.async_api import async_playwright
from rich.console import Console

# ... (existing imports remain the same)

console = Console()

# Enhanced delays for better stealth
NAVIGATION_DELAYS = {
    'page_load': (3000, 8000),
    'after_fill': (800, 2000),
    'after_click': (1500, 4000),
    'before_submit': (3000, 6000),
    'human_pause': (10000, 20000)  # Longer pauses for CF challenges
}

async def launch_browser(headless=True):
    """
    Enhanced browser launch with more anti-detection features.
    """
    proxy_settings = {
        "server": f"http://{config.PROXY_HOST}:{config.PROXY_PORT}",
        "username": config.PROXY_USER,
        "password": config.PROXY_PASS
    } if config.PROXY_HOST else None
    
    p = await async_playwright().start()
    
    try:
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
            "--disable-session-crashed-bubble",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            "--disable-ipc-flooding-protection",
            "--disable-background-networking",
            "--disable-default-apps"
        ]
        
        browser = await p.chromium.launch(
            headless=headless,
            proxy=proxy_settings,
            channel="chrome",
            args=browser_args
        )
    except Exception as e:
        console.print(f"[bold red]ERROR: Tidak bisa meluncurkan Google Chrome.[/bold red]")
        console.print(f"Error detail: {e}")
        return None, None

    return browser, p

async def create_advanced_stealth_context(browser):
    """
    Advanced stealth context with more comprehensive bot detection avoidance.
    """
    # Create context with realistic device parameters
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=browser_config.USER_AGENT,
        device_scale_factor=1,
        is_mobile=False,
        has_touch=False,
        locale="en-US,en;q=0.9",
    )
    
    # Add advanced stealth scripts
    await context.add_init_script("""
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock chrome object realistically
        window.chrome = {
            runtime: {},
            csi: function() {},
            loadTimes: function() {}
        };
        
        // Hide plugins and mimeTypes
        const originalPlugins = Object.create(navigator.plugins.__proto__);
        const pluginArray = Object.create(PluginArray.prototype);
        Object.defineProperty(navigator, 'plugins', {
            get: () => pluginArray,
        });
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => [],
        });
        
        // Hide permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
    """)
    
    return context

async def handle_cloudflare_blocking(page):
    """
    Handle advanced Cloudflare blocking mechanisms.
    """
    try:
        # Check for Error 1020 (Access Denied)
        error_content = await page.content()
        if "Error 1020" in error_content or "access denied" in error_content.lower():
            console.print("[bold red]DETEKSI ERROR 1020: Akses ditolak oleh Cloudflare WAF![/bold red]")
            console.print("[yellow]Strategi: Menggunakan proxy berganti-ganti atau teknik lainnya[/yellow]")
            return False
            
        # Check for Attention Required page
        if "Checking your browser" in error_content or "Attention Required" in error_content:
            console.print("[yellow]Mendeteksi halaman 'Checking your browser'...[/yellow]")
            
            # Wait longer for challenge completion
            await asyncio.sleep(random.randint(15, 30))
            
            # Check again after waiting
            new_content = await page.content()
            if "Checking your browser" in new_content:
                console.print("[red]Challenge belum terselesaikan secara otomatis[/red]")
                # Try to interact with page to trigger challenge resolution
                await page.mouse.move(100, 100)
                await page.mouse.down()
                await page.mouse.move(200, 200)
                await page.mouse.up()
                await asyncio.sleep(5)
                
            return True
            
        # No blocking detected
        return True
    except Exception as e:
        console.print(f"[red]Error saat menangani Cloudflare blocking: {e}[/red]")
        return False

async def solve_cloudflare_challenge(page):
    """
    Enhanced Cloudflare challenge solver.
    """
    try:
        await page.wait_for_selector('body', timeout=15000)
        
        # Check for various Cloudflare challenge elements
        selectors = [
            '#cf-challenge-running',
            '.cf-browser-verification',
            '#challenge-form',
            '.ray-id',
            '.cf-column'
        ]
        
        challenge_found = False
        for selector in selectors:
            element = await page.query_selector(selector)
            if element:
                challenge_found = True
                console.print(f"[yellow]Mendeteksi tantangan Cloudflare dengan selector: {selector}[/yellow]")
                break
                
        if challenge_found:
            console.print("[yellow]Menunggu penyelesaian tantangan Cloudflare...[/yellow]")
            # Wait for challenge to complete automatically
            await asyncio.sleep(random.randint(15, 30))
            
            # Try to click verification button if exists
            verify_button = await page.query_selector('input[type="checkbox"]')
            if verify_button:
                console.print("[cyan]Mencoba mengklik checkbox verifikasi...[/cyan]")
                try:
                    await verify_button.click()
                    await asyncio.sleep(5)
                except:
                    pass
                    
            # Reload page to check if challenge resolved
            await page.reload()
            await page.wait_for_load_state('networkidle')
            
        return True
    except Exception as e:
        console.print(f"[red]Gagal menangani tantangan Cloudflare: {e}[/red]")
        return False

async def login_account(account):
    """
    Enhanced login with advanced Cloudflare bypass techniques.
    """
    email = account['email']
    password = account['password']
    console.print(f"\n[bold yellow]--- Mencoba Login Akun: {email} ---[/bold yellow]")

    browser = None
    playwright = None
    context = None

    try:
        # Launch browser
        browser, playwright = await launch_browser(headless=False)
        if not browser:
            return False
        
        # Create stealth context
        context = await create_advanced_stealth_context(browser)
        page = await context.new_page()
        
        # Add realistic browser fingerprints
        await page.add_init_script("""
            // Enhance navigator properties
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
        """)
        
        # Visit a few pages to build realistic browsing history
        console.print("Memulai sesi penjelajahan...")
        await page.goto("https://www.google.com", timeout=60000)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(random.randint(2, 5))
        
        # Search for target domain
        await page.fill('textarea[name="q"]', constants.BASE_URL.replace("https://", "").replace("http://", ""))
        await page.keyboard.press("Enter")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(random.randint(3, 7))
        
        # Click on the site link
        try:
            await page.click(f'a[href*="{constants.BASE_URL.replace("https://", "").replace("http://", "")}"]')
            await page.wait_for_load_state('networkidle')
        except:
            # If direct click fails, go directly to the site
            await page.goto(constants.BASE_URL, timeout=60000)
            await page.wait_for_load_state('networkidle')
            
        await asyncio.sleep(random.randint(3, 8))
        
        # Handle Cloudflare protections
        if not await handle_cloudflare_blocking(page):
            return False
            
        # Solve Cloudflare challenges
        if not await solve_cloudflare_challenge(page):
            return False

        # Navigate to login page
        console.print("Membuka halaman login...")
        await page.goto(constants.LOGIN_URL, timeout=60000)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(random.randint(3, 6))
        
        # Handle protections again after navigation
        if not await handle_cloudflare_blocking(page):
            return False
            
        # Wait for login form
        console.print("Menunggu form login muncul...")
        await page.wait_for_selector('input[name="username"]', timeout=60000)
        console.print("[green]Form login terdeteksi.[/green]")
        await asyncio.sleep(random.randint(1, 3))

        # CAPTCHA handling
        console.print("Memulai penyelesaian CAPTCHA...")
        # Note: Make sure your CAPTCHA solver is working correctly
        # For strict Cloudflare sites, consider using a service like 2Captcha
        
        # For demonstration purposes, we'll add a placeholder
        # In practice, you'd integrate with a real CAPTCHA solving service
        captcha_token = captcha_solver.solve_recaptcha_v2() if hasattr(captcha_solver, 'solve_recaptcha_v2') else None

        if not captcha_token:
            console.print(f"[bold red]Gagal mendapatkan token CAPTCHA untuk {email}. Login dibatalkan.[/bold red]")
            # Consider manual CAPTCHA solving for strict protections
            console.print("[yellow]Petunjuk: Buka browser secara manual untuk menyelesaikan CAPTCHA[/yellow]")
            return False

        console.print("[green]Token CAPTCHA didapat.[/green] Mengisi form...")
        
        # Fill login form with human-like behavior
        await page.fill('input[name="username"]', email)
        await asyncio.sleep(random.uniform(0.5, 2))
        await page.fill('input[name="password"]', password)
        await asyncio.sleep(random.uniform(0.5, 2))

        # Inject CAPTCHA token
        await page.evaluate(
            f"""document.getElementById('g-recaptcha-response').value = '{captcha_token}';"""
        )

        # Try to check "Remember me"
        try:
            await page.check('input[name="rememberMe"]')
            console.print("Mencentang 'Remember Me'...")
        except Exception as e:
            console.print(f"[yellow]Peringatan: Gagal mencentang 'Remember Me': {e}[/yellow]")

        # Human-like scroll and interaction
        await page.evaluate("""() => {
            window.scrollTo(0, document.body.scrollHeight);
        }""")
        await asyncio.sleep(random.uniform(1, 3))
        
        await page.evaluate("""() => {
            document.querySelector('button[type="submit"]').scrollIntoView();
        }""")
        await asyncio.sleep(random.uniform(2, 5))

        # Click login button
        console.print("Mengklik tombol login...")
        await page.click('button[type="submit"]')
        
        console.print("Menunggu hasil login...")
        try:
            await page.wait_for_url(
                lambda url: constants.PROFILE_URL in url, 
                timeout=20000
            )
        except Exception:
            console.print(f"[bold red]GAGAL LOGIN: {email}[/bold red]")
            console.print(f"URL saat ini: {page.url}")
            
            # Check for errors
            try:
                error_title = await page.locator(".swal2-title").text_content(timeout=3000)
                error_body = await page.locator(".swal2-html-container").text_content(timeout=3000)
                console.print(f"[bold yellow]Pesan Error: {error_title.strip()} - {error_body.strip()}[/yellow]")
            except:
                content = await page.content()
                if "Error 1020" in content:
                    console.print("[bold red]TERDETEKSI: Cloudflare WAF Error 1020 (Access Denied)[/bold red]")
                    console.print("[yellow]Saran: Gunakan proxy berkualitas tinggi atau ganti IP[/yellow]")
                elif "blocked" in content.lower():
                    console.print("[bold red]TERDETEKSI: Akses diblokir[/bold red]")
                    
            return False

        # Success
        console.print(f"[bold green]BERHASIL LOGIN: {email}[/bold green]")
        
        storage_state_path = os.path.join(STORAGE_STATE_DIR, f"state_{email.replace('@', '_').replace('.', '_')}.json")
        await context.storage_state(path=storage_state_path)
        console.print(f"Status login disimpan ke {storage_state_path}")
        return True

    except Exception as e:
        console.print(f"[bold red]Error saat login {email}: {str(e)}[/bold red]")
        return False
    
    finally:
        if browser and not config.KEEP_BROWSER_OPEN:
            await asyncio.sleep(3)
            await browser.close()
        if playwright:
            await playwright.stop()