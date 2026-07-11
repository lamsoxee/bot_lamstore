#!/usr/bin/env python3
# ============================================================
#  LAM ENGLISH BOT — Storefront jasa English via Telegram
#  Fitur: katalog bernomor, pagination, detail produk,
#         alur order, pembayaran QRIS, notifikasi admin.
#  Framework: python-telegram-bot v21+ (async)
# ============================================================

import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
import db

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Ambil token dari environment variable (aman, nggak ditulis di kode) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Simpan produk yang lagi dipilih user sementara (in-memory)
# key: user_id, value: product dict
user_selection = {}


def rupiah(n: int) -> str:
    """Format angka jadi Rupiah: 65000 -> Rp65.000"""
    return "Rp" + f"{n:,}".replace(",", ".")


def welcome_text(user) -> str:
    """Bikin teks welcome screen personal + statistik REAL dari database."""
    ustats = db.get_user_stats(user.id)
    sstats = db.get_store_stats()
    uname = f"@{user.username}" if user.username else user.full_name

    return (
        f"👋 Halo, *{user.first_name}*!\n"
        f"Selamat datang di *{config.STORE_NAME}*.\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 *INFO KAMU*\n"
        f"🆔 ID : `{user.id}`\n"
        f"👤 User : {uname}\n"
        f"📚 Sesi diambil : {ustats['orders']}x\n"
        f"💰 Total belanja : {rupiah(ustats['total_spent'])}\n\n"
        f"📊 *STATISTIK TOKO*\n"
        f"📦 Jasa terjual : {sstats['total_orders']}\n"
        f"👥 Total pelanggan : {sstats['total_users']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_{config.STORE_TAGLINE}_\n\n"
        f"Silakan pilih jasa di bawah ini 👇"
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Menu tombol permanen di bawah (reply keyboard)."""
    return ReplyKeyboardMarkup(
        [
            ["🛒 List Produk", "📝 Riwayat"],
            ["🚀 Terlaris", "⭐ Top Buyer"],
            ["❓ Cara Order", "💬 Hubungi Admin"],
        ],
        resize_keyboard=True,
    )


def best_sellers_text() -> str:
    rows = db.get_best_sellers()
    if not rows:
        return "🚀 *Jasa Terlaris*\n\nBelum ada penjualan. Jadilah yang pertama! 😉"
    lines = ["🚀 *Jasa Terlaris*\n"]
    medals = ["🥇", "🥈", "🥉", "4.", "5."]
    for i, (name, jml) in enumerate(rows):
        lines.append(f"{medals[i]} {name} — terjual {jml}x")
    return "\n".join(lines)


def top_buyers_text() -> str:
    rows = db.get_top_buyers()
    if not rows:
        return "⭐ *Top Buyer*\n\nBelum ada pembeli. Slot juara masih kosong! 🏆"
    lines = ["⭐ *Top Buyer*\n"]
    medals = ["🥇", "🥈", "🥉", "4.", "5."]
    for i, (name, username, jml, total) in enumerate(rows):
        who = f"@{username}" if username else name
        lines.append(f"{medals[i]} {who} — {jml}x ({rupiah(total)})")
    return "\n".join(lines)


def history_text(user_id) -> str:
    rows = db.get_user_history(user_id)
    if not rows:
        return "📝 *Riwayat Order*\n\nKamu belum punya riwayat order. Yuk pesan jasa pertama! 🚀"
    lines = ["📝 *Riwayat Order Kamu*\n"]
    status_emoji = {"paid": "✅ Lunas", "pending": "⏳ Menunggu"}
    for name, price, status, created in rows:
        tgl = created.split(" ")[0] if created else "-"
        lines.append(f"• {name}\n  {rupiah(price)} — {status_emoji.get(status, status)} ({tgl})")
    return "\n".join(lines)


def cara_order_text() -> str:
    return (
        f"❓ *Cara Order di {config.STORE_NAME}*\n\n"
        "1️⃣ Klik *🛒 List Produk* / ketik /produk\n"
        "2️⃣ Pilih jasa yang kamu mau\n"
        "3️⃣ Klik *✅ Order Sekarang*\n"
        "4️⃣ Bayar via QRIS sesuai nominal\n"
        "5️⃣ Kirim *screenshot bukti bayar* ke chat ini\n"
        "6️⃣ Admin konfirmasi & jadwalin sesi kamu ✅\n\n"
        f"Ada kendala? Klik *💬 Hubungi Admin* atau chat @{config.ADMIN_USERNAME}"
    )


def build_catalog_keyboard(page: int) -> InlineKeyboardMarkup:
    """Bikin tombol katalog dengan pagination."""
    per_page = config.ITEMS_PER_PAGE
    products = config.PRODUCTS
    total_pages = (len(products) - 1) // per_page + 1
    page = max(0, min(page, total_pages - 1))

    start = page * per_page
    end = start + per_page
    page_products = products[start:end]

    buttons = []
    for i, p in enumerate(page_products, start=start + 1):
        label = f"{i}. {p['name']} — {rupiah(p['price'])}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"prod:{p['id']}")])

    # Baris navigasi pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Sebelumnya", callback_data=f"page:{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Berikutnya ▶️", callback_data=f"page:{page+1}"))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(buttons)


def catalog_text(page: int) -> str:
    per_page = config.ITEMS_PER_PAGE
    total_pages = (len(config.PRODUCTS) - 1) // per_page + 1
    page = max(0, min(page, total_pages - 1))
    return (
        f"🛍️ *{config.STORE_NAME}*\n"
        f"_{config.STORE_TAGLINE}_\n\n"
        f"Pilih jasa yang kamu mau di bawah ini 👇\n"
        f"_(Halaman {page+1} dari {total_pages})_"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start — register user + welcome screen saja (katalog via menu List Produk)."""
    user = update.message.from_user
    db.register_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        welcome_text(user),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def menu_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle klik tombol menu bawah (reply keyboard = pesan teks biasa)."""
    text = update.message.text
    user = update.message.from_user

    if text == "🛒 List Produk":
        await update.message.reply_text(
            catalog_text(0), reply_markup=build_catalog_keyboard(0), parse_mode="Markdown"
        )
    elif text == "📝 Riwayat":
        await update.message.reply_text(history_text(user.id), parse_mode="Markdown")
    elif text == "🚀 Terlaris":
        await update.message.reply_text(best_sellers_text(), parse_mode="Markdown")
    elif text == "⭐ Top Buyer":
        await update.message.reply_text(top_buyers_text(), parse_mode="Markdown")
    elif text == "❓ Cara Order":
        await update.message.reply_text(cara_order_text(), parse_mode="Markdown")
    elif text == "💬 Hubungi Admin":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Chat Admin", url=f"https://t.me/{config.ADMIN_USERNAME}")]
        ])
        await update.message.reply_text(
            f"Klik tombol di bawah buat chat admin, atau langsung ke @{config.ADMIN_USERNAME} 👇",
            reply_markup=kb,
        )
    else:
        # Teks lain yang bukan tombol → arahkan ke menu
        await update.message.reply_text(
            "Pilih menu di bawah ya, atau ketik /start buat lihat katalog 😉",
            reply_markup=main_menu_keyboard(),
        )


async def show_catalog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /produk — sama kayak start."""
    await update.message.reply_text(
        catalog_text(0),
        reply_markup=build_catalog_keyboard(0),
        parse_mode="Markdown",
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle semua klik tombol inline."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- Navigasi halaman ---
    if data.startswith("page:"):
        page = int(data.split(":")[1])
        await query.edit_message_text(
            catalog_text(page),
            reply_markup=build_catalog_keyboard(page),
            parse_mode="Markdown",
        )
        return

    # --- Tombol dummy (nomor halaman) ---
    if data == "noop":
        return

    # --- Pilih produk → tampilkan detail ---
    if data.startswith("prod:"):
        pid = data.split(":", 1)[1]
        product = next((p for p in config.PRODUCTS if p["id"] == pid), None)
        if not product:
            await query.edit_message_text("❌ Produk tidak ditemukan.")
            return

        text = (
            f"📦 *{product['name']}*\n\n"
            f"{product['desc']}\n\n"
            f"💰 Harga: *{rupiah(product['price'])}*\n"
            f"📦 Stok ready: {db.get_available_stock_count(product['id'])}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Order Sekarang", callback_data=f"order:{pid}")],
            [InlineKeyboardButton("◀️ Kembali ke Katalog", callback_data="page:0")],
        ])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # --- Order → tampilkan info pembayaran ---
    if data.startswith("order:"):
        pid = data.split(":", 1)[1]
        product = next((p for p in config.PRODUCTS if p["id"] == pid), None)
        if not product:
            await query.edit_message_text("❌ Produk tidak ditemukan.")
            return

        user = query.from_user
        user_selection[user.id] = product

        # Catat order ke database (status pending) + register user
        db.register_user(user.id, user.username, user.full_name)
        order_id = db.add_order(user.id, product["id"], product["name"], product["price"])

        text = (
            f"🧾 *Ringkasan Order*\n\n"
            f"Jasa: {product['name']}\n"
            f"Total: *{rupiah(product['price'])}*\n\n"
            f"{config.PAYMENT_NOTE}"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Hubungi Admin", url=f"https://t.me/{config.ADMIN_USERNAME}")],
            [InlineKeyboardButton("◀️ Kembali ke Katalog", callback_data="page:0")],
        ])

        # Kirim gambar QRIS kalau ada filenya
        qris_path = config.QRIS_IMAGE
        if qris_path and os.path.exists(qris_path):
            await query.message.reply_photo(
                photo=open(qris_path, "rb"),
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await query.answer()
        else:
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

        # Notifikasi ke admin bahwa ada order masuk
        admin_msg = (
            f"🔔 *ORDER BARU MASUK* (#{order_id})\n\n"
            f"👤 Dari: {user.full_name}"
            + (f" (@{user.username})" if user.username else "")
            + f"\n🆔 User ID: `{user.id}`\n"
            f"📦 Jasa: {product['name']}\n"
            f"💰 Harga: {rupiah(product['price'])}\n\n"
            f"_Menunggu bukti pembayaran dari pelanggan._"
        )
        admin_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tandai LUNAS", callback_data=f"paid:{order_id}")],
        ])
        for admin_id in config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id, admin_msg, parse_mode="Markdown", reply_markup=admin_kb
                )
            except Exception as e:
                logger.warning(f"Gagal kirim notif ke admin {admin_id}: {e}")
        return

    # --- Admin tandai order lunas → auto-drop akun ke buyer ---
    if data.startswith("paid:"):
        if query.from_user.id not in config.ADMIN_IDS:
            await query.answer("Cuma admin yang bisa.", show_alert=True)
            return
        order_id = int(data.split(":")[1])
        order = db.get_order(order_id)
        if not order:
            await query.answer("Order tidak ditemukan.", show_alert=True)
            return

        # Tarik 1 akun dari stok
        cred = db.pop_stock(order["product_id"])
        db.mark_paid(order_id)

        if cred is None:
            await query.edit_message_text(
                query.message.text_markdown
                + "\n\n⚠️ *LUNAS, TAPI STOK HABIS* — admin harus drop manual.",
                parse_mode="Markdown",
            )
            await context.bot.send_message(
                order["user_id"],
                "✅ Pembayaran kamu sudah kami terima!\n"
                "Mohon maaf, stok akun sedang kosong. Admin akan mengirimkan "
                "akun kamu maksimal 1x24 jam. Makasih 🙏",
            )
            return

        # Kirim akun ke buyer
        await context.bot.send_message(
            order["user_id"],
            f"✅ *PEMBAYARAN LUNAS — AKUN KAMU*\n\n"
            f"📦 {order['product_name']}\n\n"
            f"🔐 *Detail Akun:*\n{cred}\n\n"
            f"_Simpan baik-baik. Jangan sebarkan ke orang lain._",
            parse_mode="Markdown",
        )
        await query.edit_message_text(
            query.message.text_markdown
            + "\n\n✅ *LUNAS — akun otomatis di-drop ke buyer*",
            parse_mode="Markdown",
        )
        return


