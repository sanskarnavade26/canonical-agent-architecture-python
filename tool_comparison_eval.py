"""Tool comparison evaluation.

Compares the performance of purpose-built specific tools vs generic API wrapper tools.
This demonstrates why specific tools lead to better agent performance.
"""

import asyncio
import os
from dotenv import load_dotenv
from braintrust import EvalAsync
import braintrust

from src.agent import WhileLoopAgent, AgentOptions
from src.tools import get_all_tools
from src.generic_tools import get_generic_tools

load_dotenv()

# Test cases for evaluation
test_cases = [
    {
        "input": "Find all premium users and notify them about a new feature launch",
        "expected": {
            "success_criteria": [
                "Found premium users",
                "Sent notifications to premium users",
                "john@co.com",
                "bob@co.com",
            ],
            "required_actions": ["search", "notify"],
        },
        "metadata": {
            "category": "multi-step",
            "difficulty": "medium",
        },
    },
    {
        "input": "Check if jane@co.com is an active subscriber and what plan they have",
        "expected": {
            "success_criteria": ["Jane Doe", "jane@co.com", "active", "basic"],
            "required_actions": ["lookup"],
        },
        "metadata": {
            "category": "single-lookup",
            "difficulty": "easy",
        },
    },
    {
        "input": "Find users with expired subscriptions and send them renewal reminders with a special offer",
        "expected": {
            "success_criteria": ["expired", "Bob Wilson", "renewal", "reminder"],
            "required_actions": ["search", "notify"],
        },
        "metadata": {
            "category": "multi-step",
            "difficulty": "medium",
        },
    },
    {
        "input": "Upgrade jane@co.com to premium plan and send confirmation",
        "expected": {
            "success_criteria": ["upgrade", "premium", "jane@co.com", "confirmation"],
            "required_actions": ["update", "notify"],
        },
        "metadata": {
            "category": "multi-step",
            "difficulty": "medium",
        },
    },
    {
        "input": "List all active users sorted by subscription type",
        "expected": {
            "success_criteria": ["John Smith", "Jane Doe", "active", "premium", "basic"],
            "required_actions": ["search"],
        },
        "metadata": {
            "category": "single-lookup",
            "difficulty": "easy",
        },
    },
]


# Scorer for checking if the agent accomplished the task
def task_success_scorer(output: str, expected: dict) -> dict:
    """Score based on whether success criteria were met."""
    if not expected or not expected.get("success_criteria"):
        return None

    success_criteria = expected["success_criteria"]
    found_criteria = [
        criteria
        for criteria in success_criteria
        if criteria.lower() in output.lower()
    ]

    score = len(found_criteria) / len(success_criteria)

    return {
        "name": "task_success",
        "score": score,
        "metadata": {
            "expected_criteria": success_criteria,
            "found_criteria": found_criteria,
            "missing_criteria": [c for c in success_criteria if c not in found_criteria],
        },
    }


# Scorer for response clarity
def clarity_scorer(output: str) -> dict:
    """Score based on clarity and structure of response."""
    # Check for clear, structured responses
    has_structure = "\n" in output or "•" in output or "-" in output
    has_confirmation = (
        "✓" in output or "successfully" in output.lower() or "completed" in output.lower()
    )
    is_verbose = len(output) > 1000
    has_json = "{" in output and "}" in output
    has_raw_data = (
        "query_id" in output
        or "request_id" in output
        or "transaction_id" in output
        or "execution_time_ms" in output
    )
    has_error = "Error:" in output or "error" in output.lower()

    score = 0.5
    if (
        has_structure
        and has_confirmation
        and not is_verbose
        and not has_json
        and not has_raw_data
        and not has_error
    ):
        score = 1.0
    elif (has_structure or has_confirmation) and not has_error:
        score = 0.7
    elif has_json or is_verbose or has_raw_data or has_error:
        score = 0.3

    return {
        "name": "clarity",
        "score": score,
        "metadata": {
            "has_structure": has_structure,
            "has_confirmation": has_confirmation,
            "is_verbose": is_verbose,
            "has_json": has_json,
            "has_raw_data": has_raw_data,
            "has_error": has_error,
            "response_length": len(output),
        },
    }


# Same system prompt for both evaluations
SYSTEM_PROMPT = """You are a customer service assistant. Help users manage customer accounts and subscriptions.

When asked to find and notify users:
- First find the relevant users
- Then send notifications to each user
- Be specific about what actions you're taking
- Provide clear confirmation of completed tasks"""


# Task function for specific tools
async def run_with_specific_tools(input_text: str) -> str:
    """Run agent with purpose-built specific tools."""
    agent = WhileLoopAgent(
        AgentOptions(
            tools=get_all_tools(),
            system_prompt=SYSTEM_PROMPT,
            max_iterations=10,
            openai_api_key=os.getenv("BRAINTRUST_API_KEY"),
        )
    )
    return await agent.run(input_text)


# Task function for generic tools
async def run_with_generic_tools(input_text: str) -> str:
    """Run agent with generic API wrapper tools."""
    agent = WhileLoopAgent(
        AgentOptions(
            tools=get_generic_tools(),
            system_prompt=SYSTEM_PROMPT,
            max_iterations=10,
            openai_api_key=os.getenv("BRAINTRUST_API_KEY"),
        )
    )
    return await agent.run(input_text)


async def main_async():
    """Run the tool comparison evaluation."""
    # Initialize Braintrust
    braintrust.init(project="canonical-agent-customer-service")

    # Evaluation with specific tools
    await EvalAsync(
        "canonical-agent-customer-service",
        experiment_name="specific-tools",
        data=test_cases,
        task=run_with_specific_tools,
        scores=[task_success_scorer, clarity_scorer],
        metadata={
            "description": "Evaluation using purpose-built, specific tools",
            "tool_type": "specific",
        },
    )

    # Evaluation with generic tools
    await EvalAsync(
        "canonical-agent-customer-service",
        experiment_name="generic-tools",
        data=test_cases,
        task=run_with_generic_tools,
        scores=[task_success_scorer, clarity_scorer],
        metadata={
            "description": "Evaluation using generic API wrapper tools",
            "tool_type": "generic",
        },
    )

    print("✅ Tool comparison evaluation complete!")
    print("View results at: https://www.braintrust.dev/app")


if __name__ == "__main__":
    # Run with proper async context to avoid cleanup errors
    asyncio.run(main_async())
