# File: account_manager.py
import json
import os
from config import ACCOUNTS_FILE

def get_all_accounts():
    """Membaca semua akun dari file JSON."""
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            accounts = json.load(f)
        return accounts
    except json.JSONDecodeError:
        return []

def save_all_accounts(accounts):
    """Menyimpan daftar akun kembali ke file JSON."""
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)

def add_account(email, password, location_id, location_name):
    """Menambah satu akun baru."""
    accounts = get_all_accounts()
    
    # Buat ID unik sederhana (berdasarkan nomor akun berikutnya)
    new_id = len(accounts) + 1
    
    new_account = {
        "id": new_id,
        "email": email,
        "password": password,
        "location_id": location_id,
        "location_name": location_name
    }
    
    accounts.append(new_account)
    save_all_accounts(accounts)
    print(f"Akun {email} untuk {location_name} berhasil ditambahkan.")

def delete_account(account_id):
    """Menghapus akun berdasarkan ID."""
    accounts = get_all_accounts()
    
    # Cari akun yang akan dihapus
    account_to_delete = None
    for acc in accounts:
        if acc['id'] == account_id:
            account_to_delete = acc
            break
            
    if account_to_delete:
        accounts.remove(account_to_delete)
        # Susun ulang ID setelah dihapus agar tetap urut
        for i, acc in enumerate(accounts):
            acc['id'] = i + 1
        
        save_all_accounts(accounts)
        print(f"Akun ID {account_id} ({account_to_delete['email']}) berhasil dihapus.")
        return True
    else:
        print(f"Akun dengan ID {account_id} tidak ditemukan.")
        return False