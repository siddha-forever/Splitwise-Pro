from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from database import (
    get_group_id,
    get_expenses,
    get_expense,
    delete_expense,
    update_expense_description,
    update_expense_amount,
    update_expense_paid_by,
    delete_expense_splits,
    add_expense_split,
    calculate_equal_split,
    get_member_names,
    get_expense_split_details
)

SELECT_EXPENSE = 1
EDIT_MENU = 2
EDIT_DESCRIPTION = 3
EDIT_AMOUNT = 4
EDIT_PAID_BY = 5
CONFIRM_DELETE = 6

# /expenses GroupName
async def expenses_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/expenses GroupName"
        )
        return

    group_name = context.args[0]
    group_id = get_group_id(
        group_name,
        update.effective_user.id
    )

    if group_id is None:
        await update.message.reply_text(
            "❌ Group not found."
        )
        return

    expenses = get_expenses(group_id)

    if len(expenses) == 0:
        await update.message.reply_text(
            "No expenses added yet."
        )
        return

    message = f"📒 {group_name} Expenses\n\n"

    for expense in expenses:
        expense_id = expense[0]
        description = expense[1]
        amount = expense[2]
        paid_by = expense[3]
        created_at = expense[4]

        message += (
            "────────────────────\n"
            f"🆔 #{expense_id}\n"
            f"📝 {description}\n"
            f"💰 ₹{amount:.2f}\n"
            f"👤 Paid by: {paid_by}\n"
            f"📅 {created_at}\n\n"
        )
    await update.message.reply_text(message)

# /expense ExpenseID
async def expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/expense ExpenseID"
        )
        return

    try:
        expense_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Expense ID must be a number."
        )
        return

    expense = get_expense(expense_id)
    if expense is None:
        await update.message.reply_text(
            "Expense not found."
        )
        return
    splits = get_expense_split_details(expense_id)

    message = (
        f"🆔 Expense #{expense[0]}\n\n"
        f"📝 {expense[2]}\n"
        f"💰 ₹{expense[3]:.2f}\n"
        f"👤 Paid by: {expense[4]}\n"
        f"📅 {expense[5]}\n\n"
        f"👥 Split\n\n"
    )

    for member, share in splits:
        message += f"• {member} : ₹{share:.2f}\n"

    await update.message.reply_text(message)

expense_management_handler = [
    CommandHandler("expenses", expenses_command),
    CommandHandler("expense", expense_command),
]

#delete expense from group
async def delete_expense_command(update, context):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Usage:\n/deleteexpense ExpenseID"
        )

        return ConversationHandler.END

    try:

        expense_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "Expense ID must be a number."
        )

        return ConversationHandler.END

    expense = get_expense(expense_id)

    if expense is None:

        await update.message.reply_text(
            "Expense not found."
        )

        return ConversationHandler.END

    context.user_data["delete_expense_id"] = expense_id

    await update.message.reply_text(

        f"⚠️ Delete Expense\n\n"
        f"🆔 #{expense[0]}\n"
        f"📝 {expense[2]}\n"
        f"💰 ₹{expense[3]:.2f}\n"
        f"👤 Paid by: {expense[4]}\n\n"
        f"Reply YES to confirm\n"
        f"Reply NO to cancel."
    )

    return CONFIRM_DELETE

#confirming delete functionality
async def confirm_delete(update, context):
    answer = update.message.text.strip().upper()

    if answer == "NO":
        context.user_data.pop("delete_expense_id", None)
        await update.message.reply_text(
            "Deletion cancelled."
        )

        return ConversationHandler.END

    if answer != "YES":
        await update.message.reply_text(
            "Please reply with YES or NO."
        )

        return CONFIRM_DELETE

    expense_id = context.user_data.get("delete_expense_id")

    if expense_id is None:
        await update.message.reply_text(
            "No expense selected."
        )

        return ConversationHandler.END

    deleted = delete_expense(expense_id)
    context.user_data.pop("delete_expense_id", None)

    if deleted:
        await update.message.reply_text(
            "✅ Expense deleted successfully."
        )

    else:
        await update.message.reply_text(
            "Expense not found."
        )

    return ConversationHandler.END

