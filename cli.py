from traceback import print_stack
import typer
from typing import Optional
from datetime import datetime
import json
from rich.console import Console
from rich.table import Table
from InquirerPy import prompt
from InquirerPy.validator import EmptyInputValidator

import database
from models import Task, Quadrant

app = typer.Typer()
console = Console()

@app.command("create")
def create_task(
    title: str = typer.Argument(..., help="Task title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Task description"),
    duedate: Optional[str] = typer.Option(None, "--duedate", help="Due date (YYYY-MM-DD)"),
    effort: int = typer.Option(5, "--effort", "-e", min=1, max=10, help="Effort score (1-10, higher means less effort)"),
    consequences: int = typer.Option(5, "--consequences", "-c", min=1, max=10, help="Consequences score (1-10)"),
    desire: int = typer.Option(5, "--desire", min=1, max=10, help="Desire score (1-10)"),
    pretask: Optional[int] = typer.Option(None, "--pretask", "-p", help="ID of prerequisite task")
):
    """Create a new task."""
    
    # Validate the due date format if provided
    due_date_obj = None
    if duedate:
        try:
            due_date_obj = datetime.fromisoformat(duedate)
            duedate = due_date_obj.isoformat()
        except ValueError:
            console.print(f"[bold red]Error:[/] Invalid date format. Use YYYY-MM-DD.")
            return
    
    try:
        task_id = database.add_task(
            title=title,
            description=description,
            due_date=duedate,
            effort=effort,
            consequences=consequences,
            desire=desire,
            pre_task=pretask
        )
        console.print(f"[bold green]Task created with ID: {task_id}[/]")
    except Exception as e:
        raise(e)
        console.print(f"[bold red]Error creating task:[/] {str(e)}")

