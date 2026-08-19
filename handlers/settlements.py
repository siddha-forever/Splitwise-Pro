from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from database import (
    get_group_id,
    create_settlement,
)

from services.balance_service import (
    calculate_balances,
    calculate_settlements,
    apply_settlements
)

# -----------------------------
# Conversation states
# -----------------------------

SELECT_SETTLEMENT = 1
CONFIRM_SETTLEMENT = 2


# -----------------------------
# /settle GroupName
# -----------------------------
async def settle_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
    ):
    # Check command format
    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/settle GroupName"
        )
        return ConversationHandler.END

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

        return ConversationHandler.END

    # Calculate current balances
    balances = calculate_balances(group_id)
    # Apply settlements that have already been recorded
    balances = apply_settlements(
        balances,
        group_id
    )

    # Calculate settlement suggestions from the current outstanding balances
    settlements = calculate_settlements(balances)

    if not settlements:
        await update.message.reply_text(
            "✅ Everyone is already settled!"
        )
        return ConversationHandler.END

    # Save information for the conversation
    context.user_data["settle_group_id"] = group_id
    context.user_data["settle_group_name"] = group_name
    context.user_data["settlements"] = settlements

    # Display available settlements
    message = (
        f"💸 Settlements for {group_name}\n\n"
        "Which payment has been made?\n\n"
    )

    for index, settlement in enumerate(
        settlements,
        start=1
        ):

        message += (
            f"{index}️⃣ "
            f"{settlement['from']} → "
            f"{settlement['to']} "
            f"₹{settlement['amount']:.2f}\n"
        )

    message += (
        "\nReply with the payment number.\n"
        "Example: 1\n\n"
        "Use /cancel to cancel."
    )

    await update.message.reply_text(
        message
    )

    return SELECT_SETTLEMENT


# -----------------------------
# Select settlement
# -----------------------------
async def select_settlement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
    ):
    text = update.message.text.strip()

    # Get stored settlements
    settlements = context.user_data.get(
        "settlements"
    )

    if not settlements:
        await update.message.reply_text(
            "❌ No settlement selection is active."
        )
        return ConversationHandler.END

    # Validate number
    try:
        selection = int(text)

    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid payment number."
        )
        return SELECT_SETTLEMENT

    # Validate range
    if selection < 1 or selection > len(settlements):
        await update.message.reply_text(
            f"❌ Please choose a number between "
            f"1 and {len(settlements)}."
        )
        return SELECT_SETTLEMENT

    # Get selected settlement
    selected = settlements[selection - 1]

    # Save selected settlement
    context.user_data["selected_settlement"] = selected

    message = (
        "💸 Confirm Settlement\n\n"
        f"👤 From: {selected['from']}\n"
        f"👤 To: {selected['to']}\n"
        f"💰 Amount: ₹{selected['amount']:.2f}\n\n"
        "Has this payment actually been made?\n\n"
        "Reply YES to confirm\n"
        "Reply NO to cancel"
    )

    await update.message.reply_text(
        message
    )

    return CONFIRM_SETTLEMENT


# -----------------------------
# Confirm settlement
# -----------------------------
async def confirm_settlement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    answer = update.message.text.strip().upper()
    # Cancel
    if answer == "NO":
        context.user_data.pop(
            "selected_settlement",
            None
        )
        context.user_data.pop(
            "settlements",
            None
        )
        context.user_data.pop(
            "settle_group_id",
            None
        )
        context.user_data.pop(
            "settle_group_name",
            None
        )
        await update.message.reply_text(
            "❌ Settlement cancelled."
        )
        return ConversationHandler.END

    # Invalid response
    if answer != "YES":
        await update.message.reply_text(
            "Please reply with YES or NO."
        )
        return CONFIRM_SETTLEMENT

    # Get stored data
    settlement = context.user_data.get(
        "selected_settlement"
    )

    group_id = context.user_data.get(
        "settle_group_id"
    )

    if settlement is None or group_id is None:
        await update.message.reply_text(
            "❌ Settlement information not found."
        )
        return ConversationHandler.END

    # Create settlement in database
    settlement_id = create_settlement(
        group_id,
        settlement["from"],
        settlement["to"],
        settlement["amount"]
    )
    # Clean up conversation data
    context.user_data.pop(
        "selected_settlement",
        None
    )
    context.user_data.pop(
        "settlements",
        None
    )
    context.user_data.pop(
        "settle_group_id",
        None
    )
    context.user_data.pop(
        "settle_group_name",
        None
    )
    await update.message.reply_text(
        "✅ Settlement recorded!\n\n"
        f"👤 {settlement['from']} paid "
        f"{settlement['to']}\n"
        f"💰 ₹{settlement['amount']:.2f}\n\n"
        f"Settlement ID: #{settlement_id}"
    )
    return ConversationHandler.END

# -----------------------------
# Cancel settlement
# -----------------------------
async def cancel_settlement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.pop(
        "selected_settlement",
        None
    )
    context.user_data.pop(
        "settlements",
        None
    )
    context.user_data.pop(
        "settle_group_id",
        None
    )
    context.user_data.pop(
        "settle_group_name",
        None
    )
    await update.message.reply_text(
        "❌ Settlement cancelled."
    )

    return ConversationHandler.END


# -----------------------------
# Settlement ConversationHandler
# -----------------------------
settlement_handler = ConversationHandler(
    entry_points=[
        CommandHandler(
            "settle",
            settle_command
        )
    ],
    states={

        SELECT_SETTLEMENT: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                select_settlement
            )

        ],
        CONFIRM_SETTLEMENT: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                confirm_settlement
            )
        ],

    },
    fallbacks=[
        CommandHandler(
            "cancel",
            cancel_settlement
        )
    ]
)