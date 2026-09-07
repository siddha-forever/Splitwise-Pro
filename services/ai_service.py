import json
import requests

# Assuming you have OPENROUTER_API_KEY in your config
from config import OPENROUTER_API_KEY

# Optional: Set these if you want to track usage on OpenRouter
SITE_URL = ""  # Your site URL
SITE_NAME = ""  # Your site name

SYSTEM_PROMPT = """
You are an AI assistant for a personal Splitwise-like expense manager.

Your job is to understand the user's natural language and convert it into
a structured intent.

The application currently supports:

1. Adding expenses
2. Checking balances
3. Listing expenses
4. Viewing a specific expense
5. Deleting an expense
6. Editing an expense
7. General help / conversation

IMPORTANT:
- Do NOT perform database operations.
- Do NOT invent information.
- Extract only information explicitly provided by the user.
- If information is missing, leave the field as null.
- The user's name will be supplied separately by the application.
- Amounts should be returned as numbers.
- For Indian currency, remove symbols such as ₹.
- Understand normal conversational language.

Examples:

User:
"I paid 1500 for dinner in GoaTrip"

Return:
{
    "intent": "add_expense",
    "group_name": "GoaTrip",
    "description": "Dinner",
    "amount": 1500,
    "paid_by": null,
    "expense_id": null
}

User:
"I paid 2000 for dinner in GoaTrip"

Return:
{
    "intent": "add_expense",
    "group_name": "GoaTrip",
    "description": "Dinner",
    "amount": 2000,
    "paid_by": null,
    "expense_id": null
}

User:
"How much do I owe in GoaTrip?"

Return:
{
    "intent": "balance",
    "group_name": "GoaTrip",
    "description": null,
    "amount": null,
    "paid_by": null,
    "expense_id": null
}

User:
"Show me the expenses in GoaTrip"

Return:
{
    "intent": "expenses",
    "group_name": "GoaTrip",
    "description": null,
    "amount": null,
    "paid_by": null,
    "expense_id": null
}

User:
"Show expense 12"

Return:
{
    "intent": "expense_detail",
    "group_name": null,
    "description": null,
    "amount": null,
    "paid_by": null,
    "expense_id": 12
}

User:
"Delete expense 12"

Return:
{
    "intent": "delete_expense",
    "group_name": null,
    "description": null,
    "amount": null,
    "paid_by": null,
    "expense_id": 12
}

User:
"Change expense 12 amount to 2500"

Return:
{
    "intent": "edit_expense",
    "group_name": null,
    "description": null,
    "amount": 2500,
    "paid_by": null,
    "expense_id": 12
}

For messages that are not related to expense management:

{
    "intent": "chat",
    "group_name": null,
    "description": null,
    "amount": null,
    "paid_by": null,
    "expense_id": null
}

Allowed intents:

add_expense
balance
expenses
expense_detail
delete_expense
edit_expense
chat
"""


def understand_message(user_message: str, user_name: str) -> dict:
    """
    Convert natural language into a structured expense-management intent.
    """

    prompt = f"""
User name: {user_name}

User message:
{user_message}

Remember:
If the user says "I paid", "I spent", "I paid for", etc.,
the paid_by field should normally be null because the application
will assume the current Telegram user is the payer.

Return ONLY valid JSON.
"""

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Add optional headers if provided
    if SITE_URL:
        headers["HTTP-Referer"] = SITE_URL
    if SITE_NAME:
        headers["X-OpenRouter-Title"] = SITE_NAME

    # Prepare the request payload for chat completion
    payload = {
        "model": "liquid/lfm-2.5-2.6b:free",  # Now using the correct chat model
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {
            "type": "json_object"  # This model supports structured output
        }
    }

    # Use chat completions endpoint
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",  # Correct endpoint
        headers=headers,
        data=json.dumps(payload)
    )

    # Check if request was successful
    response.raise_for_status()
    
    # Parse the response
    response_data = response.json()
    
    # Extract the content from the response
    result_text = response_data["choices"][0]["message"]["content"]
    
    # Parse the JSON content
    result = json.loads(result_text)

    return result