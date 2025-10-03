"""Generic tools - intentionally over-engineered examples of what NOT to do.

These tools are designed to demonstrate the problems with generic API wrappers:
- Too many parameters that confuse the agent
- Complex abstractions that don't match the agent's mental model
- Error-prone with lots of failure modes
- Return unhelpful, overly technical output
"""

from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import Literal, Any
import json

from .user_service import UserService


# ❌ Generic query tool with too many parameters
class QueryDataSchema(BaseModel):
    """Generic data query schema - confusing for agents."""

    source: str = Field(..., description="Data source to query (e.g., 'users', 'orders', 'products')")
    operation: Literal["find", "findOne", "count", "aggregate"] = Field(
        ..., description="Query operation type"
    )
    filters: dict[str, Any] | None = Field(None, description="Filter criteria as key-value pairs")
    projection: list[str] | None = Field(None, description="Fields to include in response")
    sort: dict[str, int] | None = Field(None, description="Sort order (-1 for desc, 1 for asc)")
    limit: int | None = Field(None, description="Maximum number of results")
    skip: int | None = Field(None, description="Number of results to skip")
    includeMetadata: bool | None = Field(None, description="Include query metadata in response")
    cacheControl: Literal["no-cache", "cache", "cache-and-refresh"] | None = None
    timeout: int | None = Field(None, description="Query timeout in milliseconds")


async def query_data_execute(args: QueryDataSchema) -> str:
    """Execute generic query - intentionally error-prone."""
    # Fail if wrong source
    if args.source != "users":
        return f"Error: Data source '{args.source}' not found. Available sources: users"

    # Fail if wrong operation
    if args.operation != "find":
        return f"Error: Operation '{args.operation}' not supported for user queries. Use 'find' instead."

    # Convert generic filters to specific search params
    subscription_plan = None
    subscription_status = None

    if args.filters:
        if args.filters.get("subscription_plan") in ["basic", "premium"]:
            subscription_plan = args.filters["subscription_plan"]
        if args.filters.get("subscription_status") in ["active", "expired"]:
            subscription_status = args.filters["subscription_status"]

    from .user_service import SearchUsersParams

    result = await UserService.search_users(
        SearchUsersParams(
            query=str(args.filters.get("query")) if args.filters and args.filters.get("query") else None,
            subscription_plan=subscription_plan,
            subscription_status=subscription_status,
        )
    )

    # Return overly verbose response if metadata is included
    if args.includeMetadata:
        return json.dumps({
            "query_metadata": {
                "execution_time_ms": 23,
                "source": args.source,
                "operation": args.operation,
                "filters_applied": list(args.filters.keys()) if args.filters else [],
                "cache_hit": False,
            },
            "result_count": len(result.users),
            "results": [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "subscription": {
                        "plan": u.subscription.plan,
                        "status": u.subscription.status,
                    }
                }
                for u in result.users
            ],
        })

    return (
        result.formatted
        + "\n\nNeed more details? Use 'query_data' with operation='findOne' and the user's email."
    )


# ❌ Generic communication tool with too many options
class SendMessageSchema(BaseModel):
    """Generic message sending schema - too many channels and options."""

    channel: Literal["email", "sms", "push", "in-app", "webhook"] = Field(
        ..., description="Communication channel"
    )
    recipient: str = Field(..., description="Recipient identifier (email, phone, user ID, etc.)")
    content: str = Field(..., description="Message content")
    subject: str | None = Field(None, description="Message subject (for email)")
    template: str | None = Field(None, description="Template ID to use")
    variables: dict[str, str] | None = Field(None, description="Template variables")
    priority: Literal["low", "normal", "high", "urgent"] | None = None
    scheduling: dict[str, str] | None = None
    tracking: dict[str, bool] | None = None
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")


async def send_message_execute(args: SendMessageSchema) -> str:
    """Execute generic message sending - error-prone."""
    # Only email channel works properly
    if args.channel != "email":
        return f"Error: Channel '{args.channel}' is not configured. Please use 'email'."

    # Fail on high priority without proper setup
    if args.priority and args.priority != "normal":
        return f"Error: Priority '{args.priority}' requires additional configuration. Use 'normal' priority."

    from .user_service import NotifyUserParams

    result = await UserService.notify_user(
        NotifyUserParams(email=args.recipient, message=args.content)
    )

    return result.message


