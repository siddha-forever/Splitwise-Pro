from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from database import get_group_id

from services.balance_service import (
    calculate_balances,
    calculate_settlements,
    apply_settlements
)


async def balance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # Check command format
    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/balance GroupName"
        )
        return

    group_name = context.args[0]

    # Find group
    group_id = get_group_id(
        group_name,
        update.effective_user.id
    )

    if group_id is None:
        await update.message.reply_text(
            "❌ Group not found."
        )
        return

    # Calculate balances
    balances = calculate_balances(group_id)
    balances = apply_settlements(
        balances,
        group_id
    )

    # Start message
    message = (
        f"💰 Balances for {group_name}\n\n"
    )

    # Display individual balances
    for member, amount in balances.items():
        if amount > 0:
            message += (
                f"🟢 {member} should receive "
                f"₹{amount:.2f}\n"
            )
        elif amount < 0:
            message += (
                f"🔴 {member} owes "
                f"₹{-amount:.2f}\n"
            )
        else:
            message += (
                f"⚪ {member} is settled\n"
            )

    # Calculate settlement suggestions
    settlements = calculate_settlements(
        balances
    )

    # Add settlement section
    if settlements:
        message += (
            "\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💸 Who Pays Whom\n\n"
        )
        for settlement in settlements:

            message += (
                f"🔴 {settlement['from']} "
                f"→ 🟢 {settlement['to']} "
                f"₹{settlement['amount']:.2f}\n"
            )
    else:
        message += (
            "\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Everyone is settled!\n"
        )

    await update.message.reply_text(
        message
    )

balance_handler = CommandHandler(
    "balance",
    balance_command
)