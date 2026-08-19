from telegram import Update
from telegram.ext import ContextTypes

from database import (
    add_member,
    get_members,
    remove_member
)

# -----------------------------
# Members in Groups functionality
# /addmember
# -----------------------------
async def add_member_command(update, context):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/addmember <group> <member>"
        )
        return

    group_name = context.args[0]
    member_name = " ".join(context.args[1:])

    result = add_member(
        group_name,
        update.effective_user.id,
        member_name
    )

    if result == "SUCCESS":
        await update.message.reply_text(
            f"✅ {member_name} added to {group_name}"
        )
    elif result == "EXISTS":
        await update.message.reply_text(
            "Member already exists."
        )
    else:
        await update.message.reply_text(
            "Group not found."
        )

# -----------------------------
# /members
# -----------------------------
async def members_command(update, context):
    if len(context.args) == 0:
        await update.message.reply_text(
            "Usage:\n/members <group>"
        )
        return
    group_name = " ".join(context.args)
    members = get_members(
        group_name,
        update.effective_user.id
    )
    if members is None:
        await update.message.reply_text(
            "Group not found."
        )
        return
    if not members:
        await update.message.reply_text(
            "No members in this group."
        )
        return
    message = f"👥 {group_name}\n\n"

    for i, member in enumerate(members, start=1):
        message += f"{i}. {member[0]}\n"

    await update.message.reply_text(message)

# -----------------------------
# /removemember
# -----------------------------
async def remove_member_command(update, context):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/removemember <group> <member>"
        )
        return

    group_name = context.args[0]
    member_name = " ".join(context.args[1:])

    success = remove_member(
        group_name,
        update.effective_user.id,
        member_name
    )

    if success:
        await update.message.reply_text(
            f"🗑 {member_name} removed."
        )
    else:
        await update.message.reply_text(
            "Member or group not found."
        )
