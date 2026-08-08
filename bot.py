import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# ================= CONFIGURATION =================
TOKEN = "8859933227:AAEMJ3-BZ_obhkAck8K8oz4M-cUAxpJpw_s"
ADMIN_CHAT_ID = 8438744876

# Mod List
MODS = [
    "Drip Client",
    "Drip Client Proxy",
    "Hg Cheats",
    "Hg Proxy",
    "Br Mods Root",
    "Pato Team",
    "Silent Cheats",
    "Fluorite",
    "Migual"
]
# =================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display Mod List Buttons"""
    keyboard = []
    for i in range(0, len(MODS), 2):
        row = [InlineKeyboardButton(MODS[i], callback_data=f"mod_{i}")]
        if i + 1 < len(MODS):
            row.append(InlineKeyboardButton(MODS[i+1], callback_data=f"mod_{i+1}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Welcome! Please select your Mod/Client:",
        reply_markup=reply_markup
    )

async def mod_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for Key after Mod selection"""
    query = update.callback_query
    await query.answer()

    mod_index = int(query.data.split('_')[1])
    selected_mod = MODS[mod_index]
    context.user_data['selected_mod'] = selected_mod

    await query.edit_message_text(
        f"Selected Mod: {selected_mod}\n\nPlease send your License Key now:"
    )

async def handle_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Key Input and Notify Admin"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    key = update.message.text.strip()
    selected_mod = context.user_data.get('selected_mod', 'Unknown')

    # Notify User
    await update.message.reply_text(
        f"⏳ STATUS: PENDING\n\n"
        f"Mod: {selected_mod}\n"
        f"Key: {key}\n\n"
        f"Your request has been submitted to Admin."
    )

    # Notify Admin
    keyboard = [
        [
            InlineKeyboardButton("Approve", callback_data=f"app_{user_id}_{mod_index_by_name(selected_mod)}"),
            InlineKeyboardButton("Reject", callback_data=f"rej_{user_id}_{mod_index_by_name(selected_mod)}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"NEW RESET REQUEST\n\n"
             f"User: @{username} (ID: {user_id})\n"
             f"Mod: {selected_mod}\n"
             f"Key: {key}",
        reply_markup=reply_markup
    )

def mod_index_by_name(name):
    try:
        return MODS.index(name)
    except ValueError:
        return 0

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Admin Approval/Rejection"""
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action = data[0]
    user_id = int(data[1])
    mod_name = MODS[int(data[2])]

    if action == "app":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ RESET SUCCESSFUL!\n\nMod: {mod_name}\nStatus: Key Reset Approved."
            )
        except Exception:
            pass
        await query.edit_message_text(f"Approved for User: {user_id} ({mod_name})")

    elif action == "rej":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ RESET REJECTED!\n\nMod: {mod_name}\nStatus: Key Reset Denied."
            )
        except Exception:
            pass
        await query.edit_message_text(f"Rejected for User: {user_id} ({mod_name})")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(mod_selected, pattern="^mod_"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^(app_|rej_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_key_input))

    print("Bot is running...")
    app.run_polling()
