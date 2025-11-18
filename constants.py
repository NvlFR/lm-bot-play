# File: constants.py

# Menggabungkan daftar <option> dari HTML dengan secretMap Anda
# Ini adalah data paling penting di project ini.
BUTIK_DATA = [
    {"id": "4", "nama": "Butik Emas LM - Balikpapan", "secret": "49ab32490d01ff03d2e38394a7bb5d13632077e1c29cd159824a5d2b67068e1b"},
    {"id": "1", "nama": "Butik Emas LM - Bandung", "secret": "5804ddc239cb88c63ddc6ed95b6e7448ce429ac601105c5df02db5809c444f5a"},
    {"id": "19", "nama": "Butik Emas LM - Bekasi", "secret": "5bb290b6476d27b5dc4554d1de28afa38addcfd9d8fc8173eaee0f5e2c724be4"},
    {"id": "16", "nama": "Butik Emas LM - Bintaro", "secret": "8b908ea214ff714e044fbc6227a9075786aee1de8060887865b2cb8f1b6c7047"},
    {"id": "17", "nama": "Butik Emas LM - Bogor", "secret": "1711e9a491d316696e958951ad43095895fb4fe1aae763713fc53dde49f36c08"},
    {"id": "5", "nama": "Butik Emas LM - Denpasar", "secret": "f46dd365f97c078c96bfdbf4951fb7ba4e9d6cd19df31c036680dffacf92616c"},
    {"id": "20", "nama": "Butik Emas LM - Djuanda", "secret": "ef9355153d1dedf6ee1e196bcb5e39ac864e2cee68fa4a6d197d354a32446cfa"},
    {"id": "6", "nama": "Butik Emas LM - Gedung Antam", "secret": "2d8ab5d3e179988e9b7fc3258d6966418a6ed67b5340db39f60a58100d6cf4ca"},
    {"id": "3", "nama": "Butik Emas LM - Graha Dipta", "secret": "fff9dd3d663c298e82f80d8fd185ffc68ddad18bc448a9b633f2b3af721fc022"},
    {"id": "11", "nama": "Butik Emas LM - Makassar", "secret": "371bc0a7a08912012fccb4eacc5850f908103fef53be98d94ec10c5818521aa8"},
    {"id": "10", "nama": "Butik Emas LM - Medan", "secret": "411a97f0038d4e7dc7b883689b20dd80a99958579986c1701eefdee879c62dd2"},
    {"id": "12", "nama": "Butik Emas LM - Palembang", "secret": "42fc6d53c7fe69cf4dcc3ec7d5a247ea2532cf5800e56b3fdb4fa890594d0f4b"},
    {"id": "24", "nama": "Butik Emas LM - Pekanbaru", "secret": "010c9c769d226147f22ab019ef6e3f5b9f70c22678f62c20a08ff974cd794f87"},
    {"id": "21", "nama": "Butik Emas LM - Puri Indah", "secret": "1ca4355363523a7d6824f8aade5cbd00fec21ea1d4bc3a5cecac7485ec4e6447"},
    {"id": "15", "nama": "Butik Emas LM - Semarang", "secret": "75d3c46ddeb5f13f0aa021847f16cbad195243869b29ec47697fa3dd654cd7d8"},
    {"id": "23", "nama": "Butik Emas LM - Serpong", "secret": "cc3071cc9c96af4a81cf19cc87ed76057b964d01117a6bd87e45c1b88d9ab51f"},
    {"id": "8", "nama": "Butik Emas LM - Setiabudi One", "secret": "26f567e14b9744f50b9903be77c377a5322884d1b4a4076ccf4780b41809c28b"},
    {"id": "13", "nama": "Butik Emas LM - Surabaya 1 Darmo", "secret": "a3e63b82063ef2e3f6715d700c1de4c191abc8d97ca2da0e342e7adf6bb259e5"},
    {"id": "14", "nama": "Butik Emas LM - Surabaya 2 Pakuwon", "secret": "1a105b5a724b99400a715b6b8d043bf9f3b821c1caca1a599d3e7e1b1576b55a"},
    {"id": "9", "nama": "Butik Emas LM - Yogyakarta", "secret": "b47560b59c11452b1eaf31ecc2a32a0e2751e38b430c25a5c8eaf3a92b8bfe84"},
    # Tambahkan lokasi lain jika ada yang kurang
]

# --- Target URL dan Data Penting ---

# URL
BASE_URL = "https://antrean.logammulia.com"
HOME_URL = "https://antrean.logammulia.com/"
LOGIN_URL = f"{BASE_URL}/login"
REGISTER_URL = f"{BASE_URL}/register"
PROFILE_URL = f"{BASE_URL}/users"
QUEUE_PAGE_URL = f"{BASE_URL}/antrian"
QUEUE_SUBMIT_URL = f"{BASE_URL}/antrian/ambil"

# CAPTCHA
RECAPTCHA_SITE_KEY = "6LdxTgUsAAAAAJ80-chHLt5PiK-xv1HbLPqQ3nB4"