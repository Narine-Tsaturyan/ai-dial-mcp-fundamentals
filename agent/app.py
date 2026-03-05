import asyncio
import os
import pprint

from agent.mcp_client import MCPClient
from agent.dial_client import DialClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT

async def main():
    async with MCPClient("http://localhost:8005/mcp") as mcp_client:
        # 1. Get resources (optional, for debug)
        resources = await mcp_client.get_resources()
        print("Resources:", resources)

        # 2. Get tools and print raw response
        tools_response = await mcp_client.get_tools()
        print("DEBUG tools_response:")
        pprint.pprint(tools_response)

        # 3. Extract the actual list of tools
        if isinstance(tools_response, dict) and "tools" in tools_response:
            tools = tools_response["tools"]
        else:
            tools = tools_response

        # 4. Convert tool objects to dicts and filter out meta fields
        filtered_tools = []
        for tool in tools:
            # If it's a tuple, get the first element
            if isinstance(tool, tuple):
                tool = tool[0]
            # If it's not a dict, try to convert to dict
            if not isinstance(tool, dict) and hasattr(tool, "model_dump"):
                tool = tool.model_dump()
            if isinstance(tool, dict) and tool.get("name") not in ("meta", "nextCursor", "tools"):
                filtered_tools.append(tool)
        print("Filtered tools:", [tool.get("name") for tool in filtered_tools])

        # 5. Convert to OpenAI/DIAL tool format
        openai_tools = []
        for tool in filtered_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            })
        print("OpenAI tools:", [t["function"]["name"] for t in openai_tools])

        # 6. Create DialClient with OpenAI tools
        dial_client = DialClient(
            api_key=os.getenv("DIAL_API_KEY", "dial-kqibp66vnaqthq1nnve8gzqynij"),
            endpoint=os.getenv("DIAL_ENDPOINT", "https://ai-proxy.lab.epam.com"),
            tools=openai_tools,
            mcp_client=mcp_client
        )

        # 7. Prepare messages
        messages = [Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)]

        # 8. Add prompts from MCP server as User messages
        prompts = await mcp_client.get_prompts()
        for prompt in prompts:
            prompt_name = prompt[0] if isinstance(prompt, tuple) else getattr(prompt, "name", None)
            if prompt_name not in ("meta", "nextCursor", "tools", "prompts") and prompt_name is not None:
                try:
                    prompt_content = await mcp_client.get_prompt(prompt_name)
                    messages.append(Message(role=Role.USER, content=prompt_content))
                except Exception as e:
                    print(f"Warning: Could not fetch prompt '{prompt_name}': {e}")

        print("User Management Agent. Type 'exit' to quit.")
        while True:
            user_input = input("> ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            messages.append(Message(role=Role.USER, content=user_input))
            assistant_response = await dial_client.get_completion(messages)
            messages.append(assistant_response)
            print(f"Assistant: {assistant_response.content}")

if __name__ == "__main__":
    asyncio.run(main())