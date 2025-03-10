import rumps
import threading
import database
import subprocess
import datetime
import os
import sys
from notifications import send_notification

class StatusBarApp(rumps.App):
    def __init__(self):
        super(StatusBarApp, self).__init__(
            name="GTD",
            title="✓",
            icon=None,
            quit_button="Quit GTD"
        )
        self.menu = ["Show Top Task", "Add Task", "Open GUI", None, "Check for Due Tasks"]
        
        # Schedule task check every 30 minutes
        self._check_timer = rumps.Timer(self.check_due_tasks, 60 * 30)
        self._check_timer.start()
    
    @rumps.clicked("Show Top Task")
    def show_top_task(self, _):
        """Show the highest priority task."""
        task = database.get_highest_score_task()
        
        if not task:
            rumps.notification(
                title="GTD",
                subtitle="No tasks found",
                message="You don't have any tasks yet. Add one to get started!",
                sound=False
            )
            return
        
        due_str = ""
        if task.get("due_date"):
            due_date = datetime.datetime.fromisoformat(task["due_date"])
            due_str = f" (Due: {due_date.strftime('%Y-%m-%d')})"
        
        rumps.notification(
            title=f"Top Task: {task['title']}",
            subtitle=f"Score: {task['score']:.2f}{due_str}",
            message=task.get("description", ""),
            sound=False
        )
    
    @rumps.clicked("Add Task")
    def add_task(self, _):
        """Quick add a task via dialog."""
        response = rumps.Window(
            message="Enter task title:",
            title="Add Task",
            default_text="",
            ok="Add",
            cancel="Cancel"
        ).run()
        
        if response.clicked and response.text:
            try:
                task_id = database.add_task(title=response.text)
                rumps.notification(
                    title="GTD",
                    subtitle=f"Task created with ID: {task_id}",
                    message=response.text,
                    sound=False
                )
            except Exception as e:
                rumps.notification(
                    title="GTD",
                    subtitle="Error creating task",
                    message=str(e),
                    sound=False
                )
    
    @rumps.clicked("Open GUI")
    def open_gui(self, _):
        """Open the GUI application."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        python_executable = sys.executable
        
        try:
            # Run the main app with GUI mode
            subprocess.Popen([python_executable, os.path.join(script_dir, "main.py"), "gui"])
        except Exception as e:
            rumps.notification(
                title="GTD",
                subtitle="Error opening GUI",
                message=str(e),
                sound=True
            )
    
    @rumps.clicked("Check for Due Tasks")
    def check_due_tasks_menu(self, _):
        """Manually trigger a check for due tasks."""
        self.check_due_tasks(None)
    
    def check_due_tasks(self, _):
        """Check for tasks due in the next 48 hours."""
        now = datetime.datetime.now()
        due_soon = []
        
        tasks = database.get_all_tasks(completed=False)
        
        for task in tasks:
            if task.get("due_date"):
                due_date = datetime.datetime.fromisoformat(task["due_date"])
                hours_remaining = (due_date - now).total_seconds() / 3600
                
                # Check if task is due within 48 hours
                if 0 <= hours_remaining <= 48:
                    due_soon.append(task)
        
        # Send notifications for tasks due soon
        if due_soon:
            for task in due_soon:
                due_date = datetime.datetime.fromisoformat(task["due_date"])
                hours_remaining = (due_date - now).total_seconds() / 3600
                
                if hours_remaining <= 2:
                    time_str = "due very soon!"
                elif hours_remaining <= 24:
                    time_str = f"due in {int(hours_remaining)} hours"
                else:
                    time_str = f"due in {int(hours_remaining / 24)} days"
                
                send_notification(
                    title=f"Task Due Soon: {task['title']}",
                    subtitle=time_str,
                    message=task.get("description", ""),
                    sound=True
                )
        
        return due_soon

    def run(self):
        """Run the status bar app."""
        # Check for due tasks immediately on start
        threading.Timer(1.0, lambda: self.check_due_tasks(None)).start()
        
        # Replace self.run_application() with the correct method
        self.start_app()  # or whatever the correct method name should be
    
    def start_app(self):
        # Implement the method that was intended to be called
        # This should contain the implementation that was meant to be in run_application
        # For example:
        try:
            # Your application starting logic here
            pass
        except Exception as e:
            print(f"Error starting status bar app: {e}")

if __name__ == "__main__":
    StatusBarApp().run()
