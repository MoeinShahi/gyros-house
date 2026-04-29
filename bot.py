import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ── KEEP-ALIVE WEB SERVER ────────────────────────────────
# This satisfies Render's "No open ports" requirement
app = Flask('')

@app.route('/')
def home():
    return "Gyros House Bot is Online! 🥙"

def run_web_server():
    # Render tells us which port to use via an environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ── SETTINGS ───────────────────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN")
OWNER_ID    = int(os.environ.get("OWNER_ID"))
WEB_APP_URL = os.environ.get("WEB_APP_URL")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton(
            "🥙 Étlap megnyitása",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ]]
    await update.message.reply_text(
        "🏛️ *Üdvözlünk a Gyros House-ban!*\n\n"
        "Kattints a gombra az étlap megnyitásához és rendelésed leadásához.\n"
        "_Fizetés készpénzzel az átvételkor_ 💵\n\n"
        "🚚 *A kiszállítás minden rendelésnél INGYENES!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Feldolgozza a Mini App-ból érkező megrendelést"""
    raw = update.message.web_app_data.data
    order = json.loads(raw)

    user     = order.get("user", {})
    items    = order.get("items", [])
    total    = order.get("total", 0)
    address  = order.get("address", "Nincs megadva")
    note     = order.get("note", "Nincs")
    username = user.get("username", "")
    name     = user.get("first_name", "Vendég")
    user_id  = user.get("id", "N/A")

    def fmt(p):
        return f"{int(p):,} Ft".replace(",", " ")

    # ── Visszaigazolás a vevőnek ──
    await update.message.reply_text(
        f"✅ *Rendelés visszaigazolva!*\n\n"
        f"Köszönjük, {name}! Hamarosan kiszállítjuk a rendelésedet 🛵\n"
        f"💵 Fizetés *készpénzzel* az átvételkor.\n\n"
        f"📍 *Szállítási cím:* {address}\n"
        f"🚚 *Szállítási díj: 0 Ft (Ingyenes)*",
        parse_mode="Markdown"
    )

    # ── Értesítés a tulajdonosnak ──
    items_text = "\n".join([
        f"  • {i['name']} × {i['qty']}  —  {fmt(i['price'] * i['qty'])}"
        for i in items
    ])

    owner_msg = (
        f"🆕 *ÚJ RENDELÉS!*\n\n"
        f"👤 Vevő: {name}"
        + (f" (@{username})" if username else f" (ID: {user_id})") + "\n"
        f"📍 Cím: {address}\n"
        f"📝 Megjegyzés: {note}\n\n"
        f"🛒 *Tételek:*\n{items_text}\n\n"
        f"💰 *Összesen: {fmt(total)}*\n"
        f"💵 Fizetés: Készpénz az átvételkor"
    )

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=owner_msg,
        parse_mode="Markdown"
    )

def main():
    # 1. Run the web server in the background
    Thread(target=run_web_server).start()

    # 2. Run the Telegram Bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_order))
    
    print("✅ Bot is running...")
    bot_app.run_polling()

if __name__ == "__main__":
    main()
