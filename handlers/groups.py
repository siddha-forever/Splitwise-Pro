from telegram import Update
from telegram.ext import ContextTypes

from database import (
    create_group,
    get_groups,
    delete_group,
)

# -----------------------------
# /newgroup command
# -----------------------------
async def new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            "Usage:\n/newgroup <group_name>\n"
            "Note: Use underscores instead of spaces, e.g., 'My_Project_Team'"
        )
        return

    group_name = " ".join(context.args)

    # Check for spaces
    if " " in group_name:
        await update.message.reply_text(
            "❌ Group names cannot contain spaces.\n"
            "Use underscores or hyphens instead.\n"
            "Example: /newgroup My_Project_Team"
        )
        return

    success = create_group(
        group_name,
        update.effective_user.id
    )

    if success:
        await update.message.reply_text(
            f'✅ Group "{group_name}" created successfully.'
        )
    else:
        await update.message.reply_text(
            "❌ You already have a group with this name."
        )

# -----------------------------
# /groups command
# -----------------------------
async def groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_groups = get_groups(update.effective_user.id)

    if not all_groups:
        await update.message.reply_text(
            "You don't have any groups yet."
        )

        return

    message = "📁 Your Groups\n\n"

    for index, group in enumerate(all_groups, start=1):
        message += f"{index}. {group[1]}\n"

    await update.message.reply_text(message)

# -----------------------------
# Delete Groups functionality
# /deletegroup
# -----------------------------
async def delete_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            "Usage:\n/deletegroup <group_name>\n"
            "Example: /deletegroup My_Project_Team"
        )
        return

    group_name = " ".join(context.args)
    
    # Validate: No spaces allowed
    if " " in group_name:
        await update.message.reply_text(
            "❌ Group names cannot contain spaces.\n"
            "Use the exact group name as shown in /groups"
        )
        return

    success = delete_group(group_name, update.effective_user.id)

    if success:
        await update.message.reply_text(f'🗑️ "{group_name}" deleted.')
    else:
        await update.message.reply_text(
            "❌ Group not found.\n"
            "Check your groups with /groups"
        )