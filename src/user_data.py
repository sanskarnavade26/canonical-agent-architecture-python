from dataclasses import dataclass
from datetime import datetime


@dataclass
class Subscription:
    """User subscription information."""

    plan: str  # "basic" | "premium" | "free"
    status: str  # "active" | "expired"
    expires: str


@dataclass
class User:
    """User model."""

    id: int
    name: str
    email: str
    subscription: Subscription
    last_login: str


# Mock user database
mock_users: list[User] = [
    User(
        id=1,
        name="John Smith",
        email="john@co.com",
        subscription=Subscription(
            plan="premium",
            status="active",
            expires="2025-01-15T08:30:00Z",
        ),
        last_login="2024-03-20T14:22:00Z",
    ),
    User(
        id=2,
        name="Jane Doe",
        email="jane@co.com",
        subscription=Subscription(
            plan="basic",
            status="active",
            expires="2024-08-20T10:15:00Z",
        ),
        last_login="2024-03-19T09:45:00Z",
    ),
    User(
        id=3,
        name="Bob Wilson",
        email="bob@co.com",
        subscription=Subscription(
            plan="premium",
            status="expired",
            expires="2024-02-01T12:00:00Z",
        ),
        last_login="2024-01-30T16:00:00Z",
    ),
]


def format_date(date_str: str) -> str:
    """Format a date string to a human-readable relative time."""
    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    now = datetime.now(date.tzinfo)
    diff = now - date
    days = diff.days

    if days == 0:
        return "today"
    elif days == 1:
        return "yesterday"
    elif days < 7:
        return f"{days} days ago"
    else:
        return date.strftime("%d/%m/%Y")
