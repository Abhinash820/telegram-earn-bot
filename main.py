import asyncio
import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB_NAME = "bot.db"


def init_db():
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0,
                referred_by INTEGER DEFAULT NULL
            )
        """)


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channels", callback_data="channels")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("💰 My Wallet", callback_data="wallet")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📊 Transaction History", callback_data="history")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    with sqlite3.connect(DB_NAME) as db:
        db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user.id,),
        )

    await update.message.reply_text(
        f"Welcome {user.first_name}!\n\nEarn Club mein aapka swagat hai.",
        reply_markup=main_menu(),
    )


async def button_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "wallet":
        with sqlite3.connect(DB_NAME) as db:
            row = db.execute(
                "SELECT balance FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        balance = row[0] if row else 0
        text = f"💰 Aapka balance: ₹{balance:.2f}"

    elif query.data == "channels":
        text = "📢 Channel tasks abhi admin panel se configure karne hain."

    elif query.data == "daily":
        text = "🎁 Daily bonus system agle step mein activate hoga."

    elif query.data == "refer":
        bot_username = context.bot.username
        text = (
            f"👥 Apna referral link:\n"
            f"https://t.me/{bot_username}?start={user_id}"
        )

    elif query.data == "withdraw":
        text = "💸 Withdrawal system configure hone ke baad available hoga."

    elif query.data == "history":
        text = "📊 Transaction history abhi configure nahi hui hai."

    else:
        text = "🆘 Help ke liye admin se sampark karein."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
    ])

    if query.data == "home":
        await query.edit_message_text(
            "🏠 Earn Club Main Menu",
            reply_markup=main_menu(),
        )
    else:
        await query.edit_message_text(text, reply_markup=keyboard)


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        await update.message.reply_text("⛔ Access denied.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Total Users", callback_data="admin_users")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ])

    await update.message.reply_text(
        "👑 Admin Panel\n\nWelcome, Admin!",
        reply_markup=keyboard,
    )


async def admin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID or ADMIN_ID == 0:
        await query.edit_message_text("⛔ Access denied.")
        return

    if query.data == "admin_users":
        with sqlite3.connect(DB_NAME) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

        await query.edit_message_text(f"📊 Total users: {count}")


def main():
    asyncio.set_event_loop(asyncio.new_event_loop())
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(
        admin_callback,
        pattern=r"^admin_",
    ))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main() 