# ❌ Generic record access tool
class AccessRecordSchema(BaseModel):
    """Generic record access schema - confusing identifier types."""

    source: str = Field(..., description="Data source (e.g., 'users', 'orders')")
    identifier: str = Field(..., description="Record identifier")
    identifierType: Literal["id", "email", "uuid", "custom"] = Field(
        ..., description="Type of identifier"
    )
    fields: list[str] | None = Field(None, description="Specific fields to retrieve")
    includeRelated: bool | None = Field(None, description="Include related records")
    format: Literal["json", "xml", "plain"] | None = Field(None, description="Response format")


async def access_record_execute(args: AccessRecordSchema) -> str:
    """Execute generic record access - error-prone."""
    if args.source != "users":
        return f"Error: Source '{args.source}' not available. Use 'users'."

    if args.identifierType != "email":
        return f"Error: Identifier type '{args.identifierType}' not supported for users. Use 'email'."

    result = await UserService.get_user_details(args.identifier)
    return (
        result.formatted
        + """

Actions available:
- Use 'send_message' to notify them
- Use 'modify_record' to update their subscription"""
    )


# ❌ Generic record modification tool
class ModifyRecordSchema(BaseModel):
    """Generic record modification schema - complex operations."""

    source: str = Field(..., description="Data source (e.g., 'users', 'orders')")
    identifier: str = Field(..., description="Record identifier")
    identifierType: Literal["id", "email", "uuid", "custom"] = Field(
        ..., description="Type of identifier"
    )
    operation: Literal["update", "patch", "replace", "merge"] = Field(
        ..., description="Modification operation"
    )
    data: dict[str, Any] = Field(..., description="Data to update")
    validate: bool | None = Field(None, description="Validate before updating")
    returnUpdated: bool | None = Field(None, description="Return the updated record")
    auditLog: bool | None = Field(None, description="Create audit log entry")


async def modify_record_execute(args: ModifyRecordSchema) -> str:
    """Execute generic record modification - error-prone."""
    if args.source != "users":
        return f"Error: Source '{args.source}' not available for modifications. Use 'users'."

    if args.identifierType != "email":
        return f"Error: Identifier type '{args.identifierType}' not supported. Use 'email'."

    if args.operation != "update":
        return f"Error: Operation '{args.operation}' not supported. Use 'update'."

    # Extract plan and action from generic data object
    plan = args.data.get("plan") if args.data.get("plan") in ["basic", "premium"] else None
    action = args.data.get("action") if args.data.get("action") in ["renew", "cancel"] else None

    from .user_service import UpdateSubscriptionParams

    result = await UserService.update_subscription(
        UpdateSubscriptionParams(
            email=args.identifier,
            plan=plan,
            action=action,
        )
    )

    return result.message


# Tool definitions
@dataclass
class Tool:
    """Tool definition."""

    name: str
    description: str
    parameters: type[BaseModel]
    execute: callable


query_data_tool = Tool(
    name="query_data",
    description="Query data from any data source",
    parameters=QueryDataSchema,
    execute=query_data_execute,
)

send_message_tool = Tool(
    name="send_message",
    description="Send a message through any communication channel",
    parameters=SendMessageSchema,
    execute=send_message_execute,
)

access_record_tool = Tool(
    name="access_record",
    description="Access a specific record from any data source",
    parameters=AccessRecordSchema,
    execute=access_record_execute,
)

modify_record_tool = Tool(
    name="modify_record",
    description="Modify a record in any data source",
    parameters=ModifyRecordSchema,
    execute=modify_record_execute,
)


def get_generic_tools() -> list[Tool]:
    """Get all generic tools (examples of what NOT to do)."""
    return [
        query_data_tool,
        send_message_tool,
        access_record_tool,
        modify_record_tool,
    ]
