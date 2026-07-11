# ============================================================
#  KONFIGURASI BOT LAM STORE — "Lamm Store"
#  Edit bagian ini aja kalau mau ganti jasa/harga/kontak.
# ============================================================

# --- Identitas toko ---
STORE_NAME = "Lamm Store"
STORE_TAGLINE = "Premium Digital Application"

# --- Nomor admin (isi user ID Telegram kamu, integer) ---
# Cara dapetin: chat @userinfobot di Telegram, dia kasih ID kamu.
ADMIN_IDS = [931375362]  # Telegram user ID Aslam

# --- Info pembayaran QRIS ---
# Taruh nama file gambar QRIS kamu di folder ini (mis. "qris.jpg"),
# atau kosongkan ("") kalau mau kirim info transfer manual aja.
QRIS_IMAGE = "qris.jpg"           # nama file QRIS di folder project
PAYMENT_NOTE = (
    "Silakan scan QRIS di atas sesuai nominal.\n"
    "Setelah bayar, kirim *screenshot bukti transfer* ke chat ini.\n"
    "Admin akan konfirmasi & jadwalin sesi kamu maksimal 1x24 jam."
)

# --- Kontak admin (buat tombol "Hubungi Admin") ---
ADMIN_USERNAME = "lammmours"  # tanpa @, username Telegram kamu

# --- Daftar produk/jasa ---
# Tinggal tambah/hapus/edit dict di list ini.
# id  : kode unik (jangan sama)
# name: nama jasa
# price: harga (integer, rupiah)
# desc: deskripsi singkat
PRODUCTS = [
    {
        "id": "Netflix",
        "name": "Netflix Premium",
        "price": 33000,
        "desc": "Premium 30hari full garansi",
    },
    {
        "id": "youtube",
        "name": "Youtube",
        "price": 10000,
        "desc": "30hari full garansi, bisa perpanjang tiap bulan pakai akun sendiri",
    },
    {
        "id": "Capcut",
        "name": "Capcut",
        "price": 30000,
        "desc": "Akun dari penjual, full garansi",
    },
    {
        "id": "Canva",
        "name": "Canva",
        "price": 7000,
        "desc": "Pakai akun sendiri, full garansi",
    },
    {
        "id": "Gemini",
        "name": "Gemini",
        "price": 40000,
        "desc": "Gemini 18bulan",
    },
]

# --- Pengaturan tampilan ---
ITEMS_PER_PAGE = 4  # jumlah produk per halaman (untuk pagination)
