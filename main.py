# File: main.py
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, IntPrompt

# Impor dari file kita yang lain
import constants
import account_manager

# Inisialisasi console 'rich'
console = Console()

def clear_screen():
    """Membersihkan layar terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_main_menu():
    """Menampilkan menu utama."""
    clear_screen()
    console.print(Panel("WAR BOT V2 - KEBAL CLOUDFLARE - SEMUA FITUR AKTIF", style="bold white on black", expand=False))
    
    menu_text = Text()
    menu_text.append("1. Login Semua Akun\n")
    menu_text.append("2. Cek Kuota & Restok\n")
    menu_text.append("3. Daftar Otomatis\n")
    menu_text.append("4. Tambah Akun\n")
    menu_text.append("5. Monitor Otomatis\n")
    menu_text.append("6. Cek & Hapus Akun\n") # Menggabungkan menu dari foto
    menu_text.append("0. Keluar")

    console.print(Panel(menu_text, title="WAR BOT V2 - FULL FEATURE", style="bold green", expand=False))

def menu_tambah_akun():
    """Handler untuk fitur Tambah Akun."""
    clear_screen()
    console.print(Panel("TAMBAH AKUN", style="bold green", expand=False))
    
    # Tampilkan daftar lokasi dari BUTIK_DATA
    console.print("\n[bold]Daftar Lokasi Butik:[/bold]")
    
    # Buat daftar pilihan yang valid untuk IntPrompt
    valid_choices = []
    location_map = {} # Untuk mapping cepat ID ke nama
    
    for butik in constants.BUTIK_DATA:
        # Tampilkan ID dan Nama
        console.print(f"{butik['id']}. {butik['nama']}")
        valid_choices.append(butik['id'])
        location_map[butik['id']] = butik['nama']

    # Minta input lokasi
    # Kita pakai Prompt.ask biasa karena ID sekarang berupa string ("1", "4", "19", dll)
    location_id_str = Prompt.ask(
        "\nPilih ID Butik", 
        choices=valid_choices, 
        show_choices=False
    )
    
    # Dapatkan nama lokasi dari map
    location_name = location_map[location_id_str]
            
    console.print(f"Lokasi dipilih: [bold yellow]{location_name}[/bold yellow]")
    
    # Minta input email dan password
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True) # password=True menyembunyikan ketikan
    
    # Simpan akun
    # Kita tetap simpan ID sebagai string agar konsisten
    account_manager.add_account(email, password, location_id_str, location_name)
    input("\nTekan Enter untuk kembali ke menu...")

def menu_cek_hapus_akun():
    """Handler untuk fitur Cek & Hapus Akun."""
    clear_screen()
    console.print(Panel("CEK & HAPUS AKUN", style="bold yellow", expand=False))
    
    accounts = account_manager.get_all_accounts()
    
    if not accounts:
        console.print("\n[bold red]Belum ada akun tersimpan.[/bold red]")
        input("\nTekan Enter untuk kembali ke menu...")
        return

    # Tampilkan akun dalam tabel
    table = Table(title="Daftar Akun Tersimpan")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Email", style="magenta")
    table.add_column("Password", style="dim")
    table.add_column("Lokasi", style="green")
    
    for acc in accounts:
        # Tampilkan password sebagian (misal: 123***)
        pass_display = acc['password'][:3] + '*' * (len(acc['password']) - 3)
        # Ambil ID lokasi (kita simpan sebagai string) dan nama
        loc_id = acc.get('location_id', '?') # .get untuk keamanan jika data lama
        loc_name = acc.get('location_name', 'Tidak Diketahui')
        
        table.add_row(
            str(acc['id']), 
            acc['email'], 
            pass_display, 
            f"({loc_id}) {loc_name}" # Tampilkan ID dan Nama Lokasi
        )
        
    console.print(table)
    
    # Opsi untuk menghapus
    console.print("\nKetik [bold]'hapus <ID>'[/bold] untuk menghapus akun (Contoh: hapus 1)")
    console.print("Ketik [bold]'batal'[/bold] untuk kembali.")
    
    choice = Prompt.ask("Pilihan")
    
    if choice.lower() == 'batal':
        return
        
    if choice.lower().startswith('hapus '):
        try:
            # Ambil ID dari perintah (misal: "hapus 1" -> 1)
            account_id_to_delete = int(choice.split()[1])
            account_manager.delete_account(account_id_to_delete)
        except (IndexError, ValueError):
            console.print("[bold red]Format salah. Contoh: hapus 1[/bold red]")
            
    input("\nTekan Enter untuk kembali ke menu...")


def main():
    """Loop utama aplikasi."""
    while True:
        show_main_menu()
        pilihan = Prompt.ask("[bold]Pilih[/bold]", choices=["1", "2", "3", "4", "5", "6", "0"])

        if pilihan == "4":
            menu_tambah_akun()

        elif pilihan == "6":
            menu_cek_hapus_akun()
            
        elif pilihan in ["1", "2", "3", "5"]:
            console.print(f"[bold yellow]Fitur '{pilihan}' belum diimplementasikan.[/bold yellow]")
            input("\nTekan Enter untuk kembali ke menu...")

        elif pilihan == "0":
            console.print("Keluar dari program. Sampai jumpa!")
            break

if __name__ == "__main__":
    main()