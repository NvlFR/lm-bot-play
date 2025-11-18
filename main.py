# File: main.py (Versi FINAL - dengan Opsi 8)
import os
import asyncio 
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, IntPrompt

# Impor dari file kita yang lain
import constants
import account_manager
import bot_core 
import config # <-- KITA PERLU IMPOR CONFIG SEKARANG

# Inisialisasi console 'rich'
console = Console()

def clear_screen():
    """Membersihkan layar terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_main_menu():
    """Menampilkan menu utama."""
    clear_screen()
    console.print(Panel("WAR BOT V2 - KEBAL CLOUDFLARE - SEMUA FITUR AKTIF", style="bold white on black", expand=False))
    
    # (BARU) Tampilkan status headless saat ini
    status_headless = "[bold green]Headless (Cepat)[/bold green]" if config.HEADLESS_MODE else "[bold red]Tampak (Debug)[/bold red]"
    
    menu_text = Text()
    menu_text.append("1. Login (Refresh Cookies)\n") 
    menu_text.append("2. Cek Kuota & Restok (Belum Ada)\n")
    menu_text.append("3. Daftar Antrean Otomatis\n")
    menu_text.append("4. Tambah Akun\n")
    menu_text.append("5. Monitor Otomatis (Belum Ada)\n")
    menu_text.append("6. Cek & Hapus Akun\n")
    menu_text.append("7. Cek Status Cookie\n") 
    menu_text.append(f"8. Ganti Mode (Saat ini: {status_headless})\n") # <-- MENU BARU
    menu_text.append("0. Keluar")

    console.print(Panel(menu_text, title="WAR BOT V2 - FULL FEATURE", style="bold green", expand=False))

def menu_tambah_akun():
    """Handler untuk fitur Tambah Akun."""
    clear_screen()
    console.print(Panel("TAMBAH AKUN", style="bold green", expand=False))
    
    console.print("\n[bold]Daftar Lokasi Butik:[/bold]")
    
    valid_choices = []
    location_map = {} 
    
    for butik in constants.BUTIK_DATA:
        console.print(f"{butik['id']}. {butik['nama']}")
        valid_choices.append(butik['id'])
        location_map[butik['id']] = butik['nama']

    location_id_str = Prompt.ask(
        "\nPilih ID Butik", 
        choices=valid_choices, 
        show_choices=False
    )
    
    location_name = location_map[location_id_str]
            
    console.print(f"Lokasi dipilih: [bold yellow]{location_name}[/bold yellow]")
    
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True)
    
    account_manager.add_account(email, password, location_id_str, location_name)
    input("\nAkun berhasil ditambah. Tekan Enter untuk kembali ke menu...")

def menu_cek_hapus_akun():
    """Handler untuk fitur Cek & Hapus Akun."""
    clear_screen()
    console.print(Panel("CEK & HAPUS AKUN", style="bold yellow", expand=False))
    
    accounts = account_manager.get_all_accounts()
    
    if not accounts:
        console.print("\n[bold red]Belum ada akun tersimpan.[/bold red]")
        input("\nTekan Enter untuk kembali ke menu...")
        return

    table = Table(title="Daftar Akun Tersimpan")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Email", style="magenta")
    table.add_column("Password", style="dim")
    table.add_column("Lokasi", style="green")
    
    for acc in accounts:
        pass_display = acc['password'][:3] + '*' * (len(acc['password']) - 3)
        loc_id = acc.get('location_id', '?')
        loc_name = acc.get('location_name', 'Tidak Diketahui')
        
        table.add_row(
            str(acc['id']), 
            acc['email'], 
            pass_display, 
            f"({loc_id}) {loc_name}"
        )
        
    console.print(table)
    
    console.print("\nKetik [bold]'hapus <ID>'[/bold] untuk menghapus akun (Contoh: hapus 1)")
    console.print("Ketik [bold]'batal'[/bold] untuk kembali.")
    
    choice = Prompt.ask("Pilihan")
    
    if choice.lower() == 'batal':
        return
        
    if choice.lower().startswith('hapus '):
        try:
            account_id_to_delete = int(choice.split()[1])
            account_manager.delete_account(account_id_to_delete)
        except (IndexError, ValueError):
            console.print("[bold red]Format salah. Contoh: hapus 1[/bold red]")
            
    input("\nTekan Enter untuk kembali ke menu...")

# --------------------------------------------------
# --- FUNGSI ASYNC ---
# --------------------------------------------------

async def menu_login_semua():
    """
    (Opsi 1) Menjalankan fungsi login dari bot_core untuk semua akun.
    """
    clear_screen()
    console.print(Panel("LOGIN (REFRESH COOKIE)", style="bold blue", expand=False))
    
    accounts = account_manager.get_all_accounts()
    if not accounts:
        console.print("\n[bold red]Tidak ada akun.[/bold red] Silakan 'Tambah Akun' dulu.")
        return

    console.print(f"Akan me-refresh cookie untuk {len(accounts)} akun...")
    
    sukses_count = 0
    gagal_count = 0
    
    for account in accounts:
        sukses = await bot_core.login_account(account)
        if sukses:
            sukses_count += 1
        else:
            gagal_count += 1
        console.print("---" * 10) # Pemisah
        
    console.print(f"\n[bold green]Refresh Selesai.[/bold green]")
    console.print(f"Berhasil: {sukses_count} | Gagal: {gagal_count}")

async def menu_daftar_semua():
    """
    (Opsi 3) Menjalankan fungsi 'login_and_register'
    """
    clear_screen()
    console.print(Panel("DAFTAR ANTREAN OTOMATIS", style="bold magenta", expand=False))

    accounts = account_manager.get_all_accounts()
    if not accounts:
        console.print("\n[bold red]Tidak ada akun.[/bold red] Silakan 'Tambah Akun' dulu.")
        return
        
    console.print(f"Akan mencoba alur penuh (Login + Daftar) untuk {len(accounts)} akun...")

    sukses_count = 0
    gagal_count = 0

    for account in accounts:
        sukses = await bot_core.login_and_register(account)
        
        if sukses:
            sukses_count += 1
        else:
            gagal_count += 1
        console.print("---" * 10) # Pemisah
        
    console.print(f"\n[bold green]Pendaftaran Selesai.[/bold green]")
    console.print(f"Berhasil: {sukses_count} | Gagal Daftar: {gagal_count}")

async def menu_cek_cookie():
    """
    (Opsi 7) Menjalankan fungsi check_cookie_validity untuk semua akun.
    """
    clear_screen()
    console.print(Panel("CEK STATUS COOKIE", style="bold cyan", expand=False))
    
    accounts = account_manager.get_all_accounts()
    if not accounts:
        console.print("\n[bold red]Tidak ada akun.[/bold red] Silakan 'Tambah Akun' dulu.")
        return

    console.print(f"Akan mengecek status cookie untuk {len(accounts)} akun...")
    
    valid_count = 0
    expired_count = 0
    
    for account in accounts:
        valid = await bot_core.check_cookie_validity(account)
        if valid:
            valid_count += 1
        else:
            expired_count += 1
        console.print("---" * 10) # Pemisah
        
    console.print(f"\n[bold green]Pengecekan Selesai.[/bold green]")
    console.print(f"Cookie Valid: {valid_count} | Cookie Kedaluwarsa: {expired_count}")

# --------------------------------------------------
# --- FUNGSI BARU UNTUK OPSI 8 ---
# --------------------------------------------------
def menu_ganti_mode():
    """
    (FUNGSI BARU) Mengganti mode headless di config.py
    """
    clear_screen()
    console.print(Panel("GANTI MODE HEADLESS", style="bold yellow", expand=False))
    
    # Baca status saat ini
    status_sekarang = config.HEADLESS_MODE
    console.print(f"Status saat ini: {'Headless (Cepat, di Latar Belakang)' if status_sekarang else 'Tampak (Debug, Browser Terbuka)'}")
    
    # Balikkan nilainya
    config.HEADLESS_MODE = not status_sekarang
    
    status_baru = config.HEADLESS_MODE
    console.print(f"[bold green]Status berhasil diubah menjadi: {'Headless' if status_baru else 'Tampak'}[/bold green]")
    input("\nTekan Enter untuk kembali ke menu...")

# --------------------------------------------------
# --- FUNGSI MAIN ---
# --------------------------------------------------

def main():
    """Loop utama aplikasi."""
    while True:
        show_main_menu()
        pilihan = Prompt.ask("[bold]Pilih[/bold]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"]) # Pilihan 8 ditambah

        if pilihan == "1":
            asyncio.run(menu_login_semua())
            input("\nTekan Enter untuk kembali ke menu...")

        elif pilihan == "3":
            asyncio.run(menu_daftar_semua())
            input("\nTekan Enter untuk kembali ke menu...")

        elif pilihan == "4":
            menu_tambah_akun()

        elif pilihan == "6":
            menu_cek_hapus_akun()
        
        elif pilihan == "7":
            asyncio.run(menu_cek_cookie())
            input("\nTekan Enter untuk kembali ke menu...")
            
        elif pilihan == "8": # <-- KONDISI BARU
            menu_ganti_mode()
            # Tidak perlu 'input(...)' karena sudah ada di dalam fungsinya
            
        elif pilihan in ["2", "5"]:
            console.print(f"[bold yellow]Fitur '{pilihan}' belum diimplementasikan.[/bold yellow]")
            input("\nTekan Enter untuk kembali ke menu...")

        elif pilihan == "0":
            console.print("Keluar dari program. Sampai jumpa!")
            break

if __name__ == "__main__":
    main()