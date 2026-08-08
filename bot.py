import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# ================= CONFIGURATION =================
RESELLER_TOKEN = "8882760232:AAHnLw-hoF5lgKxkWRhbNypO8POXx9NCFhk"
LOGS_TOKEN = "8993788156:AAGO72TkJkPa5cyEN44gLQWAdvj1NEQlrqQ"
ADMIN_TOKEN = "8192870600:AAHQ91M5z2UN2MKspqK9LK3GeGr-WKUkFng"

ADMIN_CHAT_ID = 8438744876

logs_bot = Bot(token=LOGS_TOKEN)

# Shared Memory Data
RESELLERS = {
    8438744876: {"name": "Admin", "balance": 999999}
}

MODS = {
    "Drip Client": 500,
    "Hg Cheats": 400
}
# =================================================

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ADMIN BOT HANDLERS ---
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    msg = (
        "👑 ADMIN PANEL CONTROL\n\n"
        "Commands:\n"
        "1. /addmod <mod_name> <price>\n"
        "2. /delmod <mod_name>\n"
        "3. /addreseller <user_id> <name>\n"
        "4. /addbalance <user_id> <amount>\n"
        "5. /setadmin <new_chat_id>\n"
    )
    await update.message.reply_text(msg)

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_CHAT_ID
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    try:
        ADMIN_CHAT_ID = int(context.args[0])
        await update.message.reply_text(f"✅ Admin Chat ID updated: `{ADMIN_CHAT_ID}`")
    except Exception:
        await update.message.reply_text("⚠️ Usage: /setadmin <new_chat_id>")

async def add_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    try:
        mod_name, price = context.args[0], int(context.args[1])
        MODS[mod_name] = price
        await update.message.reply_text(f"✅ Mod `{mod_name}` added: {price} LKR")
    except Exception:
        await update.message.reply_text("⚠️ Usage: /addmod <mod_name> <price>")

async def del_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    try:
        mod_name = context.args[0]
        if mod_name in MODS:
            del MODS[mod_name]
            await update.message.reply_text(f"✅ Mod `{mod_name}` deleted!")
    except Exception:
        await update.message.reply_text("⚠️ Usage: /delmod <mod_name>")

async def add_reseller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    try:
        target_id = int(context.args[0])
        name = context.args[1] if len(context.args) > 1 else "Reseller"
        RESELLERS[target_id] = {"name": name, "balance": 0}
        await update.message.reply_text(f"✅ Reseller `{target_id}` added!")
    except Exception:
        await update.message.reply_text("⚠️ Usage: /addreseller <user_id> <name>")

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    try:
        target_id, amount = int(context.args[0]), int(context.args[1])
        if target_id in RESELLERS:
            RESELLERS[target_id]["balance"] += amount
            await update.message.reply_text(f"✅ Added {amount} LKR to `{target_id}`")
    except Exception:
        await update.message.reply_text("⚠️ Usage: /addbalance <user_id> <amount>")


# --- RESELLER BOT HANDLERS ---
async def reseller_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in RESELLERS:
        await update.message.reply_text("❌ ACCESS DENIED!")
        return

    balance = RESELLERS[user_id]["balance"]
    keyboard = [
        [InlineKeyboardButton("🔑 Generate Key", callback_data="gen_key_menu")],
        [InlineKeyboardButton("💰 My Balance", callback_data="check_balance")]
    ]
    await update.message.reply_text(
        f"👑 RESELLER DASHBOARD\n\nUser: {update.effective_user.first_name}\nBalance: {balance} LKR",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def reseller_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in RESELLERS:
        await query.edit_message_text("❌ Access Denied!")
        return

    data = query.data
    if data == "check_balance":
        await query.edit_message_text(f"💰 Current Balance: {RESELLERS[user_id]['balance']} LKR")

    elif data == "gen_key_menu":
        keyboard = []
        items = list(MODS.items())
        for i in range(0, len(items), 2):
            row = [InlineKeyboardButton(f"{items[i][0]} - {items[i][1]} LKR", callback_data=f"buy_{items[i][0]}")]
            if i + 1 < len(items):
                row.append(InlineKeyboardButton(f"{items[i+1][0]} - {items[i+1][1]} LKR", callback_data=f"buy_{items[i+1][0]}"))
            keyboard.append(row)
        await query.edit_message_text("🔑 Select Mod:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_"):
        mod_name = data.split("_")[1]
        price = MODS.get(mod_name, 0)

        if RESELLERS[user_id]["balance"] < price:
            await query.edit_message_text("❌ INSUFFICIENT BALANCE!")
            return

        RESELLERS[user_id]["balance"] -= price
        generated_key = f"KEY-{mod_name[:3].upper()}-99823-XITER"

        await query.edit_message_text(
            f"✅ KEY GENERATED!\n\nMod: {mod_name}\nKey: `{generated_key}`\nBalance Left: {RESELLERS[user_id]['balance']} LKR"
        )

        log_text = (
            f"📢 NEW KEY LOG\n\n"
            f"Reseller: @{query.from_user.username or user_id}\n"
            f"Mod: {mod_name}\n"
            f"Key: `{generated_key}`"
        )
        try:
            await logs_bot.send_message(chat_id=ADMIN_CHAT_ID, text=log_text)
        except Exception as e:
            print(f"Log Error: {e}")


# --- MAIN RUNNER ---
def main():
    admin_app = ApplicationBuilder().token(ADMIN_TOKEN).build()
    admin_app.add_handler(CommandHandler("start", admin_start))
    admin_app.add_handler(CommandHandler("setadmin", set_admin))
    admin_app.add_handler(CommandHandler("addmod", add_mod))
    admin_app.add_handler(CommandHandler("delmod", del_mod))
    admin_app.add_handler(CommandHandler("addreseller", add_reseller))
    admin_app.add_handler(CommandHandler("addbalance", add_balance))

    reseller_app = ApplicationBuilder().token(RESELLER_TOKEN).build()
    reseller_app.add_handler(CommandHandler("start", reseller_start))
    reseller_app.add_handler(CallbackQueryHandler(reseller_button))

    # Run Admin bot and Reseller bot concurrently
    import asyncio
    async def run_bots():
        await admin_app.initialize()
        await admin_app.start()
        await admin_app.updater.start_polling()

        await reseller_app.initialize()
        await reseller_app.start()
        await reseller_app.updater.start_polling()

        while True:
            await asyncio.sleep(3600)

    asyncio.run(run_bots())

if __name__ == '__main__':
    main()
