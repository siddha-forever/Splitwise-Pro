from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database import initialize_database
from handlers.user import help_command
from handlers.groups import (
    new_group,
    groups,
    delete_group_command
)
from handlers.members import (
    add_member_command,
    members_command,
    remove_member_command
)
from handlers.expenses import expense_handler
from handlers.expense_management import (
    expense_management_handler,
    delete_expense_handler,
    edit_expense_handler
)
from handlers.balance import balance_handler
from handlers.settlements import settlement_handler
from handlers.menu import (
    main_menu,
    menu_button_handler
)

from config import BOT_TOKEN


def main():
    # Initialize database
    initialize_database()
    # Create Telegram application
    app = Application.builder().token(BOT_TOKEN).build()
    # --------------------------------
    # Main menu
    # --------------------------------
    app.add_handler(
        CommandHandler(
            "start",
            main_menu
        )
    )

    # --------------------------------
    # Basic commands
    # --------------------------------
    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )
    # --------------------------------
    # Group commands
    # --------------------------------
    app.add_handler(
        CommandHandler(
            "newgroup",
            new_group
        )
    )
    app.add_handler(
        CommandHandler(
            "groups",
            groups
        )
    )
    app.add_handler(
        CommandHandler(
            "deletegroup",
            delete_group_command
        )
    )

    # --------------------------------
    # Member commands
    # --------------------------------
    app.add_handler(
        CommandHandler(
            "addmember",
            add_member_command
        )
    )
    app.add_handler(
        CommandHandler(
            "members",
            members_command
        )
    )
    app.add_handler(
        CommandHandler(
            "removemember",
            remove_member_command
        )
    )

    # --------------------------------
    # Expense commands
    # --------------------------------
    app.add_handler(expense_handler)
    for handler in expense_management_handler:
        app.add_handler(handler)
    app.add_handler(delete_expense_handler)
    app.add_handler(edit_expense_handler)

    # --------------------------------
    # Balance
    # --------------------------------
    app.add_handler(balance_handler)

    # --------------------------------
    # Settlement
    # --------------------------------
    app.add_handler(settlement_handler)

    # --------------------------------
    # Menu buttons
    # --------------------------------
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_button_handler
        )
    )
    print("🤖 Expense Manager Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()