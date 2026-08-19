from telegram import Update
from telegram.ext import ContextTypes

from database import save_user

# -----------------------------
# /start command
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Save user to the database
    save_user(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username
    )

    # Store name temporarily
    context.user_data["name"] = user.first_name
    await update.message.reply_text(
        f"Hello {user.first_name}! 👋\n\n"
        "Welcome to Expense Manager Bot.\n"
        "I'm happy to help you manage your expenses.\n\n"
        "Type /help to see available commands."
    )


# -----------------------------
# /help command
# -----------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    help_text = """
🤖 *Expense Manager Bot*

Welcome! Here are the available commands.

━━━━━━━━━━━━━━━━━━━
👤 *User*
━━━━━━━━━━━━━━━━━━━

/start
Start the bot

/help
Show this help menu

━━━━━━━━━━━━━━━━━━━
👥 *Group Management*
━━━━━━━━━━━━━━━━━━━

/newgroup <GroupName>
Create a new group.

Example:
`/newgroup GoaTrip`

/groups
View all your groups.

/deletegroup <GroupName>

Example:
`/deletegroup GoaTrip`

━━━━━━━━━━━━━━━━━━━
👤 *Member Management*
━━━━━━━━━━━━━━━━━━━

/addmember <GroupName> <MemberName>

Example:
`/addmember GoaTrip Rahul`

/removemember <GroupName> <MemberName>

Example:
`/removemember GoaTrip Rahul`

/members <GroupName>

Example:
`/members GoaTrip`

━━━━━━━━━━━━━━━━━━━
💰 *Expenses*
━━━━━━━━━━━━━━━━━━━

/addexpense

Starts an interactive conversation to add a new expense.

/expenses <GroupName>

View all expenses in a group.

Example:
`/expenses GoaTrip`

━━━━━━━━━━━━━━━━━━━
📊 *Balances*
━━━━━━━━━━━━━━━━━━━

/balance <GroupName>

See who owes whom.

Example:
`/balance GoaTrip`

━━━━━━━━━━━━━━━━━━━
🚧 *Coming Soon*
━━━━━━━━━━━━━━━━━━━

✏️ Edit Expense

🗑 Delete Expense

🤝 Record Settlement

📈 Statistics

📱 Interactive Menu
"""

    await update.message.reply_text(
        help_text,
        parse_mode="Markdown"
    )
