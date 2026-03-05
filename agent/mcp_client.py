from typing import Optional, Any, List
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, TextContent, GetPromptResult, ReadResourceResult, Resource, TextResourceContents, BlobResourceContents, Prompt
from pydantic import AnyUrl

class MCPClient:
    def __init__(self, mcp_server_url: str) -> None:
        self.mcp_server_url = mcp_server_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

    async def __aenter__(self):
        self._streams_context = streamablehttp_client(self.mcp_server_url)
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()
        print(await self.session.initialize())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        if self._streams_context:
            await self._streams_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tools(self) -> List[Any]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        tools_response = await self.session.list_tools()
        # If it's a dict with a 'tools' key, return the list
        if isinstance(tools_response, dict) and "tools" in tools_response:
            return tools_response["tools"]
        # If it's a list, return as is
        if isinstance(tools_response, list):
            return tools_response
        # If it's something else, try to extract the list
        if hasattr(tools_response, "tools"):
            return tools_response.tools
        raise RuntimeError(f"Unknown tools response format: {tools_response}")

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
        content = tool_result.content[0]
        print(f"    ⚙️: {content}\n")
        if isinstance(content, TextContent):
            return content.text
        else:
            return content

    async def get_resources(self) -> List[Resource]:
        try:
            resources = await self.session.list_resources()
            return resources
        except Exception as e:
            print(f"Error getting resources: {e}")
            return []

    async def get_resource(self, uri: AnyUrl) -> str:
        resource = await self.session.get_resource(uri)
        content = resource.contents[0]
        if isinstance(content, TextResourceContents):
            return content.text
        elif isinstance(content, BlobResourceContents):
            return content.blob
        return ""

    async def get_prompts(self) -> List[Prompt]:
        try:
            prompts = await self.session.list_prompts()
            return prompts
        except Exception as e:
            print(f"Error getting prompts: {e}")
            return []

    async def get_prompt(self, name: str) -> str:
        prompt_result = await self.session.get_prompt(name)
        combined_content = ""
        for message in prompt_result.messages:
            if hasattr(message, "content"):
                if isinstance(message.content, TextContent):
                    combined_content += message.content.text + "\n"
                elif isinstance(message.content, str):
                    combined_content += message.content + "\n"
        return combined_content