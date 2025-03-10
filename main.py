import typer
from typing import Optional
import os
import sys

# Add the current directory to the path so we can import from local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cli import app as cli_app
from gui import launch_gui
from server import start_server
import database

def validate_date(date_string):
    """Validate and standardize date format."""
    if not date_string:
        return None
    
    try:
        # Parse the date string to handle formats like "2025-3-7"
        from datetime import datetime
        parsed_date = datetime.strptime(date_string, "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d")  # Return standardized format
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD format.")
        return None

def create_task(title, description="", due_date=None, effort=5, consequences=5, desire=5):
    """Create a task with the given attributes."""
    try:
        # Ensure all numeric values are integers
        effort = int(effort)
        consequences = int(consequences)
        desire = int(desire)
        
        # Calculate priority or other metrics
        priority = effort + consequences + desire
        
        # Rest of your task creation logic...
        
        return True, "Task created successfully"
    except Exception as e:
        return False, f"Error creating task: {str(e)}"

def main():
    # Initialize the database
    database.init_db()
    
    # Check if the app is in GUI mode or CLI mode
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        launch_gui()
    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        start_server()
    else:
        # Run CLI mode
        cli_app()

if __name__ == "__main__":
    main()
