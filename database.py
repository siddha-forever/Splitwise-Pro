import sqlite3
from datetime import datetime

from datetime import datetime

# Name of the SQLite database file
DATABASE_NAME = "data/expense.db"


def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    """
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    """
    Creates the required tables if they do not already exist.
    """

    conn = get_connection()
    cursor = conn.cursor()

    #user table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            username TEXT,
            joined_at TEXT NOT NULL
        )
    """)

    #group table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        owner_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,

        FOREIGN KEY(owner_id) REFERENCES users(telegram_id),

        UNIQUE(name, owner_id)
    )
""")

    #group_members table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        member_name TEXT NOT NULL,

        FOREIGN KEY(group_id) REFERENCES groups(id),

        UNIQUE(group_id, member_name)
    )
""")

    #expenses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        paid_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(group_id) REFERENCES groups(id)
    )
""")

    #expense split table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_splits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_id INTEGER NOT NULL,
        member_name TEXT NOT NULL,
        share_amount REAL NOT NULL,
        FOREIGN KEY(expense_id) REFERENCES expenses(id)
    )
""")
    #settlement table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            from_member TEXT NOT NULL,
            to_member TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            created_at TEXT NOT NULL,
            CHECK (from_member <> to_member),
            FOREIGN KEY (group_id) REFERENCES groups(id)
        )
 """)

    conn.commit()
    conn.close()

    print("✅ Database initialized.")


# -----------------------------
# Creating users table
# -----------------------------
def save_user(telegram_id, first_name, username):
    """
    Inserts a new user into the database.
    If the user already exists, update their name and username.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            first_name,
            username,
            joined_at
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            username = excluded.username
    """, (
        telegram_id,
        first_name,
        username,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    print(f"✅ User saved: {first_name}")


def get_all_users():
    """
    Returns all users stored in the database.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            telegram_id,
            first_name,
            username,
            joined_at
        FROM users
    """)

    users = cursor.fetchall()

    conn.close()

    return users

# -----------------------------
# Creating group table
# -----------------------------
def create_group(group_name, owner_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO groups (
                name,
                owner_id,
                created_at
            )
            VALUES (?, ?, ?)
        """, (
            group_name,
            owner_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()

def get_groups(owner_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name
        FROM groups
        WHERE owner_id = ?
        ORDER BY name
    """, (owner_id,))

    groups = cursor.fetchall()

    conn.close()

    return groups

def delete_group(group_name, owner_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM groups
        WHERE
            name = ?
            AND owner_id = ?
    """, (
        group_name,
        owner_id
    ))

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted > 0

# -------------------
# Helper function to convert group name into database ID
# -------------------
def get_group_id(group_name, owner_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM groups
        WHERE
            name = ?
            AND owner_id = ?
    """, (
        group_name,
        owner_id
    ))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]

    return None

#add members
def add_member(group_name, owner_id, member_name):
    group_id = get_group_id(group_name, owner_id)
    if group_id is None:
        return "GROUP_NOT_FOUND"

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO group_members (
                group_id,
                member_name
            )
            VALUES (?, ?)
        """, (
            group_id,
            member_name
        ))

        conn.commit()
        return "SUCCESS"

    except sqlite3.IntegrityError:
        return "EXISTS"

    finally:
        conn.close()

#get members
def get_members(group_name, owner_id):
    group_id = get_group_id(group_name, owner_id)
    if group_id is None:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT member_name
        FROM group_members
        WHERE group_id = ?
        ORDER BY member_name
    """, (group_id,))

    members = cursor.fetchall()
    conn.close()

    return members

#remove members
def remove_member(group_name, owner_id, member_name):
    group_id = get_group_id(group_name, owner_id)
    if group_id is None:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM group_members
        WHERE
            group_id = ?
            AND member_name = ?
    """, (
        group_id,
        member_name
    ))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted > 0

