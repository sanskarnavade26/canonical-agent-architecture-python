import asyncio
import os
from dotenv import load_dotenv
import braintrust

from src.agent import WhileLoopAgent, AgentOptions
from src.tools import get_all_tools


# Load environment variables
load_dotenv()


async def main():
    """Run the customer service agent demo."""
    # Initialize Braintrust logger with experiment name
    logger = braintrust.init(
        project="canonical-agent-customer-service",
        experiment="interactive-queries"
    )

    agent = WhileLoopAgent(
        AgentOptions(
            model="gpt-4o-mini",
            system_prompt="""You are a helpful customer service agent. You can:

1. Search for users by name, email, or subscription details
2. Get detailed information about specific users
3. Send email notifications to customers
4. Update subscription plans and statuses

Always be polite and helpful. When you need more information, ask clarifying questions.
When you complete an action, summarize what you did for the customer.""",
            tools=get_all_tools(),
            max_iterations=10,
            openai_api_key=os.getenv("BRAINTRUST_API_KEY"),
        )
    )

    queries = [
        "Find all premium users with expired subscriptions",
        "Get details for john@co.com and send them a renewal reminder",
        "Cancel the subscription for jane@co.com",
        "Search for users with basic plans",
        "Find all premium users with active subscriptions and send them a thank you email",
    ]

    print("🤖 Customer Service Agent Demo")
    print("================================\n")

    for query in queries:
        print(f"Query: {query}")
        response = await agent.run(query)
        print(f"Response: {response}")
        print("---\n")


if __name__ == "__main__":
    asyncio.run(main())
