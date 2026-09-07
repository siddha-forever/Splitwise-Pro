from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

from database import (
    get_group_id,
    get_member_names,
    create_expense,
    add_expense_split,
    calculate_equal_split,
    get_expenses,
    get_expense,
    get_expense_split_details,
)

from services.balance_service import calculate_balances
from services.ai_service import understand_message


async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    user_message = update.message.text.strip()

    if not user_message:
        return

    user = update.effective_user
    user_name = user.first_name or "User"

    # ============================================================
    # HANDLE PENDING EXPENSE CONFIRMATION
    # ============================================================

    pending_expense = context.user_data.get("ai_pending_expense")

    if pending_expense:

        answer = user_message.lower().strip()

        # --------------------------------------------------------
        # USER CONFIRMS
        # --------------------------------------------------------

        if answer in ["yes", "y", "confirm", "ok"]:

            try:
                group_id = pending_expense["group_id"]
                group_name = pending_expense["group_name"]
                description = pending_expense["description"]
                amount = pending_expense["amount"]
                paid_by = pending_expense["paid_by"]
                members = pending_expense["members"]

                # Create expense
                expense_id = create_expense(
                    group_id,
                    description,
                    amount,
                    paid_by
                )

                # Calculate equal split
                splits = calculate_equal_split(
                    amount,
                    members
                )

                # Save splits
                for split in splits:
                    add_expense_split(
                        expense_id,
                        split["member"],
                        split["share"]
                    )

                # Clear pending expense
                context.user_data.pop(
                    "ai_pending_expense",
                    None
                )

                await update.message.reply_text(
                    "✅ Expense added successfully!\n\n"
                    f"Group: {group_name}\n"
                    f"Description: {description}\n"
                    f"Amount: ₹{amount:.2f}\n"
                    f"Paid by: {paid_by}\n"
                    f"Expense ID: #{expense_id}"
                )

            except Exception as e:

                print(f"AI expense save error: {e}")

                await update.message.reply_text(
                    "❌ I understood the expense, but "
                    "couldn't save it.\n\n"
                    "Please check the terminal for the error."
                )

            return

        # --------------------------------------------------------
        # USER CANCELS
        # --------------------------------------------------------

        elif answer in ["no", "n", "cancel"]:

            context.user_data.pop(
                "ai_pending_expense",
                None
            )

            await update.message.reply_text(
                "❌ Expense cancelled."
            )

            return

        # --------------------------------------------------------
        # SOMETHING OTHER THAN YES/NO
        # --------------------------------------------------------

        else:

            await update.message.reply_text(
                "Please reply **YES** to add the expense "
                "or **NO** to cancel it.",
                parse_mode="Markdown"
            )

            return

    # ============================================================
    # AI INTERPRETATION
    # ============================================================

    try:

        intent_data = understand_message(
            user_message,
            user_name
        )

        intent = intent_data.get("intent")

        # ========================================================
        # ADD EXPENSE
        # ========================================================

        if intent == "add_expense":

            group_name = intent_data.get("group_name")
            description = intent_data.get("description")
            amount = intent_data.get("amount")
            paid_by = intent_data.get("paid_by")

            # ----------------------------------------------------
            # GROUP MISSING
            # ----------------------------------------------------

            if not group_name:

                await update.message.reply_text(
                    "I understood that you want to add an expense, "
                    "but I couldn't identify the group.\n\n"
                    "For example:\n"
                    "\"I paid ₹1500 for dinner in GoaTrip\""
                )

                return

            # ----------------------------------------------------
            # DESCRIPTION MISSING
            # ----------------------------------------------------

            if not description:

                await update.message.reply_text(
                    "What was the expense for?\n\n"
                    "For example:\n"
                    "\"I paid ₹1500 for dinner in GoaTrip\""
                )

                return

            # ----------------------------------------------------
            # AMOUNT MISSING
            # ----------------------------------------------------

            if amount is None:

                await update.message.reply_text(
                    "I couldn't identify the amount.\n\n"
                    "For example:\n"
                    "\"I paid ₹1500 for dinner in GoaTrip\""
                )

                return

            # ----------------------------------------------------
            # CONVERT AMOUNT
            # ----------------------------------------------------

            try:

                amount = float(amount)

            except (ValueError, TypeError):

                await update.message.reply_text(
                    "I couldn't understand the amount."
                )

                return

            if amount <= 0:

                await update.message.reply_text(
                    "The expense amount must be greater than ₹0."
                )

                return

            # ----------------------------------------------------
            # DEFAULT PAYER = CURRENT USER
            # ----------------------------------------------------

            if not paid_by:

                paid_by = user_name

            # ----------------------------------------------------
            # FIND GROUP
            # ----------------------------------------------------

            group_id = get_group_id(
                group_name,
                user.id
            )

            if group_id is None:

                await update.message.reply_text(
                    f"I couldn't find a group named "
                    f"'{group_name}'."
                )

                return

            # ----------------------------------------------------
            # GET MEMBERS
            # ----------------------------------------------------

            members = get_member_names(group_id)

            if not members:

                await update.message.reply_text(
                    f"The group '{group_name}' has no members."
                )

                return

            # ----------------------------------------------------
            # VALIDATE PAYER
            # ----------------------------------------------------

            if paid_by not in members:

                await update.message.reply_text(
                    f"I understood that {paid_by} paid the expense, "
                    f"but {paid_by} is not a member of "
                    f"{group_name}.\n\n"
                    f"Members: {', '.join(members)}"
                )

                return

            # ----------------------------------------------------
            # CALCULATE SPLIT
            # ----------------------------------------------------

            splits = calculate_equal_split(
                amount,
                members
            )

            # ----------------------------------------------------
            # STORE PENDING EXPENSE
            # ----------------------------------------------------

            context.user_data["ai_pending_expense"] = {

                "group_id": group_id,

                "group_name": group_name,

                "description": description,

                "amount": amount,

                "paid_by": paid_by,

                "members": members,

            }

            # ----------------------------------------------------
            # BUILD SPLIT DISPLAY
            # ----------------------------------------------------

            split_text = ""
            for split in splits:
                split_text += (
                    f"{split['member'   ]}: "
                    f"{split['share']: .2f}\n"
                )

            # ----------------------------------------------------
            # CONFIRMATION MESSAGE
            # ----------------------------------------------------

            await update.message.reply_text(

                "🧾 I understood:\n\n"

                f"Group: {group_name}\n"
                f"Description: {description}\n"
                f"Amount: ₹{amount:.2f}\n"
                f"Paid by: {paid_by}\n\n"

                "Split:\n"
                f"{split_text}\n"

                "Should I add this expense?\n"
                "Reply YES or NO."

            )

            return

        # ========================================================
        # BALANCE
        # ========================================================

        elif intent == "balance":

            group_name = intent_data.get("group_name")

            if not group_name:

                await update.message.reply_text(
                    "Which group would you like to check?"
                )

                return

            group_id = get_group_id(
                group_name,
                user.id
            )

            if group_id is None:

                await update.message.reply_text(
                    f"I couldn't find a group named "
                    f"'{group_name}'."
                )

                return

            balances = calculate_balances(group_id)

            message = (
                f"💰 Balance for {group_name}\n\n"
            )

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

            await update.message.reply_text(message)

            return

        # ========================================================
        # EXPENSE LIST
        # ========================================================

        elif intent == "expenses":

            group_name = intent_data.get("group_name")

            if not group_name:

                await update.message.reply_text(
                    "Which group's expenses should I show?"
                )

                return

            group_id = get_group_id(
                group_name,
                user.id
            )

            if group_id is None:

                await update.message.reply_text(
                    f"I couldn't find a group named "
                    f"'{group_name}'."
                )

                return

            expenses = get_expenses(group_id)

            if not expenses:

                await update.message.reply_text(
                    f"There are no expenses in "
                    f"{group_name}."
                )

                return

            message = (
                f"📋 Expenses in {group_name}\n\n"
            )

            for expense in expenses:

                expense_id = expense[0]
                description = expense[1]
                amount = expense[2]
                paid_by = expense[3]

                message += (
                    f"#{expense_id} — {description}\n"
                    f"₹{amount:.2f} paid by {paid_by}\n\n"
                )

            await update.message.reply_text(message)

            return

        # ========================================================
        # EXPENSE DETAIL
        # ========================================================

        elif intent == "expense_detail":

            expense_id = intent_data.get("expense_id")

            if not expense_id:

                await update.message.reply_text(
                    "Which expense would you like to see?"
                )

                return

            try:

                expense_id = int(expense_id)

            except (ValueError, TypeError):

                await update.message.reply_text(
                    "That doesn't look like a valid expense ID."
                )

                return

            expense = get_expense(expense_id)

            if not expense:

                await update.message.reply_text(
                    f"I couldn't find expense #{expense_id}."
                )

                return

            splits = get_expense_split_details(
                expense_id
            )

            message = (

                f"🧾 Expense #{expense_id}\n\n"

                f"Description: {expense[1]}\n"

                f"Amount: ₹{expense[2]:.2f}\n"

                f"Paid by: {expense[3]}\n\n"

                "Split:\n"

            )

            for member, share in splits:

                message += (
                    f"• {member}: ₹{share:.2f}\n"
                )

            await update.message.reply_text(message)

            return

        # ========================================================
        # DELETE EXPENSE
        # ========================================================

        elif intent == "delete_expense":

            expense_id = intent_data.get(
                "expense_id"
            )

            await update.message.reply_text(

                "I understand that you want to delete "
                f"expense #{expense_id}.\n\n"

                "For safety, please use:\n"

                f"/deleteexpense {expense_id}"

            )

            return

        # ========================================================
        # EDIT EXPENSE
        # ========================================================

        elif intent == "edit_expense":

            expense_id = intent_data.get(
                "expense_id"
            )

            await update.message.reply_text(

                "I understand that you want to edit "
                f"expense #{expense_id}.\n\n"

                "For now, please use:\n"

                f"/editexpense {expense_id}"

            )

            return

        # ========================================================
        # GENERAL CHAT
        # ========================================================

        else:

            await update.message.reply_text(

                "I can help you manage your expenses.\n\n"

                "Try saying things like:\n\n"

                "• \"I paid ₹1500 for dinner in GoaTrip\"\n"

                "• \"How much do I owe in GoaTrip?\"\n"

                "• \"Show my expenses in GoaTrip\"\n"

                "• \"Show expense 12\"\n"

                "• \"Delete expense 12\""

            )

    except Exception as e:

        print(
            f"AI chat error: {e}"
        )

        await update.message.reply_text(
            "Sorry, I couldn't process that message right now."
        )


# ================================================================
# AI CHAT HANDLER
# ================================================================

ai_chat_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    ai_chat
)