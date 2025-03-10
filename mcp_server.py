

from arrow import get
from mcp.server.fastmcp import FastMCP, Context, Image
from cli import create_task as create_task_cli

from database import add_task, get_all_tasks
import json

mcp = FastMCP()

# Tool fixes
@mcp.tool(name="create_task", description="when user says remind me, create task, or add task")
def create_task(title:str , description:str) -> str:
    """create a new task with title and optional description"""
    add_task(title, description)
    return f"Task created: {title}"
    

@mcp.tool(name="list_tasks", description="list all tasks, when user says list tasks, or what are my tasks etc")
def list_tasks() -> list:
    """list all tasks"""
    tasks = get_all_tasks()
    return tasks




if __name__ == "__main__":
    mcp.run(transport="sse")
