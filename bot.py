import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
)

# ================= CONFIGURATION =================
RESELLER_TOKEN = "8882760232:AAHnLw-hoF5lgKxkWRhbNypO8POXx9NCFhk"
LOGS_TOKEN = "8993788156:AAGO72TkJkPa5cyEN44gLQWAdvj1NEQlrqQ"
ADMIN_TOKEN = "8192870600:AAHQ91M5z2UN2MKspqK9LK3GeGr-WKUkFng"

ADMIN_CHAT_ID = 8438744876

logs_bot = Bot(token=LOGS_TOKEN)

# System In-Memory Database
RESELLERS = {
    8438744876: {"name": "Owner Admin", "balance": 999999, "history": []}
}

MODS = {
    "Drip Client (1 Day)": 500,
    "Hg Cheats (1 Day)": 400
}

ALL_GLOBAL_LOGS = []  # System එකේ සියලුම Keys වල Master History එක

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


# =================================================
# 👑 ADMIN PANEL (FULL INTERACTIVE BUTTONS)
# =================================================

def get_admin_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Mod & Price", callback_data="adm_guide_mod"),
         InlineKeyboardButton("🗑️ Delete Mod", callback_data="adm_guide_delmod")],
        [InlineKeyboardButton("👤 Register Reseller", callback_data="adm_guide_res"),
         InlineKeyboardButton("💰 Top-Up Balance", callback_data="adm_guide_bal")],
        [InlineKeyboardButton("📜 All Keys Logs", callback_data="adm_view_all_logs"),
         InlineKeyboardButton("🧹 Clear All Logs", callback_data="adm_clear_logs_confirm")],
        [InlineKeyboardButton("📊 System Overview", callback_data="adm_stats")]
    ])

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    await update.message.reply_text(
        "👑 **SEER STORE — MASTER ADMIN CONTROL PANEL** 👑\n\n"
        "Welcome Admin! Control all reseller activities, mod prices, and key logs from this menu:",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="Markdown"
    )

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_CHAT_ID:
        return
    await query.answer()

    data = query.data

    if data == "adm_home":
        await query.edit_message_text(
            "👑 **SEER STORE — MASTER ADMIN CONTROL PANEL** 👑\n\nSelect an operation to perform:",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "adm_stats":
        msg = (
            "📊 **SYSTEM OVERVIEW & STATS**\n\n"
            f"👤 **Registered Resellers:** `{len(RESELLERS)}`\n"
            f"🎮 **Active Mod Items:** `{len(MODS)}`\n"
            f"🔑 **Total Keys Generated All-Time:** `{len(ALL_GLOBAL_LOGS)}`\n"
            f"👑 **Master Admin ID:** `{ADMIN_CHAT_ID}`"
        )
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_home")]]), parse_mode="Markdown")

    elif data == "adm_view_all_logs":
        if not ALL_GLOBAL_LOGS:
            msg = "📜 **MASTER KEY LOGS**\n\nNo keys have been generated yet."
        else:
            recent_logs = "\n".join(ALL_GLOBAL_LOGS[-10:])
            msg = f"📜 **MASTER KEY LOGS (Recent 10)**\n\n{recent_logs}"

        keyboard = [
            [InlineKeyboardButton("🧹 Clear All Logs", callback_data="adm_clear_logs_confirm")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_home")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "adm_clear_logs_confirm":
        keyboard = [
            [InlineKeyboardButton("⚠️ Yes, Clear Everything", callback_data="adm_clear_logs_do")],
            [InlineKeyboardButton("❌ Cancel", callback_data="adm_home")]
        ]
        await query.edit_message_text(
            "⚠️ **ARE YOU SURE YOU WANT TO CLEAR ALL KEY LOGS?**\n\nThis will reset the global key history list.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "adm_clear_logs_do":
        ALL_GLOBAL_LOGS.clear()
        await query.edit_message_text(
            "✅ **ALL KEY LOGS CLEARED SUCCESSFULLY!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_home")]]),
            parse_mode="Markdown"
        )

    elif data == "adm_guide_mod":
        msg = "➕ **ADD MOD & PRICE INSTRUCTIONS**\n\nSend command:\n`/addmod <Mod_Name> <Price>`\n\n*Example:* `/addmod Drip_Client_1Day 500`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode="Markdown")

    elif data == "adm_guide_res":
        msg = "👤 **REGISTER RESELLER INSTRUCTIONS**\n\nSend command:\n`/addreseller <Chat_ID> <Name>`\n\n*Example:* `/addreseller 8610996167 Sulthan`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode="Markdown")

    elif data == "adm_guide_bal":
        msg = "💰 **TOP-UP BALANCE INSTRUCTIONS**\n\nSend command:\n`/addbalance <Chat_ID> <Amount>`\n\n*Example:* `/addbalance 8610996167 5000`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode="Markdown")

    elif data == "adm_guide_delmod":
        msg = "🗑️ **DELETE MOD INSTRUCTIONS**\n\nSend command:\n`/delmod <Mod_Name>`\n\n*Example:* `/delmod Drip_Client_1Day`"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_home")]]), parse_mode="Markdown")