# -----------------------------
# Creating Expense table
# -----------------------------
def create_expense(group_id, description, amount, paid_by):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (
            group_id,
            description,
            amount,
            paid_by,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        group_id,
        description,
        amount,
        paid_by,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()

    return expense_id

#split expense:
def add_expense_split(expense_id, member_name, share_amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expense_splits (
            expense_id,
            member_name,
            share_amount
        )
        VALUES (?, ?, ?)
    """, (
        expense_id,
        member_name,
        share_amount
    ))

    conn.commit()
    conn.close()


# -------------
# Building the Expense API
# -------------
def get_expenses(group_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            description,
            amount,
            paid_by,
            created_at
        FROM expenses
        WHERE group_id = ?
        ORDER BY id DESC
    """, (group_id,))

    expenses = cursor.fetchall()

    conn.close()

    return expenses

def get_expense(expense_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            group_id,
            description,
            amount,
            paid_by,
            created_at
        FROM expenses
        WHERE id = ?
    """, (expense_id,))

    expense = cursor.fetchone()

    conn.close()

    return expense

def delete_expense(expense_id):

    conn = get_connection()
    cursor = conn.cursor()

    # Delete splits first
    cursor.execute("""
        DELETE FROM expense_splits
        WHERE expense_id = ?
    """, (expense_id,))

    # Delete expense
    cursor.execute("""
        DELETE FROM expenses
        WHERE id = ?
    """, (expense_id,))

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted > 0

#splitting the expense equally as of now
def calculate_equal_split(amount, members):

    share = round(amount / len(members), 2)

    splits = []

    for member in members:
        splits.append({
            "member": member,
            "share": share
        })

    return splits


#helper function to get all members of the group
def get_member_names(group_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT member_name
        FROM group_members
        WHERE group_id = ?
        ORDER BY member_name
    """, (group_id,))

    members = [row[0] for row in cursor.fetchall()]

    conn.close()

    return members
# ------------------------
# Creating Balance Engine
# ------------------------
def get_expense_splits(expense_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            member_name,
            share_amount
        FROM expense_splits
        WHERE expense_id = ?
    """, (expense_id,))

    splits = cursor.fetchall()

    conn.close()

    return splits

def get_group_expenses(group_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            description,
            amount,
            paid_by
        FROM expenses
        WHERE group_id = ?
    """, (group_id,))

    expenses = cursor.fetchall()

    conn.close()

    return expenses

# ---------------------------
# Edit expense functionality
# ---------------------------
def update_expense_description(expense_id, description):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET description = ?
        WHERE id = ?
    """, (description, expense_id))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated > 0

#update amount
def update_expense_amount(expense_id, amount):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET amount = ?
        WHERE id = ?
    """, (amount, expense_id))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated > 0

#update paid by
def update_expense_paid_by(expense_id, paid_by):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET paid_by = ?
        WHERE id = ?
    """, (paid_by, expense_id))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated > 0

#rebuild the splits
def delete_expense_splits(expense_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM expense_splits
        WHERE expense_id = ?
    """, (expense_id,))

    conn.commit()

    conn.close()

def get_expense_split_details(expense_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            member_name,
            share_amount
        FROM expense_splits
        WHERE expense_id = ?
        ORDER BY member_name
    """, (expense_id,))

    rows = cursor.fetchall()

    conn.close()

    return rows

# -----------------------------
# Settlement Functions
# -----------------------------
def create_settlement(
    group_id,
    from_member,
    to_member,
    amount
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO settlements (
            group_id,
            from_member,
            to_member,
            amount,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        group_id,
        from_member,
        to_member,
        amount,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    settlement_id = cursor.lastrowid
    conn.close()

    return settlement_id

#after one settlement is made
def get_settlement(settlement_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            group_id,
            from_member,
            to_member,
            amount,
            created_at
        FROM settlements
        WHERE id = ?
    """, (settlement_id,))

    settlement = cursor.fetchone()
    conn.close()

    return settlement

#get all settlements
def get_group_settlements(group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            from_member,
            to_member,
            amount,
            created_at
        FROM settlements
        WHERE group_id = ?
        ORDER BY id DESC
    """, (group_id,))

    settlements = cursor.fetchall()
    conn.close()

    return settlements

#undo an incorrectly made payment
def delete_settlement(settlement_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM settlements
        WHERE id = ?
    """, (settlement_id,))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted > 0