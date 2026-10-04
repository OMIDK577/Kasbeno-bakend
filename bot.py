import os
import sqlite3
import random
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

DB = "kasbeno.db"


# ================= DATABASE =================

def db():
    return sqlite3.connect(DB)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            last_mine TEXT,
            last_wheel TEXT,
            referred_by INTEGER
        )
    """)

    con.commit()
    con.close()


def add_user(user_id, username, referred_by=None):
    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users
            (user_id, username, referred_by)
            VALUES (?, ?, ?)
        """, (user_id, username, referred_by))

        con.commit()

    con.close()


def get_user(user_id):
    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cur.fetchone()
    con.close()

    return user


# ================= MENU =================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton("⛏️ Mining", callback_data="mine"),
            InlineKeyboardButton("🎡 Lucky Wheel", callback_data="wheel")
        ],
        [
            InlineKeyboardButton("🎯 Tasks", callback_data="tasks"),
            InlineKeyboardButton("👥 Referrals", callback_data="referrals")
        ],
        [
            InlineKeyboardButton("💰 Wallet", callback_data="wallet"),
            InlineKeyboardButton("🌐 Language", callback_data="language")
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    referred_by = None

    if context.args:

        try:
            ref = int(context.args[0])

            if ref != user.id:
                referred_by = ref

        except ValueError:
            pass

    add_user(
        user.id,
        user.username or "",
        referred_by
    )

    await update.message.reply_text(
        "💰 Welcome to Kasbeno Bot!\n\n"
        "⛏️ Mine points every 24 hours\n"
        "🎡 Try the daily Lucky Wheel\n"
        "🎯 Complete tasks\n"
        "👥 Invite friends\n"
        "💰 Manage your wallet",
        reply_markup=main_menu()
    )


# ================= MINING =================

async def mining(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = get_user(user_id)

    now = datetime.utcnow()

    if user[3]:

        last_mine = datetime.fromisoformat(user[3])

        if now - last_mine < timedelta(hours=24):

            remaining = timedelta(hours=24) - (now - last_mine)

            hours = int(remaining.total_seconds() // 3600)
            minutes = int(
                (remaining.total_seconds() % 3600) // 60
            )

            await query.message.reply_text(
                f"⛏️ Mining is not ready yet.\n\n"
                f"⏳ Try again in {hours}h {minutes}m."
            )

            return

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        UPDATE users
        SET balance = balance + 10,
            last_mine = ?
        WHERE user_id = ?
        """,
        (now.isoformat(), user_id)
    )

    con.commit()
    con.close()

    await query.message.reply_text(
        "⛏️ Mining completed!\n\n"
        "🎁 You received 10 points."
    )


# ================= LUCKY WHEEL =================

async def wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = get_user(user_id)

    now = datetime.utcnow()

    if user[4]:

        last_wheel = datetime.fromisoformat(user[4])

        if now - last_wheel < timedelta(hours=24):

            remaining = timedelta(hours=24) - (now - last_wheel)

            hours = int(remaining.total_seconds() // 3600)
            minutes = int(
                (remaining.total_seconds() % 3600) // 60
            )

            await query.message.reply_text(
                f"🎡 You already used the wheel today.\n\n"
                f"⏳ Try again in {hours}h {minutes}m."
            )

            return

    prizes = [1, 5, 10, 25, 50]
    weights = [55, 25, 12, 6, 2]

    prize = random.choices(
        prizes,
        weights=weights
    )[0]

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        UPDATE users
        SET balance = balance + ?,
            last_wheel = ?
        WHERE user_id = ?
        """,
        (prize, now.isoformat(), user_id)
    )

    con.commit()
    con.close()

    await query.message.reply_text(
        f"🎡 Lucky Wheel!\n\n"
        f"🎁 You won {prize} points!"
    )


# ================= WALLET =================

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    await query.message.reply_text(
        f"💰 Your Wallet\n\n"
        f"💵 Balance: {user[2]} points\n\n"
        "💳 Withdrawals will be enabled after "
        "the payment system is connected."
    )


# ================= REFERRALS =================

async def referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bot_username = context.bot.username

    referral_link = (
        f"https://t.me/{bot_username}?start={user_id}"
    )

    await query.message.reply_text(
        "👥 Referral System\n\n"
        "Invite your friends and earn rewards!\n\n"
        f"🔗 Your referral link:\n{referral_link}"
    )


# ================= TASKS =================

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🎯 Tasks\n\n"
        "No tasks are available yet."
    )


# ================= LANGUAGE =================

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("🇦🇫 دری", callback_data="lang_fa"),
            InlineKeyboardButton("🇦🇫 پښتو", callback_data="lang_ps")
        ],
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ]

    await query.message.reply_text(
        "🌐 Select your language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= BUTTONS =================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.data == "mine":
        await mining(update, context)

    elif query.data == "wheel":
        await wheel(update, context)

    elif query.data == "wallet":
        await wallet(update, context)

    elif query.data == "referrals":
        await referrals(update, context)

    elif query.data == "tasks":
        await tasks(update, context)

    elif query.data == "language":
        await language(update, context)

    elif query.data.startswith("lang_"):
        await query.answer("Language saved!")


# ================= MAIN =================

def main():

    if not TOKEN:
        raise ValueError("BOT_TOKEN is missing.")

    if not RENDER_URL:
        raise ValueError("RENDER_EXTERNAL_URL is missing.")

    init_db()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    webhook_url = f"{RENDER_URL}/telegram"

    print("Kasbeno Bot starting...")
    print(f"Webhook: {webhook_url}")

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "10000")),
        url_path="telegram",
        webhook_url=webhook_url
    )


if __name__ == "__main__":
    main()
