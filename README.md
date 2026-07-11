# 🤖 Aslam English Service — Telegram Storefront Bot

Bot katalog jasa English via Telegram. Fitur: katalog bernomor, pagination,
detail produk, alur order, pembayaran QRIS, dan notifikasi order ke admin.

Wujud & alurnya mirip bot storefront pada umumnya, tapi isinya **jasa English
punya kamu sendiri** — halal, sustainable, dan sekaligus jadi portfolio automation.

---

## 📁 Isi Project

| File | Fungsi |
|---|---|
| `bot.py` | Kode utama bot (jangan diedit kalau belum paham) |
| `config.py` | **EDIT DI SINI** — daftar jasa, harga, admin, QRIS |
| `requirements.txt` | Daftar library |
| `Procfile` | Perintah start buat hosting |
| `.env.example` | Contoh setting token |
| `qris.jpg` | (opsional) taruh gambar QRIS kamu di sini |

---

## 🚀 CARA JALANIN (3 Tahap)

### TAHAP 1 — Dapetin Token Bot (2 menit)

1. Buka Telegram, chat **@BotFather**
2. Ketik `/newbot`
3. Kasih nama bot (mis. `Aslam English Service`)
4. Kasih username (harus diakhiri `bot`, mis. `aslam_english_bot`)
5. BotFather kasih **token** — bentuknya kayak `123456:ABC-xyz...`
6. **SIMPAN token itu**, jangan kasih ke siapa-siapa.

### TAHAP 2 — Dapetin User ID kamu (buat notif admin)

1. Chat **@userinfobot** di Telegram
2. Dia bakal kasih **user ID** kamu (angka, mis. `123456789`)
3. Buka `config.py`, ganti baris:
   ```python
   ADMIN_IDS = [123456789]   # <-- ganti dengan ID kamu
   ADMIN_USERNAME = "aicelamm"  # <-- username kamu (tanpa @)
   ```

### TAHAP 3 — Deploy ke Cloud (biar 24/7, laptop bebas)

**Opsi A — Railway (paling gampang, rekomendasi):**

1. Bikin akun di [railway.com](https://railway.com) (login pakai GitHub)
2. Upload folder ini ke GitHub (bikin repo baru → upload semua file)
3. Di Railway: **New Project → Deploy from GitHub repo** → pilih repo bot ini
4. Masuk tab **Variables**, tambahin:
   - Key: `BOT_TOKEN`
   - Value: token dari BotFather
5. Railway auto-deploy. Cek tab **Deployments** → kalau ada tulisan
   "Bot jalan..." berarti sukses! 🎉
6. Buka botmu di Telegram, ketik `/start` — katalog muncul.

**Opsi B — Render (alternatif):**

1. Bikin akun di [render.com](https://render.com)
2. **New → Background Worker** → connect repo GitHub
3. Start command: `python bot.py`
4. Tambahin Environment Variable `BOT_TOKEN` = token kamu
5. Deploy.

> ⚠️ Catatan: free tier Render bisa "tidur" kalau idle. Railway lebih stabil buat awal.

---

## 🧪 Tes Lokal Dulu (opsional, di laptop)

Kalau mau coba di laptop sebelum deploy:

```bash
cd lam_english_bot
python3 -m venv venv
source venv/bin/activate          # Mac/Linux
pip install -r requirements.txt
export BOT_TOKEN="token_dari_botfather"
python bot.py
```

Buka bot di Telegram, ketik `/start`. Ctrl+C buat stop.

---

## ✏️ Cara Edit Jasa/Harga

Buka `config.py`, edit list `PRODUCTS`. Contoh nambah jasa:

```python
{
    "id": "ielts_prep",              # kode unik
    "name": "Paket IELTS Prep (8x sesi)",
    "price": 500000,
    "desc": "Persiapan IELTS intensif target band 7+.",
},
```

Simpan → commit ke GitHub → Railway auto-update. Selesai.

---

## 💳 Setup QRIS

1. Screenshot / download gambar QRIS kamu (dari DANA/GoPay/dll)
2. Rename jadi `qris.jpg`
3. Taruh di folder project ini
4. Upload ke GitHub (hapus `qris.jpg` dari `.gitignore` dulu kalau mau ke-upload)

Kalau nggak pasang QRIS, bot tetap jalan — cuma nampilin teks info bayar aja.

---

## 🔒 Keamanan

- **Jangan pernah** commit token asli ke GitHub. Selalu lewat Variables/Environment.
- Token bocor? Chat @BotFather → `/revoke` → dapet token baru.

---

Dibangun buat Aslam Nurdin Anwar 🚀
Bisnis sendiri, income sendiri, portfolio automation naik kelas.
