from dataclasses import dataclass

@dataclass
class User:
    telegram_id: int
    first_name: str
    username: str


@dataclass
class Group:
    id: int
    name: str
    owner_id: int


@dataclass
class Expense:
    id: int
    group_id: int
    description: str
    amount: float
    paid_by: str
    created_at: str