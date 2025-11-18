# File: test_proxy_playwright.py
import asyncio
from patchright.async_api import async_playwright
from rich.console import Console
import config

console = Console()

async def check_playwright_proxy():
    """
    Mengecek apakah patchright + proxy bisa memuat halaman sederhana.
    """
    
    if not config.USE_PROXY:
        console.print("[yellow]Tes Dibatalkan:[/yellow] USE_PROXY di .env di-set ke 'false'.")
        return

    console.print("[cyan]Memulai tes Playwright (patchright) + Proxy...[/cyan]")
    
    proxy_settings = {
        "server": f"http://{config.PROXY_HOST}:{config.PROXY_PORT}",
        "username": config.PROXY_USER,
        "password": config.PROXY_PASS
    }
    console.print(f"Host: {config.PROXY_HOST}")

    test_url = "https://api.ipify.org"
    browser = None
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=False, # Kita buat False agar terlihat
                proxy=proxy_settings,
                channel="chrome"
            )
            context = await browser.new_context(no_viewport=True)
            page = await context.new_page()
            
            console.print(f"Mencoba membuka: {test_url} (Timeout 30 detik)...")
            await page.goto(test_url, timeout=30000, wait_until="networkidle")
            
            # Jika berhasil, baca IP-nya
            content = await page.content()
            # Ekstrak IP dari body
            import re
            ip_match = re.search(r'<body>(.*?)</body>', content)
            
            if ip_match:
                returned_ip = ip_match.group(1).strip()
                console.print("\n[bold green]--- TES PLAYWRIGHT BERHASIL! ---[/bold green]")
                console.print(f"IP yang dikembalikan oleh server: [bold]{returned_ip}[/bold]")
            else:
                 console.print(f"\n[bold red]--- TES GAGAL ---[/bold red]")
                 console.print("Berhasil membuka halaman, tapi tidak bisa membaca IP.")

            await asyncio.sleep(5) # Jeda untuk melihat
            await browser.close()

        except Exception as e:
            console.print(f"\n[bold red]--- TES PLAYWRIGHT GAGAL (TIMEOUT/ERROR) ---[/bold red]")
            console.print(f"Error: {e}")
            if browser:
                await browser.close()

if __name__ == "__main__":
    asyncio.run(check_playwright_proxy())