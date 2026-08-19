from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


# --------------------------------
# Main Menu Keyboard
# --------------------------------
def get_main_menu():

    keyboard = [
        ["➕ Add Expense", "📊 Balance"],
        ["💸 Settle Payment", "📒 Expenses"],
        ["👥 Groups", "❓ Help"],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# --------------------------------
# /start menu
# --------------------------------
async def main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
    ):

    await update.message.reply_text(
        "💰 Expense Manager\n\n"
        "Welcome! What would you like to do?",
        reply_markup=get_main_menu()
    )


# --------------------------------
# Menu button handler
# --------------------------------
async def menu_button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
    ):

    text = update.message.text
    if text == "➕ Add Expense":
        await update.message.reply_text(
            "➕ Add Expense\n\n"
            "Use /addexpense to add a new expense."
        )

    elif text == "📊 Balance":
        await update.message.reply_text(
            "📊 Balance\n\n"
            "Use /balance GroupName\n\n"
            "Example:\n"
            "/balance My_Group"
        )

    elif text == "💸 Settle Payment":
        await update.message.reply_text(
            "💸 Settle Payment\n\n"
            "Use /settle GroupName\n\n"
            "Example:\n"
            "/settle My_Group"
        )

    elif text == "📒 Expenses":
        await update.message.reply_text(
            "📒 Expenses\n\n"
            "Use /expenses GroupName\n\n"
            "Example:\n"
            "/expenses My_Group"
        )

    elif text == "👥 Groups":
        await update.message.reply_text(
            "👥 Groups\n\n"
            "Use /groups to view your groups."
        )

    elif text == "❓ Help":
        await update.message.reply_text(
            "❓ Help\n\n"
            "Use /help to see all available commands."
        )

