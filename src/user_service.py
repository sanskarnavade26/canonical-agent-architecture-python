import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .user_data import mock_users, User, format_date


@dataclass
class SearchUsersParams:
    """Parameters for searching users."""

    query: Optional[str] = None
    subscription_plan: Optional[str] = None  # "basic" | "premium"
    subscription_status: Optional[str] = None  # "active" | "expired"


@dataclass
class NotifyUserParams:
    """Parameters for notifying a user."""

    email: str
    message: str


@dataclass
class UpdateSubscriptionParams:
    """Parameters for updating a subscription."""

    email: str
    plan: Optional[str] = None  # "basic" | "premium"
    action: Optional[str] = None  # "renew" | "cancel"


@dataclass
class SearchUsersResult:
    """Result of searching users."""

    users: list[User]
    formatted: str


@dataclass
class UserDetailsResult:
    """Result of getting user details."""

    user: Optional[User]
    formatted: str


@dataclass
class OperationResult:
    """Generic operation result."""

    success: bool
    message: str


class UserService:
    """Service for managing users and subscriptions."""

    @staticmethod
    async def search_users(params: SearchUsersParams) -> SearchUsersResult:
        """Search for users by various criteria."""
        filtered = list(mock_users)

        if params.query:
            query_lower = params.query.lower()
            filtered = [
                u
                for u in filtered
                if query_lower in u.name.lower() or query_lower in u.email.lower()
            ]

        if params.subscription_plan:
            filtered = [
                u for u in filtered if u.subscription.plan == params.subscription_plan
            ]

        if params.subscription_status:
            filtered = [
                u
                for u in filtered
                if u.subscription.status == params.subscription_status
            ]

        if not filtered:
            return SearchUsersResult(
                users=[],
                formatted="No users found matching the criteria.",
            )

        formatted_users = []
        for i, u in enumerate(filtered, 1):
            plan_capitalized = u.subscription.plan.capitalize()
            if u.subscription.status == "active":
                expires_date = datetime.fromisoformat(
                    u.subscription.expires.replace("Z", "+00:00")
                )
                status_text = f"active until {expires_date.strftime('%d/%m/%Y')}"
            else:
                status_text = "expired"

            formatted_users.append(
                f"{i}. {u.name} ({u.email})\n"
                f"   - {plan_capitalized} subscriber ({status_text})\n"
                f"   - Last seen: {format_date(u.last_login)}"
            )

        formatted = "\n\n".join(formatted_users)
        count_text = f"{len(filtered)} user{'s' if len(filtered) != 1 else ''}"

        return SearchUsersResult(
            users=filtered,
            formatted=f"Found {count_text}:\n\n{formatted}",
        )

    @staticmethod
    async def get_user_details(email: str) -> UserDetailsResult:
        """Get detailed information about a specific user."""
        user = next((u for u in mock_users if u.email == email), None)

        if not user:
            return UserDetailsResult(
                user=None,
                formatted=f"No user found with email: {email}",
            )

        expires_date = datetime.fromisoformat(
            user.subscription.expires.replace("Z", "+00:00")
        )
        last_login_date = datetime.fromisoformat(
            user.last_login.replace("Z", "+00:00")
        )
        created_date = datetime(2024, 1, user.id * 15)

        status_label = "Expires" if user.subscription.status == "active" else "Expired"

        formatted = f"""User Details for {user.name}:

Email: {user.email}
User ID: {user.id}

Subscription:
- Plan: {user.subscription.plan}
- Status: {user.subscription.status}
- {status_label}: {expires_date.strftime('%d/%m/%Y')}

Activity:
- Last login: {last_login_date.strftime('%d/%m/%Y, %H:%M:%S')}
- Account created: {created_date.strftime('%d/%m/%Y')}"""

        return UserDetailsResult(user=user, formatted=formatted)

    @staticmethod
    async def notify_user(params: NotifyUserParams) -> OperationResult:
        """Send a notification email to a user."""
        user = next((u for u in mock_users if u.email == params.email), None)

        if not user:
            return OperationResult(
                success=False,
                message=f"❌ Failed to send notification: Customer with email {params.email} not found",
            )

        # Simulate sending email
        await asyncio.sleep(0.5)

        return OperationResult(
            success=True,
            message=f'✓ Sent update to {params.email}: "{params.message}"',
        )

    @staticmethod
    async def update_subscription(params: UpdateSubscriptionParams) -> OperationResult:
        """Update a customer's subscription plan or status."""
        user = next((u for u in mock_users if u.email == params.email), None)

        if not user:
            return OperationResult(
                success=False,
                message=f"❌ Failed to update subscription: Customer with email {params.email} not found",
            )

        updates = []

        if params.plan and params.plan != user.subscription.plan:
            user.subscription.plan = params.plan
            updates.append(f"plan changed to {params.plan}")

        if params.action == "renew":
            user.subscription.status = "active"
            new_expiry = datetime.now() + timedelta(days=365)
            user.subscription.expires = new_expiry.isoformat() + "Z"
            updates.append("subscription renewed for 1 year")
        elif params.action == "cancel":
            user.subscription.status = "expired"
            updates.append("subscription cancelled")

        if not updates:
            return OperationResult(
                success=True,
                message=f"No changes made to {user.name}'s subscription.",
            )

        return OperationResult(
            success=True,
            message=f"✓ Updated {user.name}'s subscription: {', '.join(updates)}",
        )
