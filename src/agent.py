from typing import Any, Callable, Awaitable, Protocol
from dataclasses import dataclass
from openai import AsyncOpenAI
from pydantic import BaseModel
from braintrust import wrap_openai, start_span


class Tool(Protocol):
    """Protocol for agent tools."""

    name: str
    description: str
    parameters: type[BaseModel]
    execute: Callable[[Any], Awaitable[str]]


@dataclass
class AgentOptions:
    """Configuration options for the agent."""

    model: str = "gpt-4o-mini"
    system_prompt: str = "You are a helpful assistant."
    max_iterations: int = 10
    tools: list[Tool] = None
    openai_api_key: str = None


class WhileLoopAgent:
    """An agent that uses a while loop to iteratively call tools until completion."""

    def __init__(self, options: AgentOptions):
        # Wrap OpenAI client with Braintrust tracing
        # Support both Braintrust proxy and direct OpenAI connection
        import os

        api_key = options.openai_api_key
        base_url = None

        # If OPENAI_API_KEY is set, use direct connection
        # Otherwise, use Braintrust proxy with BRAINTRUST_API_KEY
        if os.getenv("OPENAI_API_KEY"):
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = None  # Use default OpenAI endpoint
        else:
            api_key = api_key or os.getenv("BRAINTRUST_API_KEY")
            base_url = "https://api.braintrust.dev/v1/proxy"

        self.client = wrap_openai(
            AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
            )
        )

        self.tools = {tool.name: tool for tool in (options.tools or [])}
        self.model = options.model
        self.system_prompt = options.system_prompt
        self.max_iterations = options.max_iterations

    def _format_tools_for_openai(self) -> list[dict]:
        """Format tools for OpenAI API."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters.model_json_schema(),
                },
            }
            for tool in self.tools.values()
        ]

    async def run(self, user_message: str) -> str:
        """Run the agent with a user message."""
        with start_span(name="agent_run", type="task") as span:
            span.log(input=user_message)

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ]

            iterations = 0
            done = False

            while not done and iterations < self.max_iterations:
                iteration_num = iterations + 1

                # Trace each iteration of the while loop
                with start_span(
                    name=f"iteration_{iteration_num}",
                    type="task",
                ) as iteration_span:
                    iteration_span.log(input=messages)

                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=self._format_tools_for_openai(),
                        tool_choice="auto",
                    )

                    message = response.choices[0].message
                    messages.append(message.model_dump(exclude_unset=True))

                    iteration_span.log(output=message.model_dump(exclude_unset=True))

                    if message.tool_calls:
                        tool_results = []
                        for tool_call in message.tool_calls:
                            # Trace each tool call
                            with start_span(
                                name=tool_call.function.name,
                                type="tool",
                            ) as tool_span:
                                tool = self.tools.get(tool_call.function.name)

                                if not tool:
                                    error = f"Error: Tool {tool_call.function.name} not found"
                                    tool_span.log(error=error)
                                    tool_results.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": error,
                                    })
                                    continue

                                try:
                                    import json
                                    args = json.loads(tool_call.function.arguments)
                                    tool_span.log(input=args)

                                    # Parse args into Pydantic model
                                    validated_args = tool.parameters(**args)
                                    result = await tool.execute(validated_args)

                                    tool_span.log(output=result)

                                    tool_results.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": result,
                                    })
                                except Exception as error:
                                    tool_span.log(error=str(error))
                                    tool_results.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": f"Error executing tool: {error}",
                                    })

                        messages.extend(tool_results)
                    elif message.content:
                        done = True

                iterations += 1

            # Return the final message if we found one
            last_message = messages[-1]
            if last_message.get("role") == "assistant" and last_message.get("content"):
                content = last_message["content"]
                if isinstance(content, list):
                    content = "".join(
                        part.get("text", "") for part in content if "text" in part
                    )

                span.log(
                    output=content,
                    metrics={"total_iterations": iterations},
                )
                return content

            fallback_message = "Agent reached maximum iterations without completing the task."
            span.log(
                output=fallback_message,
                metrics={
                    "total_iterations": iterations,
                    "max_iterations_reached": 1,
                },
            )
            return fallback_message
