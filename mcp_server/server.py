from pathlib import Path
from mcp.server.fastmcp import FastMCP
from models.user_info import UserSearchRequest, UserCreate, UserUpdate
from user_client import UserClient

# 1. Create FastMCP instance
mcp = FastMCP(
    name="users-management-mcp-server",
    host="0.0.0.0",
    port=8005,
)

# 2. Create UserClient
user_client = UserClient()

# ==================== TOOLS ====================
@mcp.tool(description="Get user by ID")
async def get_user_by_id(id: int) -> str:
    return await user_client.get_user(id)

@mcp.tool(description="Delete user by ID")
async def delete_user(id: int) -> str:
    return await user_client.delete_user(id)

@mcp.tool(description="Search users by name, surname, email, or gender")
async def search_user(name: str = None, surname:
 str = None, email: str = None, gender: str = None) -> str:
    return await user_client.search_users(name=name, surname=surname, email=email, gender=gender)

@mcp.tool(description="Add a new user")
async def add_user(user: UserCreate) -> str:
    result =  await user_client.add_user(user)  # or await user_client.add_user(user)
    print("DEBUG add_user result:", result, type(result))
    return result
@mcp.tool(description="Update user by ID")
async def update_user(id: int, new_info: UserUpdate) -> str:
    return await user_client.update_user(id, new_info)

# ==================== MCP RESOURCES ====================
@mcp.resource(
    uri="users-management://flow-diagram",
    mime_type="image/png",
    description="Flow diagram of the user management process"
)
async def get_flow_diagram() -> bytes:
    with open(Path(__file__).parent / "flow.png", "rb") as f:
        return f.read()

# ==================== MCP PROMPTS ====================
@mcp.prompt(name="search_guidance", description="Helps users formulate effective search queries")
async def search_guidance() -> str:
    return """You are helping users search through a dynamic user database..."""  # (paste your full prompt here)

@mcp.prompt(name="profile_creation", description="Guides creation of realistic user profiles")
async def profile_creation() -> str:
    return """You are helping create realistic user profiles for the system..."""  # (paste your full prompt here)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
