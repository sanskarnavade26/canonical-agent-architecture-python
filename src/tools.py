from dataclasses import dataclass
from pydantic import BaseModel, Field

from .user_service import (
    UserService,
    NotifyUserParams,
    SearchUsersParams,
    UpdateSubscriptionParams,
)


# Tool parameter schemas using Pydantic
class NotifyCustomerSchema(BaseModel):
    """Schema for notify_customer tool."""

    customerEmail: str = Field(..., description="Customer's email address")
    message: str = Field(..., description="The update message to send to the customer")


class SearchUsersSchema(BaseModel):
    """Schema for search_users tool."""

    query: str | None = Field(
        None, description="Search query to match against user names or emails"
    )
    subscriptionPlan: str | None = Field(None, description="Filter by subscription plan")
    subscriptionStatus: str | None = Field(
        None, description="Filter by subscription status"
    )


class GetUserDetailsSchema(BaseModel):
    """Schema for get_user_details tool."""

    email: str = Field(..., description="User's email address")


class UpdateSubscriptionSchema(BaseModel):
    """Schema for update_subscription tool."""

    email: str = Field(..., description="Customer's email address")
    plan: str | None = Field(None, description="New subscription plan")
    action: str | None = Field(None, description="Action to take on subscription")


# Tool definitions
@dataclass
class Tool:
    """Base tool class."""

    name: str
    description: str
    parameters: type[BaseModel]
    execute: callable


async def notify_customer_execute(args: NotifyCustomerSchema) -> str:
    """Execute notify_customer tool."""
    result = await UserService.notify_user(
        NotifyUserParams(email=args.customerEmail, message=args.message)
    )
    return result.message


notify_customer_tool = Tool(
    name="notify_customer",
    description="Send a notification email to a customer about their order or account",
    parameters=NotifyCustomerSchema,
    execute=notify_customer_execute,
)


async def search_users_execute(args: SearchUsersSchema) -> str:
    """Execute search_users tool."""
    result = await UserService.search_users(
        SearchUsersParams(
            query=args.query,
            subscription_plan=args.subscriptionPlan,
            subscription_status=args.subscriptionStatus,
        )
    )
    return (
        result.formatted
        + "\n\nNeed more details? Use 'get_user_details' with the user's email."
    )


search_users_tool = Tool(
    name="search_users",
    description="Search for users by various criteria",
    parameters=SearchUsersSchema,
    execute=search_users_execute,
)


async def get_user_details_execute(args: GetUserDetailsSchema) -> str:
    """Execute get_user_details tool."""
    result = await UserService.get_user_details(args.email)
    return (
        result.formatted
        + """

Actions available:
- Use 'notify_customer' to send them an email
- Use 'update_subscription' to modify their plan"""
    )


get_user_details_tool = Tool(
    name="get_user_details",
    description="Get detailed information about a specific user",
    parameters=GetUserDetailsSchema,
    execute=get_user_details_execute,
)


async def update_subscription_execute(args: UpdateSubscriptionSchema) -> str:
    """Execute update_subscription tool."""
    result = await UserService.update_subscription(
        UpdateSubscriptionParams(
            email=args.email,
            plan=args.plan,
            action=args.action,
        )
    )
    return result.message


update_subscription_tool = Tool(
    name="update_subscription",
    description="Update a customer's subscription plan or status",
    parameters=UpdateSubscriptionSchema,
    execute=update_subscription_execute,
)


def get_all_tools() -> list[Tool]:
    """Get all available tools."""
    return [
        notify_customer_tool,
        search_users_tool,
        get_user_details_tool,
        update_subscription_tool,
    ]