delete_expense_handler = ConversationHandler(
    entry_points=[
        CommandHandler(
            "deleteexpense",
            delete_expense_command
        )
    ],
    states={
        CONFIRM_DELETE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                confirm_delete
            )
        ]
    },
    fallbacks=[]
)

async def edit_expense_command(update, context):
    print(">>> edit_expense_command called")
    # Check command format
    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/editexpense ExpenseID"
        )
        return ConversationHandler.END

    try:
        expense_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Expense ID must be a number."
        )
        return ConversationHandler.END

    expense = get_expense(expense_id)
    if expense is None:
        await update.message.reply_text(
            "❌ Expense not found."
        )
        return ConversationHandler.END

    # Save expense id for later use
    context.user_data["edit_expense_id"] = expense_id

    # Save additional details (useful later)
    context.user_data["group_id"] = expense[1]

    # Show current expense details
    message = (
        f"✏️ Editing Expense #{expense[0]}\n\n"
        f"📝 Description : {expense[2]}\n"
        f"💰 Amount      : ₹{expense[3]:.2f}\n"
        f"👤 Paid By     : {expense[4]}\n"
        f"📅 Created At  : {expense[5]}\n\n"
        "What would you like to edit?\n\n"
        "1️⃣ Description\n"
        "2️⃣ Amount\n"
        "3️⃣ Paid By\n"
        "4️⃣ Cancel"
    )
    await update.message.reply_text(message)
    return EDIT_MENU

# Handle the edit menu selection
async def edit_menu(update, context):
    choice = update.message.text.strip()
    # Option 1 - Edit description
    if choice == "1":
        await update.message.reply_text(
            "📝 Enter the new description:"
        )
        return EDIT_DESCRIPTION

    # Option 2 - Edit amount
    elif choice == "2":
        await update.message.reply_text(
            "💰 Enter the new amount:"
        )

        return EDIT_AMOUNT

    # Option 3 - Edit paid by
    elif choice == "3":
        group_id = context.user_data.get("group_id")
        if group_id is None:
            await update.message.reply_text(
                "❌ Group information not found."
            )

            return ConversationHandler.END

        members = get_member_names(group_id)

        if len(members) == 0:
            await update.message.reply_text(
                "❌ This group has no members."
            )

            return ConversationHandler.END

        member_list = "\n".join(
            f"• {member}"
            for member in members
        )

        await update.message.reply_text(
            "👤 Enter the name of the member who paid.\n\n"
            "Available members:\n\n"
            f"{member_list}"
        )
        return EDIT_PAID_BY

    # Option 4 - Cancel
    elif choice == "4":
        context.user_data.pop(
            "edit_expense_id",
            None
        )

        context.user_data.pop(
            "group_id",
            None
        )

        await update.message.reply_text(
            "❌ Expense editing cancelled."
        )

        return ConversationHandler.END

    # Invalid option
    else:
        await update.message.reply_text(
            "❌ Invalid option.\n\n"
            "Please choose:\n\n"
            "1️⃣ Description\n"
            "2️⃣ Amount\n"
            "3️⃣ Paid By\n"
            "4️⃣ Cancel"
        )
        return EDIT_MENU

#update the description
async def update_description(update, context):
    new_description = update.message.text.strip()
    if not new_description:
        await update.message.reply_text(
            "❌ Description cannot be empty.\n\n"
            "Please enter a valid description."
        )
        return EDIT_DESCRIPTION

    expense_id = context.user_data.get("edit_expense_id")

    if expense_id is None:
        await update.message.reply_text(
            "❌ No expense is currently being edited."
        )
        return ConversationHandler.END

    updated = update_expense_description(
        expense_id,
        new_description
    )

    if updated:
        await update.message.reply_text(
            f"✅ Description updated successfully!\n\n"
            f"📝 New description:\n"
            f"{new_description}"
        )
    else:
        await update.message.reply_text(
            "❌ Could not update the expense."
        )

    # Clean up
    context.user_data.pop("edit_expense_id", None)
    context.user_data.pop("group_id", None)

    return ConversationHandler.END

