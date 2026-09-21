# Splitwise Pro Telegram Bot 🤖💰

A powerful Telegram bot that brings Splitwise-style expense splitting right into your chats. Track shared expenses, settle debts, and manage group finances without leaving Telegram.

## ✨ Features

- 🧠 **Natural Language Understanding** — Just type what you mean. The bot uses an LLM to decipher intent from free-form messages like *"Alice paid 500 for dinner, split it between all four of us"*
- ✅ **Confirmation Before Action** — Every LLM-parsed action is summarized back to you for confirmation before anything is saved or changed
- 👥 **Group Management** — Create groups and invite members via Telegram
- 💸 **Add Expenses** — Log expenses with a single command, split equally or by custom amounts
- ⚖️ **Smart Splitting** — Equal, percentage, exact amounts, or shares-based split
- 📊 **Balance Tracking** — Real-time balance summary for each member
- 🧾 **Settlement Suggestions** — Minimal transactions to settle all debts
- 🔔 **Reminders** — Nudge members with outstanding balances
- 📜 **Expense History** — View, edit, and delete past expenses
- 🌍 **Multi-Currency Support** — Handle multiple currencies per group

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Telegram Bot Token from @BotFather
- PostgreSQL (or SQLite for local dev)

### Installation
1. Clone: `git clone https://github.com/yourusername/splitwise-pro-bot.git`
2. Create venv: `python -m venv venv && source venv/bin/activate`
3. Install: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in values
5. Run: `python bot.py`

## 📖 Commands

| Command | Description |
|---------|-------------|
| /start | Register and start using the bot |
| /help | Shows available commands/help |
| /newgroup <name> | Create a new group |
| /deletegroup | Delete a group |
| /addmember | Add a member |
| /members | List group members |
| /removemembers | Remove a group members |
| /addexpense | Add an expense using the guided multi-line flow |
| /expenses | List expenses for a group |
| /expense | View details of a particular expensep |
| /deleteexpense | Delete an expense |
| /editexpense | Edit an existing expense |
| /balance | Calculate balances and show who owes whom |
| /settle | Calculate balances and show who owes whom |

## 📄 License
MIT