@app.command("getone")
def get_highest_priority_task():
    """Get the highest priority task."""
    task_data = database.get_highest_score_task()
    
    if not task_data:
        console.print("[yellow]No tasks found.[/]")
        return
    
    task = Task.from_dict(task_data)
    
    table = Table(title=f"Task #{task.id}: {task.title}")
    
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Description", task.description or "N/A")
    table.add_row("Due Date", task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A")
    table.add_row("Effort", str(task.effort))
    table.add_row("Consequences", str(task.consequences))
    table.add_row("Desire", str(task.desire))
    table.add_row("Score", f"{task.score:.2f}")
    table.add_row("Quadrant", task.get_quadrant().name.replace("_", " "))
    
    console.print(table)

@app.command("list")
def list_tasks(
    all: bool = typer.Option(False, "--all", "-a", help="Show all tasks including completed"),
    completed: bool = typer.Option(False, "--completed", "-c", help="Show only completed tasks"),
):
    """List all tasks, filtered by completion status."""
    completed_filter = None
    if not all:
        completed_filter = True if completed else False
    
    tasks = database.get_all_tasks(completed=completed_filter)
    
    if not tasks:
        console.print("[yellow]No tasks found.[/]")
        return
    
    table = Table(title="Tasks")
    
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title", style="green")
    table.add_column("Due Date", style="blue")
    table.add_column("Score", justify="right")
    table.add_column("Quadrant", style="magenta")
    table.add_column("Status", style="yellow")
    
    for task_data in tasks:
        task = Task.from_dict(task_data)
        
        due_date_str = task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A"
        status = "✓" if task.completed else "○"
        quadrant = task.get_quadrant().name.replace("_", " ")
        
        table.add_row(
            str(task.id),
            task.title,
            due_date_str,
            f"{task.score:.2f}",
            quadrant,
            status
        )
    
    console.print(table)

@app.command("done")
def complete_task(task_id: int = typer.Argument(..., help="ID of the task to complete")):
    """Mark a task as completed."""
    success = database.complete_task(task_id)
    
    if success:
        console.print(f"[bold green]Task {task_id} marked as complete.[/]")
    else:
        console.print(f"[bold red]Failed to mark task {task_id} as complete. Task may not exist.[/]")

@app.command("edit")
def edit_task(
    task_id: int = typer.Argument(..., help="ID of the task to edit"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Task title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Task description"),
    duedate: Optional[str] = typer.Option(None, "--duedate", help="Due date (YYYY-MM-DD)"),
    effort: Optional[int] = typer.Option(None, "--effort", "-e", min=1, max=10, help="Effort score (1-10)"),
    consequences: Optional[int] = typer.Option(None, "--consequences", "-c", min=1, max=10, help="Consequences score (1-10)"),
    desire: Optional[int] = typer.Option(None, "--desire", min=1, max=10, help="Desire score (1-10)"),
    pretask: Optional[int] = typer.Option(None, "--pretask", "-p", help="ID of prerequisite task")
):
    """Edit an existing task."""
    # Get the current task details
    task_data = database.get_task(task_id)
    
    if not task_data:
        console.print(f"[bold red]Task {task_id} not found.[/]")
        return
    
    # Prepare updates dictionary
    updates = {}
    
    if title is not None:
        updates['title'] = title
    if description is not None:
        updates['description'] = description
    if duedate is not None:
        try:
            due_date_obj = datetime.fromisoformat(duedate)
            updates['due_date'] = due_date_obj.isoformat()
        except ValueError:
            console.print(f"[bold red]Error:[/] Invalid date format. Use YYYY-MM-DD.")
            return
    if effort is not None:
        updates['effort'] = effort
    if consequences is not None:
        updates['consequences'] = consequences
    if desire is not None:
        updates['desire'] = desire
    if pretask is not None:
        updates['pre_task'] = pretask
    
    # If no updates were specified, use interactive mode
    if not updates:
        task = Task.from_dict(task_data)
        
        questions = [
            {
                "type": "input",
                "name": "title",
                "message": "Task title:",
                "default": task.title,
            },
            {
                "type": "input",
                "name": "description",
                "message": "Task description:",
                "default": task.description or "",
            },
            {
                "type": "input",
                "name": "duedate",
                "message": "Due date (YYYY-MM-DD):",
                "default": task.due_date.strftime("%Y-%m-%d") if task.due_date else "",
            },
            {
                "type": "number",
                "name": "effort",
                "message": "Effort score (1-10, higher means less effort):",
                "default": task.effort,
                "min_allowed": 1,
                "max_allowed": 10,
            },
            {
                "type": "number",
                "name": "consequences",
                "message": "Consequences score (1-10):",
                "default": task.consequences,
                "min_allowed": 1,
                "max_allowed": 10,
            },
            {
                "type": "number",
                "name": "desire",
                "message": "Desire score (1-10):",
                "default": task.desire,
                "min_allowed": 1,
                "max_allowed": 10,
            },
        ]
        
        result = prompt(questions)
        
        updates = {k: v for k, v in result.items() if v}
        
        # Handle the due date
        if updates.get('duedate'):
            try:
                due_date_obj = datetime.fromisoformat(updates['duedate'])
                updates['due_date'] = due_date_obj.isoformat()
            except ValueError:
                console.print(f"[bold red]Error:[/] Invalid date format. Skipping due date update.")
            
            # Remove the original duedate key
            del updates['duedate']
    
    if updates:
        success = database.update_task(task_id, **updates)
        
        if success:
            console.print(f"[bold green]Task {task_id} updated successfully.[/]")
        else:
            console.print(f"[bold red]Failed to update task {task_id}.[/]")
    else:
        console.print("[yellow]No changes made to the task.[/]")

@app.command("interactive")
def interactive_mode():
    """Interactive task creation mode."""
    questions = [
        {
            "type": "input",
            "name": "title",
            "message": "Task title:",
            "validate": EmptyInputValidator("Title cannot be empty"),
        },
        {
            "type": "input",
            "name": "description",
            "message": "Task description (optional):",
        },
        {
            "type": "input",
            "name": "duedate",
            "message": "Due date (YYYY-MM-DD, optional):",
        },
        {
            "type": "number",
            "name": "effort",
            "message": "Effort score (1-10, higher means less effort):",
            "default": 5,
            "min_allowed": 1,
            "max_allowed": 10,
        },
        {
            "type": "number",
            "name": "consequences",
            "message": "Consequences score (1-10):",
            "default": 5,
            "min_allowed": 1,
            "max_allowed": 10,
        },
        {
            "type": "number",
            "name": "desire",
            "message": "Desire score (1-10):",
            "default": 5,
            "min_allowed": 1,
            "max_allowed": 10,
        },
    ]
    
    result = prompt(questions)
    
    # Process due date if provided
    duedate = None
    if result.get('duedate'):
        try:
            due_date_obj = datetime.fromisoformat(result['duedate'])
            duedate = due_date_obj.isoformat()
        except ValueError:
            console.print(f"[bold red]Error:[/] Invalid date format. Due date will not be set.")
    
    try:
        task_id = database.add_task(
            title=result['title'],
            description=result.get('description'),
            due_date=duedate,
            effort=result['effort'],
            consequences=result['consequences'],
            desire=result['desire']
        )
        console.print(f"[bold green]Task created with ID: {task_id}[/]")
    except Exception as e:
        raise(e) 
        console.print(f"[bold red]Error creating task:[/] {str(e)}")

if __name__ == "__main__":
    app()