# Admin Command Listeners
async def add_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID: return
    try:
        mod_name = context.args[0].replace("_", " ")
        price = int(context.args[1])
        MODS[mod_name] = price
        await update.message.reply_text(f"✅ **Mod Added:** `{mod_name}` — `{price} LKR`", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/addmod Mod_Name Price`", parse_mode="Markdown")

async def del_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID: return
    try:
        mod_name = context.args[0].replace("_", " ")
        if mod_name in MODS:
            del MODS[mod_name]
            await update.message.reply_text(f"✅ **Mod Removed:** `{mod_name}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ **Mod not found!**", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/delmod Mod_Name`", parse_mode="Markdown")

async def add_reseller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID: return
    try:
        target_id = int(context.args[0])
        name = context.args[1] if len(context.args) > 1 else "Reseller"
        RESELLERS[target_id] = {"name": name, "balance": 0, "history": []}
        await update.message.reply_text(f"✅ **Reseller Activated:** `{name}` (`{target_id}`)", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/addreseller Chat_ID Name`", parse_mode="Markdown")

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID: return
    try:
        target_id, amount = int(context.args[0]), int(context.args[1])
        if target_id in RESELLERS:
            RESELLERS[target_id]["balance"] += amount
            await update.message.reply_text(
                f"✅ **Balance Top-Up Successful!**\n\n👤 **Reseller:** `{target_id}`\n➕ **Added:** `{amount} LKR`\n💰 **New Balance:** `{RESELLERS[target_id]['balance']} LKR`",
                parse_mode="Markdown"
            )
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"🎉 **BALANCE TOP-UP CONFIRMED!**\n\nAdded Amount: `+{amount} LKR`\nUpdated Wallet Balance: `{RESELLERS[target_id]['balance']} LKR`",
                    parse_mode="Markdown"
                )
            except Exception: pass
    except Exception:
        await update.message.reply_text("⚠️ **Usage:** `/addbalance Chat_ID Amount`", parse_mode="Markdown")


# =================================================
# 💎 RESELLER PANEL (PROFESSIONAL INTERFACE)
# =================================================

def get_reseller_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Store & Generate Keys", callback_data="res_store")],
        [InlineKeyboardButton("👤 My Wallet Profile", callback_data="res_profile"),
         InlineKeyboardButton("📜 My Keys History", callback_data="res_history")],
        [InlineKeyboardButton("💬 Admin Support", url="https://t.me/SeerCheatz72")]
    ])

async def reseller_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in RESELLERS:
        await update.message.reply_text(
            "🔒 **ACCESS RESTRICTED**\n\nYou are not an authorized reseller.\nContact Administrator to obtain reseller access.",
            parse_mode="Markdown"
        )
        return

    reseller = RESELLERS[user_id]
    await update.message.reply_text(
        f"🔥 **WELCOME TO SEER STORE RESELLER PANEL** 🔥\n\n"
        f"👤 **Reseller:** {update.effective_user.first_name}\n"
        f"💰 **Wallet Balance:** `{reseller['balance']} LKR`\n\n"
        f"Choose an option from below:",
        reply_markup=get_reseller_main_keyboard(),
        parse_mode="Markdown"
    )

async def reseller_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in RESELLERS:
        await query.edit_message_text("❌ **Access Denied!**")
        return

    data = query.data
    reseller = RESELLERS[user_id]

    if data == "res_home":
        await query.edit_message_text(
            f"🔥 **WELCOME TO SEER STORE RESELLER PANEL** 🔥\n\n"
            f"👤 **Reseller:** {query.from_user.first_name}\n"
            f"💰 **Wallet Balance:** `{reseller['balance']} LKR`\n\n"
            f"Choose an option from below:",
            reply_markup=get_reseller_main_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "res_profile":
        msg = (
            "👤 **RESELLER ACCOUNT SUMMARY**\n\n"
            f"🔹 **Account Holder:** {reseller['name']}\n"
            f"🔹 **Telegram ID:** `{user_id}`\n"
            f"💰 **Current Balance:** `{reseller['balance']} LKR`\n"
            f"🔑 **Total Keys Generated:** `{len(reseller.get('history', []))}`"
        )
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]]), parse_mode="Markdown")

    elif data == "res_store":
        if not MODS:
            await query.edit_message_text(
                "⚠️ **STORE OUT OF STOCK / NO MODS ADDED**\nPlease contact Admin to update mods list.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]]),
                parse_mode="Markdown"
            )
            return

        keyboard = []
        for mod, price in MODS.items():
            keyboard.append([InlineKeyboardButton(f"🎯 {mod} — {price} LKR", callback_data=f"buy_{mod}")])
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")])

        await query.edit_message_text(
            "🛒 **AVAILABLE MODS & KEY GENERATOR**\n\nSelect a Mod from the store below to generate key:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("buy_"):
        mod_name = data.split("_", 1)[1]
        price = MODS.get(mod_name, 0)

        if reseller["balance"] < price:
            msg = (
                f"❌ **INSUFFICIENT WALLET BALANCE!**\n\n"
                f"Mod Price: `{price} LKR`\n"
                f"Your Balance: `{reseller['balance']} LKR`\n\n"
                f"Please top-up your wallet with the Admin."
            )
            keyboard = [
                [InlineKeyboardButton("💬 Top-Up With Admin", url="https://t.me/SeerCheatz72")],
                [InlineKeyboardButton("🔙 Back to Store", callback_data="res_store")]
            ]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return

        # Deduct Balance & Create Key
        reseller["balance"] -= price
        clean_code = mod_name.replace(" ", "").upper()[:4]
        generated_key = f"SEER-{clean_code}-9823-XITER"

        key_log_entry = f"🎯 {mod_name} | Key: `{generated_key}`"
        
        if "history" not in reseller: reseller["history"] = []
        reseller["history"].append(key_log_entry)
        ALL_GLOBAL_LOGS.append(f"Reseller @{query.from_user.username or user_id} | {key_log_entry}")

        msg = (
            "🎉 **KEY GENERATED SUCCESSFULLY!**\n\n"
            f"🎯 **Mod:** {mod_name}\n"
            f"🔑 **Key:** `{generated_key}`\n\n"
            f"💸 **Deducted:** `{price} LKR`\n"
            f"💰 **Remaining Balance:** `{reseller['balance']} LKR`"
        )
        keyboard = [
            [InlineKeyboardButton("🔑 Generate Another Key", callback_data="res_store")],
            [InlineKeyboardButton("📜 View Key History", callback_data="res_history")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

        # LOGS TO LOGS BOT
        log_text = (
            "📢 **NEW KEY LOG**\n\n"
            f"👤 **Reseller:** @{query.from_user.username or user_id} (`{user_id}`)\n"
            f"🎯 **Mod:** {mod_name}\n"
            f"🔑 **Key:** `{generated_key}`\n"
            f"💰 **Price:** {price} LKR"
        )
        try:
            await logs_bot.send_message(chat_id=ADMIN_CHAT_ID, text=log_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Log Error: {e}")

    elif data == "res_history":
        history = reseller.get("history", [])
        if not history:
            msg = "📜 **MY KEY HISTORY**\n\nYou have not generated any keys yet."
        else:
            recent_keys = "\n".join(f"• {item}" for item in history[-10:])
            msg = f"📜 **MY GENERATED KEYS HISTORY (Recent 10)**\n\n{recent_keys}"

        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="res_home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# =================================================
# 🚀 MAIN RUNNER
# =================================================

def main():
    admin_app = ApplicationBuilder().token(ADMIN_TOKEN).build()
    admin_app.add_handler(CommandHandler("start", admin_start))
    admin_app.add_handler(CallbackQueryHandler(admin_button_handler))
    admin_app.add_handler(CommandHandler("addmod", add_mod))
    admin_app.add_handler(CommandHandler("delmod", del_mod))
    admin_app.add_handler(CommandHandler("addreseller", add_reseller))
    admin_app.add_handler(CommandHandler("addbalance", add_balance))

    reseller_app = ApplicationBuilder().token(RESELLER_TOKEN).build()
    reseller_app.add_handler(CommandHandler("start", reseller_start))
    reseller_app.add_handler(CallbackQueryHandler(reseller_button_handler))

    async def run_bots():
        await admin_app.initialize()
        await admin_app.start()
        await admin_app.updater.start_polling()

        await reseller_app.initialize()
        await reseller_app.start()
        await reseller_app.updater.start_polling()

        print("⚡ Seer Store Full Interactive System Running...")
        while True:
            await asyncio.sleep(3600)

    asyncio.run(run_bots())

if __name__ == '__main__':
    main()