#now recalculate the splits
async def update_amount(update, context):
    amount_text = update.message.text.strip()
    # Validate amount
    try:
        new_amount = float(amount_text)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount.\n\n"
            "Please enter a valid number.\n\n"
            "Example:\n"
            "1800"
        )
        return EDIT_AMOUNT

    # Validate positive amount
    if new_amount <= 0:
        await update.message.reply_text(
            "❌ Amount must be greater than ₹0.\n\n"
            "Please enter a valid amount."
        )
        return EDIT_AMOUNT

    expense_id = context.user_data.get("edit_expense_id")

    if expense_id is None:
        await update.message.reply_text(
            "❌ No expense is currently being edited."
        )

        return ConversationHandler.END

    # Get existing expense
    expense = get_expense(expense_id)
    if expense is None:
        await update.message.reply_text(
            "❌ Expense not found."
        )
        return ConversationHandler.END

    group_id = expense[1]

    # Get group members
    members = get_member_names(group_id)
    if len(members) == 0:

        await update.message.reply_text(
            "❌ This group has no members."
        )

        return ConversationHandler.END

    # Update amount
    updated = update_expense_amount(
        expense_id,
        new_amount
    )

    if not updated:
        await update.message.reply_text(
            "❌ Could not update the expense."
        )
        return ConversationHandler.END

    # Delete old splits
    delete_expense_splits(expense_id)

    # Calculate new equal splits
    splits = calculate_equal_split(
        new_amount,
        members
    )
    # Save new splits
    for split in splits:
        add_expense_split(
            expense_id,
            split["member"],
            split["share"]
        )

    await update.message.reply_text(
        f"✅ Amount updated successfully!\n\n"
        f"💰 New amount: ₹{new_amount:.2f}\n\n"
        f"👥 Equal split recalculated for "
        f"{len(members)} members."
    )
    # Clean up
    context.user_data.pop("edit_expense_id", None)
    context.user_data.pop("group_id", None)
    return ConversationHandler.END

#update paid by function
async def update_paid_by(update, context):
    new_paid_by = update.message.text.strip()
    if not new_paid_by:
        await update.message.reply_text(
            "❌ Member name cannot be empty."
        )
        return EDIT_PAID_BY

    expense_id = context.user_data.get("edit_expense_id")

    if expense_id is None:
        await update.message.reply_text(
            "❌ No expense is currently being edited."
        )
        return ConversationHandler.END

    # Get existing expense
    expense = get_expense(expense_id)
    if expense is None:
        await update.message.reply_text(
            "❌ Expense not found."
        )
        return ConversationHandler.END

    group_id = expense[1]

    # Get group members
    members = get_member_names(group_id)
    # Validate payer
    if new_paid_by not in members:
        member_list = "\n".join(
            f"• {member}"
            for member in members
        )
        await update.message.reply_text(
            "❌ That person is not a member of this group.\n\n"
            "Please choose one of these members:\n\n"
            f"{member_list}"
        )

        return EDIT_PAID_BY

    # Update payer
    updated = update_expense_paid_by(
        expense_id,
        new_paid_by
    )
    if updated:
        await update.message.reply_text(
            f"✅ Paid By updated successfully!\n\n"
            f"👤 New payer: {new_paid_by}"
        )
    else:

        await update.message.reply_text(
            "❌ Could not update the payer."
        )

    # Clean up
    context.user_data.pop("edit_expense_id", None)
    context.user_data.pop("group_id", None)
    return ConversationHandler.END

#to cancel edit midway
async def cancel_edit(update, context):
    context.user_data.pop("edit_expense_id", None)
    context.user_data.pop("group_id", None)

    await update.message.reply_text(
        "❌ Expense editing cancelled."
    )

    return ConversationHandler.END


#conversation handler
edit_expense_handler = ConversationHandler(
    entry_points=[
        CommandHandler(
            "editexpense",
            edit_expense_command
        )
    ],
    states={

        EDIT_MENU: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                edit_menu
            )
        ],
        EDIT_DESCRIPTION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                update_description
            )
        ],
        EDIT_AMOUNT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                update_amount
            )
        ],
        EDIT_PAID_BY: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                update_paid_by
            )
        ],
    },

    fallbacks=[
        CommandHandler(
            "cancel",
            cancel_edit
        )
    ]
)