async def add_stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /addstock <product_id> <kredensial> — inject 1 akun ke stok."""
    if update.message.from_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("Cuma admin yang bisa.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Format: /addstock <product_id> <kredensial>\n"
            "Contoh: /addstock netflix_1bulan email:xxx@x.com | pass:yyy"
        )
        return
    pid = args[0]
    cred = " ".join(args[1:])
    if not any(p["id"] == pid for p in config.PRODUCTS):
        await update.message.reply_text(f"❌ product_id '{pid}' gak ada di config.")
        return
    db.add_stock(pid, cred)
    avail = db.get_available_stock_count(pid)
    await update.message.reply_text(f"✅ Stok '{pid}' +1. Total ready: {avail}")


async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kalau user kirim foto (dianggap bukti bayar), teruskan ke admin."""
    user = update.message.from_user
    product = user_selection.get(user.id)

    caption = (
        f"💳 *BUKTI PEMBAYARAN MASUK*\n\n"
        f"👤 Dari: {user.full_name}"
        + (f" (@{user.username})" if user.username else "")
        + f"\n🆔 User ID: `{user.id}`\n"
    )
    if product:
        caption += f"📦 Jasa: {product['name']}\n💰 {rupiah(product['price'])}\n"
    caption += "\n_Silakan cek & konfirmasi ke pelanggan._"

    # Teruskan foto ke semua admin
    sent = False
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_photo(
                admin_id,
                photo=update.message.photo[-1].file_id,
                caption=caption,
                parse_mode="Markdown",
            )
            sent = True
        except Exception as e:
            logger.warning(f"Gagal teruskan bukti ke admin {admin_id}: {e}")

    if sent:
        await update.message.reply_text(
            "✅ Bukti pembayaran kamu udah diterima!\n"
            "Admin akan cek & konfirmasi maksimal 1x24 jam. Makasih ya 🙏"
        )
    else:
        await update.message.reply_text(
            "⚠️ Ada kendala kirim ke admin. Silakan hubungi admin langsung: "
            f"@{config.ADMIN_USERNAME}"
        )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"*{config.STORE_NAME}* — Bantuan\n\n"
        "/start — Lihat katalog jasa\n"
        "/produk — Lihat katalog jasa\n"
        "/help — Bantuan\n\n"
        "Cara order:\n"
        "1. Pilih jasa di katalog\n"
        "2. Klik *Order Sekarang*\n"
        "3. Bayar via QRIS\n"
        "4. Kirim screenshot bukti bayar ke chat ini\n"
        "5. Admin konfirmasi ✅",
        parse_mode="Markdown",
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN belum di-set! Set environment variable BOT_TOKEN "
            "dengan token dari @BotFather."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    db.init_db()  # siapin database (bikin tabel kalau belum ada)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("produk", show_catalog_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("addstock", add_stock_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_payment_proof))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))

    logger.info("Bot jalan... (Ctrl+C buat stop)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
