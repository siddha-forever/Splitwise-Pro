from database import (
    get_group_expenses,
    get_expense_splits,
    get_group_settlements
)


def calculate_balances(group_id):
    balances = {}
    expenses = get_group_expenses(group_id)

    for expense in expenses:
        expense_id = expense[0]
        amount = expense[2]
        paid_by = expense[3]

        if paid_by not in balances:
            balances[paid_by] = 0

        balances[paid_by] += amount

        splits = get_expense_splits(expense_id)

        for member, share in splits:

            if member not in balances:
                balances[member] = 0

            balances[member] -= share

    return balances


# Convert net balances into the minimum practical
# set of payments between members.
# Positive balance  -> member should receive money
# Negative balance  -> member owes money
def calculate_settlements(balances):
    creditors = []
    debtors = []

    # Separate people who should receive and people who owe
    for member, balance in balances.items():

        if balance > 0:
            creditors.append({
                "member": member,
                "amount": round(balance, 2)
            })

        elif balance < 0:
            debtors.append({
                "member": member,
                "amount": round(-balance, 2)
            })

    settlements = []

    debtor_index = 0
    creditor_index = 0

    while (
        debtor_index < len(debtors)
        and creditor_index < len(creditors)
    ):

        debtor = debtors[debtor_index]
        creditor = creditors[creditor_index]

        # Amount that can be transferred in this transaction
        amount = min(
            debtor["amount"],
            creditor["amount"]
        )
        amount = round(amount, 2)
        settlements.append({
            "from": debtor["member"],
            "to": creditor["member"],
            "amount": amount
        })

        # Reduce remaining balances
        debtor["amount"] = round(
            debtor["amount"] - amount,
            2
        )
        creditor["amount"] = round(
            creditor["amount"] - amount,
            2
        )

        # Move to next debtor if completely settled
        if debtor["amount"] <= 0.01:
            debtor_index += 1

        # Move to next creditor if completely settled
        if creditor["amount"] <= 0.01:
            creditor_index += 1

    return settlements


def apply_settlements(balances, group_id):
    """
    Adjust expense balances using recorded settlements.
    If A pays B:
        A's balance increases
        B's balance decreases
    """

    settlements = get_group_settlements(group_id)

    # Make a copy so we don't modify the original dictionary
    adjusted_balances = balances.copy()

    for settlement in settlements:
        # settlement structure:
        # id, from_member, to_member, amount, created_at
        from_member = settlement[1]
        to_member = settlement[2]
        amount = settlement[3]

        # Person who paid becomes less in debt
        if from_member in adjusted_balances:
            adjusted_balances[from_member] += amount

        # Person who received is owed less
        if to_member in adjusted_balances:
            adjusted_balances[to_member] -= amount

    # Avoid tiny floating point values such as -0.0000001
    for member in adjusted_balances:
        if abs(adjusted_balances[member]) < 0.01:
            adjusted_balances[member] = 0.0
        else:
            adjusted_balances[member] = round(
                adjusted_balances[member],
                2
            )

    return adjusted_balances