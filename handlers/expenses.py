from telegram import Update, ForceReply
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from database import (
    get_group_id,
    get_member_names,
    create_expense,
    add_expense_split,
    calculate_equal_split,
)

import traceback

# Conversation State
WAITING_DETAILS = 1


# -----------------------------
# /addexpense command
# -----------------------------
async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # print(">>> add_expense called") #to debug
    await update.message.reply_text(
        "Send the expense in exactly this format:\n\n"
        "Group Name\n"
        "Description\n"
        "Amount\n"
        "Paid By",
        reply_markup=ForceReply(selective=True)
    )
    return WAITING_DETAILS


# -----------------------------
# Save Expense
# -----------------------------
async def save_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # print(">>> save_expense called")  #to debug
    # print(update.message.text)  #to debug

    try:
        # Split message into lines
        lines = update.message.text.strip().split("\n")
        if len(lines) != 4:
            await update.message.reply_text(
                "❌ Invalid format.\n\n"
                "Example:\n\n"
                "GoaTrip\n"
                "Dinner\n"
                "1500\n"
                "Siddhabrata\n"
                "Try Again"
            )
            return WAITING_DETAILS

        # Read values
        group_name = lines[0].strip()
        description = lines[1].strip()

        try:
            amount = float(lines[2].strip())
        except ValueError:
            await update.message.reply_text(
                "❌ Amount must be a number.\n" 
                "Try Again"
            )
            return WAITING_DETAILS

        paid_by = lines[3].strip()

        print("Finding group...")

        group_id = get_group_id(
            group_name,
            update.effective_user.id
        )

        print("Group ID:", group_id)

        if group_id is None:
            await update.message.reply_text(
                "❌ Group not found.\n\n"
                "Please send the expense again."
            )
            return WAITING_DETAILS

        print("Fetching members...")

        members = get_member_names(group_id)

        print("Members:", members)

        if len(members) == 0:
            await update.message.reply_text(
                "❌ This group has no members."
            )
            return WAITING_DETAILS

        if paid_by not in members:
            await update.message.reply_text(
                "❌ Paid By must be an existing member."
            )
            return WAITING_DETAILS

        print("Creating expense...")

        expense_id = create_expense(
            group_id,
            description,
            amount,
            paid_by
        )

        print("Expense ID:", expense_id)

        splits = calculate_equal_split(
            amount,
            members
        )

        print("Splits:", splits)
        for split in splits:
            print("Saving split for", split["member"])
            add_expense_split(
                expense_id,
                split["member"],
                split["share"]
            )

        print("Expense saved successfully!")

        await update.message.reply_text(
            f"✅ Expense Added Successfully!\n\n"
            f"📝 Description : {description}\n"
            f"💰 Amount      : ₹{amount:.2f}\n"
            f"👤 Paid By     : {paid_by}\n"
            f"👥 Members     : {len(members)}"
        )

        return ConversationHandler.END

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(
            f"❌ Something went wrong.\n\n{e}"
        )

        return ConversationHandler.END


# -----------------------------
# Cancel command
# -----------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "❌ Expense creation cancelled."
    )
    return ConversationHandler.END


# -----------------------------
# Conversation Handler
# -----------------------------
expense_handler = ConversationHandler(
    entry_points=[
        CommandHandler("addexpense", add_expense)
    ],
    states={
        WAITING_DETAILS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_expense
            )
        ]
    },

    fallbacks=[
        CommandHandler("cancel", cancel)
    ],
)