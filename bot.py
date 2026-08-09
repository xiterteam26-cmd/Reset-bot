import os
import sqlite3
import logging
import asyncio
import html
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# ================= CONFIGURATION =================
RESELLER_TOKEN = "8882760232:AAHnLw-hoF5lgKxkWRhbNypO8POXx9NCFhk"
LOGS_TOKEN = "8993788156:AAGO72TkJkPa5cyEN44gLQWAdvj1NEQlrqQ"
ADMIN_TOKEN = "8192870600:AAHQ91M5z2UN2MKspqK9LK3GeGr-WKUkFng"

ADMIN_CHAT_ID = 8438744876

SUPPORT_USERNAME = "SeerCheatz72"
DATABASE_FILE = "seer_store.db"

logs_bot = Bot(token=LOGS_TOKEN)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("SEER_STORE")

# ============================================================
#                        DATABASE SETUP
# ============================================================

def db():
    connection = sqlite3.connect(DATABASE_FILE, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def init_database():
    connection = db()
    cursor = connection.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS resellers (user_id INTEGER PRIMARY KEY, name TEXT NOT NULL, balance INTEGER DEFAULT 0, active INTEGER DEFAULT 1, created_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, price INTEGER NOT NULL, active INTEGER DEFAULT 1, created_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS key_pool (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER NOT NULL, key_value TEXT UNIQUE NOT NULL, is_used INTEGER DEFAULT 0, added_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, reseller_id INTEGER NOT NULL, reseller_name TEXT, mod_id INTEGER NOT NULL, mod_name TEXT NOT NULL, key_value TEXT UNIQUE NOT NULL, price INTEGER NOT NULL, created_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS system_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL)")

    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('admin_chat_id', ?)", (str(ADMIN_CHAT_ID),))
    cursor.execute("INSERT OR IGNORE INTO resellers (user_id, name, balance, active, created_at) VALUES (?, ?, ?, ?, ?)", (ADMIN_CHAT_ID, "Owner Admin", 999999, 1, now()))

    connection.commit()
    connection.close()

def get_admin_id():
    connection = db()
    row = connection.execute("SELECT value FROM config WHERE key = 'admin_chat_id'").fetchone()
    connection.close()
    return int(row["value"]) if row else ADMIN_CHAT_ID

def set_admin_id(new_id):
    connection = db()
    connection.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('admin_chat_id', ?)", (str(new_id),))
    connection.commit()
    connection.close()

def get_stock_count(mod_id):
    connection = db()
    count = connection.execute("SELECT COUNT(*) FROM key_pool WHERE mod_id = ? AND is_used = 0", (mod_id,)).fetchone()[0]
    connection.close()
    return count

def add_log(event_type, message):
    connection = db()
    connection.execute("INSERT INTO system_logs (event_type, message, created_at) VALUES (?, ?, ?)", (event_type, message, now()))
    connection.commit()
    connection.close()

# ============================================================
# 👑 ADMIN PANEL UI & HANDLERS
# ============================================================

def get_admin_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Mod & Price", callback_data="adm_guide_mod"),
         InlineKeyboardButton("🗑️ Delete Mod", callback_data="adm_guide_delmod")],
        [InlineKeyboardButton("🔑 Add Key Stock", callback_data="adm_guide_addkey"),
         InlineKeyboardButton("💰 Top-Up Balance", callback_data="adm_guide_bal")],
        [InlineKeyboardButton("👤 Register Reseller", callback_data="adm_guide_res"),
         InlineKeyboardButton("🆔 Change Admin Chat ID", callback_data="adm_guide_id")],
        [InlineKeyboardButton("📜 Master Logs", callback_data="adm_view_all_logs"),
         InlineKeyboardButton("📊 System Overview", callback_data="adm_stats")]
    ])

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != get_admin_id():
        return

    await update.message.reply_text(
        "👑 **SEER STORE — MASTER ADMIN CONTROL PANEL** 👑\n\n"
        "Welcome Admin! Control reseller activities, mod prices, key stocks, and settings from here:",
        reply_markup=get_admin_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != get_admin_id():
        return
    await query.answer()

    data = query.data

    if data == "adm_home":
        await query.edit_message_text(
            "👑 **SEER STORE — MASTER ADMIN CONTROL PANEL** 👑\n\nSelect an operation to perform:",
            reply_markup=get_admin_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "adm_stats":
        connection = db()
        res_count = connection.execute("SELECT COUNT(*) FROM resellers WHERE active = 1").fetchone()[0]
        mod_count = connection.execute("SELECT COUNT(*) FROM mods WHERE active = 1").fetchone()[0]
        keys_sold = connection.execute("SELECT COUNT(*) FROM keys").fetchone()[0]
        keys_stock = connection.execute("SELECT COUNT(*) FROM key_pool WHERE is_used = 0").fetchone()[0]
        connection.close()

        msg = (
            "📊 **SYSTEM OVERVIEW & STATS**\n\n"
            f"👤 **Registered Resellers:** `{res_count}`\n"
            f"🎮 **Active Mod Items:** `{mod_count}`\n"
            f"📦 **Available Stock Keys:** `{keys_stock}`\n"
            f"🔑 **Total Keys Sold:** `{keys_sold}`\n"
            f"👑 **Current Admin Chat ID:** `{get_admin_id()}`"
        )
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "adm_view_all_logs":
        connection = db()
        logs = connection.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 10").fetchall()
        connection.close()

        if not logs:
            msg = "📜 **MASTER KEY LOGS**\n\nNo activity logged yet."
        else:
            lines = ["📜 **MASTER SYSTEM LOGS (Recent 10)**\n"]
            for l in logs:
                lines.append(f"• `[{l['event_type']}]` {l['message']}")
            msg = "\n".join(lines)

        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "adm_guide_mod":
        msg = "➕ **ADD MOD INSTRUCTIONS**\n\nSend command:\n`/addmod <Mod_Name> <Price>`\n\n*Example:* `/addmod Drip_Client_1Day 500`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "adm_guide_addkey":
        msg = "🔑 **ADD KEYS TO STOCK INSTRUCTIONS**\n\nSend command:\n`/addkey <Mod_ID> <Key1> <Key2>...`\n\n*Example:* `/addkey 1 SEER-XXXX-YYYY`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "adm_guide_delmod":
        msg = "🗑️ **DELETE MOD INSTRUCTIONS**\n\nSend command:\n`/delmod <Mod_Name>`\n\n*Example:* `/delmod Drip_Client_1Day`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "adm_guide_res":
        msg = "👤 **REGISTER RESELLER INSTRUCTIONS**\n\nSend command:\n`/addreseller <Chat_ID> <Name>`\n\n*Example:* `/addreseller 8610996167 Sulthan`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "adm_guide_bal":
        msg = "💰 **TOP-UP BALANCE INSTRUCTIONS**\n\nSend command:\n`/addbalance <Chat_ID> <Amount>`\n\n*Example:* `/addbalance 8610996167 5000`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "adm_guide_id":
        msg = f"🆔 **CHANGE ADMIN CHAT ID**\n\nCurrent ID: `{get_admin_id()}`\n\nSend command:\n`/setadminid <New_Chat_ID>`\n\n*Example:* `/setadminid 123456789`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode=ParseMode.MARKDOWN)

# Admin Commands
async def set_admin_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != get_admin_id():
        return
    try:
        new_id = int(context.args[0])
        set_admin_id(new_id)
        add_log("ADMIN", f"Admin Chat ID changed to {new_id}")
        await update.message.reply_text(f"✅ **Admin Chat ID successfully updated to:** `{new_id}`", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/setadminid New_Chat_ID`", parse_mode=ParseMode.MARKDOWN)

async def add_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != get_admin_id():
        return
    try:
        mod_name = " ".join(context.args[:-1]).replace("_", " ").strip()
        price = int(context.args[-1])
        
        connection = db()
        connection.execute("INSERT OR REPLACE INTO mods (name, price, active, created_at) VALUES (?, ?, 1, ?)", (mod_name, price, now()))
        connection.commit()
        connection.close()

        add_log("PRODUCT", f"Mod Added/Updated: {mod_name} ({price} LKR)")
        await update.message.reply_text(f"✅ **Mod Saved:** `{mod_name}` — `{price} LKR`", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/addmod Mod_Name Price`", parse_mode=ParseMode.MARKDOWN)

async def add_key_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != get_admin_id():
        return
    try:
        mod_id = int(context.args[0])
        keys_input = context.args[1:]
        
        connection = db()
        count = 0
        for k in keys_input:
            try:
                connection.execute("INSERT INTO key_pool (mod_id, key_value, is_used, added_at) VALUES (?, ?, 0, ?)", (mod_id, k, now()))
                count += 1
            except sqlite3.IntegrityError:
                pass
        connection.commit()
        connection.close()

        add_log("STOCK", f"Added {count} keys for Mod ID {mod_id}")
        await update.message.reply_text(f"✅ **Added {count} Keys to Stock for Mod ID:** `{mod_id}`", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/addkey Mod_ID Key1 Key2...`", parse_mode=ParseMode.MARKDOWN)

async def del_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != get_admin_id():
        return
    try:
        mod_name = " ".join(context.args).replace("_", " ").strip()
        connection = db()
        connection.execute("UPDATE mods SET active = 0 WHERE name = ?", (mod_name,))
        connection.commit()
        connection.close()
        
        add_log("PRODUCT", f"Mod Removed: {mod_name}")
        await update.message.reply_text(f"✅ **Mod Deactivated:** `{mod_name}`", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/delmod Mod_Name`", parse_mode=ParseMode.MARKDOWN)

async def add_reseller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != get_admin_id():
        return
    try:
        target_id = int(context.args[0])
        name = context.args[1] if len(context.args) > 1 else "Reseller"
        
        connection = db()
        connection.execute("INSERT INTO resellers (user_id, name, balance, active, created_at) VALUES (?, ?, 0, 1, ?) ON CONFLICT(user_id) DO UPDATE SET name = excluded.name, active = 1", (target_id, name, now()))
        connection.commit()
        connection.close()

        add_log("RESELLER", f"Reseller Added: {name} ({target_id})")
        await update.message.reply_text(f"✅ **Reseller Activated:** `{name}` (`{target_id}`)", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/addreseller Chat_ID Name`", parse_mode=ParseMode.MARKDOWN)

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != get_admin_id():
        return
    try:
        target_id, amount = int(context.args[0]), int(context.args[1])
        connection = db()
        reseller = connection.execute("SELECT * FROM resellers WHERE user_id = ? AND active = 1", (target_id,)).fetchone()
        
        if not reseller:
            await update.message.reply_text("❌ Reseller not found!")
            connection.close()
            return

        new_bal = reseller["balance"] + amount
        connection.execute("UPDATE resellers SET balance = ? WHERE user_id = ?", (new_bal, target_id))
        connection.commit()
        connection.close()

        add_log("WALLET", f"Added {amount} LKR to {target_id}")
        await update.message.reply_text(f"✅ **Balance Top-Up Successful!**\n\n👤 **Reseller:** `{target_id}`\n💰 **New Balance:** `{new_bal} LKR`", parse_mode=ParseMode.MARKDOWN)
        
        try:
            await context.bot.send_message(chat_id=target_id, text=f"🎉 **BALANCE TOP-UP CONFIRMED!**\n\nAdded: `+{amount} LKR`\nUpdated Wallet Balance: `{new_bal} LKR`", parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/addbalance Chat_ID Amount`", parse_mode=ParseMode.MARKDOWN)

# ============================================================
# 💎 RESELLER PANEL UI & HANDLERS
# ============================================================

def get_reseller_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Store & Purchase Keys", callback_data="res_store")],
        [InlineKeyboardButton("👤 My Wallet Profile", callback_data="res_profile"),
         InlineKeyboardButton("📜 My Keys History", callback_data="res_history")],
        [InlineKeyboardButton("💬 Admin Support", url=f"https://t.me/{SUPPORT_USERNAME}")]
    ])

async def reseller_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    connection = db()
    reseller = connection.execute("SELECT * FROM resellers WHERE user_id = ? AND active = 1", (user_id,)).fetchone()
    connection.close()

    if not reseller:
        await update.message.reply_text("🔒 **ACCESS RESTRICTED**\n\nYou are not an authorized reseller.\nContact Administrator to obtain reseller access.", parse_mode=ParseMode.MARKDOWN)
        return

    await update.message.reply_text(
        f"🔥 **WELCOME TO SEER STORE RESELLER PANEL** 🔥\n\n"
        f"👤 **Reseller:** {html.escape(reseller['name'])}\n"
        f"💰 **Wallet Balance:** `{reseller['balance']} LKR`\n\n"
        f"Choose an option from below:",
        reply_markup=get_reseller_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def reseller_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    connection = db()
    reseller = connection.execute("SELECT * FROM resellers WHERE user_id = ? AND active = 1", (user_id,)).fetchone()

    if not reseller:
        connection.close()
        await query.edit_message_text("❌ **Access Denied!**")
        return

    data = query.data

    if data == "res_home":
        await query.edit_message_text(
            f"🔥 **WELCOME TO SEER STORE RESELLER PANEL** 🔥\n\n"
            f"👤 **Reseller:** {html.escape(reseller['name'])}\n"
            f"💰 **Wallet Balance:** `{reseller['balance']} LKR`\n\n"
            f"Choose an option from below:",
            reply_markup=get_reseller_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "res_profile":
        total_keys = connection.execute("SELECT COUNT(*) FROM keys WHERE reseller_id = ?", (user_id,)).fetchone()[0]
        msg = (
            "👤 **RESELLER ACCOUNT SUMMARY**\n\n"
            f"🔹 **Account Holder:** {html.escape(reseller['name'])}\n"
            f"🔹 **Telegram ID:** `{user_id}`\n"
            f"💰 **Current Balance:** `{reseller['balance']} LKR`\n"
            f"🔑 **Total Keys Generated:** `{total_keys}`"
        )
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]]), parse_mode=ParseMode.MARKDOWN)

    elif data == "res_store":
        mods = connection.execute("SELECT * FROM mods WHERE active = 1").fetchall()

        if not mods:
            await query.edit_message_text("⚠️ **STORE OUT OF STOCK / NO MODS ADDED**\nPlease contact Admin to update mods list.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]]), parse_mode=ParseMode.MARKDOWN)
            connection.close()
            return

        keyboard = []
        for mod in mods:
            stk = get_stock_count(mod["id"])
            lbl = f"🎯 {mod['name']} — {mod['price']} LKR [{stk} Left]"
            keyboard.append([InlineKeyboardButton(lbl, callback_data=f"buy_{mod['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")])

        await query.edit_message_text("🛒 **AVAILABLE MODS & KEY GENERATOR**\n\nSelect a Mod from stock below:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("buy_"):
        mod_id = int(data.split("_")[1])
        mod = connection.execute("SELECT * FROM mods WHERE id = ? AND active = 1", (mod_id,)).fetchone()

        if not mod:
            await query.edit_message_text("❌ Mod unavailable.")
            connection.close()
            return

        stock_item = connection.execute("SELECT * FROM key_pool WHERE mod_id = ? AND is_used = 0 ORDER BY id ASC LIMIT 1", (mod_id,)).fetchone()

        if not stock_item:
            await query.edit_message_text("⚠️ **OUT OF STOCK!**\nNo available keys for this mod right now.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Store", callback_data="res_store")]]), parse_mode=ParseMode.MARKDOWN)
            connection.close()
            return

        if reseller["balance"] < mod["price"]:
            msg = f"❌ **INSUFFICIENT BALANCE!**\n\nMod Price: `{mod['price']} LKR`\nYour Balance: `{reseller['balance']} LKR`"
            keyboard = [[InlineKeyboardButton("💬 Top-Up With Admin", url=f"https://t.me/{SUPPORT_USERNAME}")], [InlineKeyboardButton("🔙 Back to Store", callback_data="res_store")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            connection.close()
            return

        # Execute Transaction
        key_value = stock_item["key_value"]
        new_balance = reseller["balance"] - mod["price"]

        connection.execute("UPDATE key_pool SET is_used = 1 WHERE id = ?", (stock_item["id"],))
        connection.execute("UPDATE resellers SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        connection.execute("INSERT INTO keys (reseller_id, reseller_name, mod_id, mod_name, key_value, price, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, reseller["name"], mod["id"], mod["name"], key_value, mod["price"], now()))
        connection.commit()

        msg = (
            "🎉 **KEY DELIVERED SUCCESSFULLY!**\n\n"
            f"🎯 **Mod:** {mod['name']}\n"
            f"🔑 **Key:** `{key_value}`\n\n"
            f"💸 **Deducted:** `{mod['price']} LKR`\n"
            f"💰 **Remaining Balance:** `{new_balance} LKR`"
        )
        keyboard = [
            [InlineKeyboardButton("🔑 Buy Another Key", callback_data="res_store")],
            [InlineKeyboardButton("📜 View Key History", callback_data="res_history")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

        # Notify via Logs Bot to Admin Chat ID
        log_text = f"📢 **NEW KEY PURCHASED**\n\n👤 **Reseller:** {reseller['name']} (`{user_id}`)\n🎯 **Mod:** {mod['name']}\n🔑 **Key:** `{key_value}`\n💰 **Price:** {mod['price']} LKR"
        add_log("SALE", f"{reseller['name']} bought {mod['name']} -> {key_value}")
        
        try:
            await logs_bot.send_message(chat_id=get_admin_id(), text=log_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.warning(f"Failed to send log: {e}")

    elif data == "res_history":
        history = connection.execute("SELECT * FROM keys WHERE reseller_id = ? ORDER BY id DESC LIMIT 10", (user_id,)).fetchall()
        if not history:
            msg = "📜 **MY KEY HISTORY**\n\nYou have not generated any keys yet."
        else:
            recent_keys = "\n".join(f"• 🎯 {h['mod_name']} | `{h['key_value']}`" for h in history)
            msg = f"📜 **MY PURCHASED KEYS (Recent 10)**\n\n{recent_keys}"

        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    connection.close()

# ============================================================
# 🚀 MAIN RUNNER
# ============================================================

def main():
    init_database()

    admin_app = ApplicationBuilder().token(ADMIN_TOKEN).build()
    admin_app.add_handler(CommandHandler("start", admin_start))
    admin_app.add_handler(CommandHandler("setadminid", set_admin_chat_id))
    admin_app.add_handler(CommandHandler("addmod", add_mod))
    admin_app.add_handler(CommandHandler("addkey", add_key_stock))
    admin_app.add_handler(CommandHandler("delmod", del_mod))
    admin_app.add_handler(CommandHandler("addreseller", add_reseller))
    admin_app.add_handler(CommandHandler("addbalance", add_balance))
    admin_app.add_handler(CallbackQueryHandler(admin_button_handler, pattern=r"^adm_"))

    reseller_app = ApplicationBuilder().token(RESELLER_TOKEN).build()
    reseller_app.add_handler(CommandHandler("start", reseller_start))
    reseller_app.add_handler(CallbackQueryHandler(reseller_button_handler, pattern=r"^(res_|buy_)"))

    async def run_bots():
        await admin_app.initialize()
        await admin_app.start()
        await admin_app.updater.start_polling()

        await reseller_app.initialize()
        await reseller_app.start()
        await reseller_app.updater.start_polling()

        logger.info("⚡ Seer Store PRO System Running...")
        while True:
            await asyncio.sleep(3600)

    asyncio.run(run_bots())

if __name__ == '__main__':
    main()

