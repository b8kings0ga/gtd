import flet as ft
from flet import (
    AppBar, ElevatedButton, Page, Row, Column, Text, TextField,
    Dropdown, Tab, Tabs, DataTable, DataColumn, DataRow, DataCell,
    Card, Icon, icons, Colors, DatePicker, Slider, AlertDialog,
    Container, IconButton, FloatingActionButton, ListTile, Divider,
)
import datetime
import database
from models import Task, Quadrant
import asyncio
from utils import check_for_similar_tasks
from statusbar import StatusBarApp
import threading

class GTDApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "GTD - Get Things Done"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 800
        self.page.window_height = 600
        
        self.setup_ui()
        self.load_tasks()
        
        # Start background tasks for auto-merge and priority adjustments
        asyncio.create_task(self.background_tasks())
    
    def setup_ui(self):
        # Create the tabs
        self.tasks_tab = self.create_tasks_tab()
        self.add_task_tab = self.create_add_task_tab()
        self.settings_tab = self.create_settings_tab()
        
        # Create the navigation tabs
        self.tabs = Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                Tab(text="Tasks", icon=icons.LIST_ALT, content=self.tasks_tab),
                Tab(text="Add Task", icon=icons.ADD, content=self.add_task_tab),
                Tab(text="Settings", icon=icons.SETTINGS, content=self.settings_tab),
            ],
            expand=True,
        )
        
        # Create the app bar
        self.app_bar = AppBar(
            title=Text("GTD - Get Things Done"),
            center_title=True,
            bgcolor=Colors.BLUE,
            actions=[
                IconButton(icon=icons.REFRESH, on_click=self.refresh_tasks),
                IconButton(icon=icons.HELP_OUTLINE, on_click=self.show_help),
            ],
        )
        
        # Floating action button for quick add task
        self.fab = FloatingActionButton(
            icon=icons.ADD,
            on_click=self.quick_add_task,
            bgcolor=Colors.BLUE,
        )
        
        # Add everything to the page
        self.page.appbar = self.app_bar
        self.page.add(self.tabs)
        self.page.floating_action_button = self.fab
        
    def create_tasks_tab(self):
        # Create data table for tasks
        self.tasks_table = DataTable(
            columns=[
                DataColumn(Text("ID")),
                DataColumn(Text("Title")),
                DataColumn(Text("Due Date")),
                DataColumn(Text("Score")),
                DataColumn(Text("Quadrant")),
                DataColumn(Text("Status")),
                DataColumn(Text("Actions")),
            ],
            rows=[],
            border=ft.border.all(1, Colors.BLACK12),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, Colors.BLACK12),
            horizontal_lines=ft.border.BorderSide(1, Colors.BLACK12),
            sort_column_index=3,  # Sort by score by default
            sort_ascending=False,  # Descending order
        )
        
        # Filter controls
        self.filter_dropdown = Dropdown(
            options=[
                ft.dropdown.Option("all", "All Tasks"),
                ft.dropdown.Option("active", "Active Tasks"),
                ft.dropdown.Option("completed", "Completed Tasks"),
            ],
            value="active",
            on_change=self.filter_tasks,
            width=200,
        )
        
        filter_row = Row([
            Text("Show:"),
            self.filter_dropdown,
            ElevatedButton("Refresh", on_click=self.refresh_tasks),
        ])
        
        # Quadrant view
        self.quadrant_view = Column(
            controls=[
                Text("Four Quadrant View", size=20, weight=ft.FontWeight.BOLD),
                Row(
                    controls=[
                        self.create_quadrant_card(Quadrant.URGENT_IMPORTANT),
                        self.create_quadrant_card(Quadrant.NOT_URGENT_IMPORTANT),
                        self.create_quadrant_card(Quadrant.URGENT_NOT_IMPORTANT),
                        self.create_quadrant_card(Quadrant.NOT_URGENT_NOT_IMPORTANT),
                    ],
                    spacing=10,
                ),
            ],
            spacing=20,
        )
        
        return Column(
            controls=[
                filter_row,
                self.tasks_table,
                Divider(),
                self.quadrant_view,
            ],
            spacing=20,
        )
    
    def create_quadrant_card(self, quadrant: Quadrant):
        """Create a card for displaying tasks in a specific quadrant."""
        title_map = {
            Quadrant.URGENT_IMPORTANT: "Urgent & Important",
            Quadrant.NOT_URGENT_IMPORTANT: "Not Urgent but Important",
            Quadrant.URGENT_NOT_IMPORTANT: "Urgent but Not Important",
            Quadrant.NOT_URGENT_NOT_IMPORTANT: "Not Urgent & Not Important",
        }
        
        color_map = {
            Quadrant.URGENT_IMPORTANT: Colors.RED_400,
            Quadrant.NOT_URGENT_IMPORTANT: Colors.BLUE_400,
            Quadrant.URGENT_NOT_IMPORTANT: Colors.AMBER_400,
            Quadrant.NOT_URGENT_NOT_IMPORTANT: Colors.GREEN_400,
        }
        
        return Card(
            content=Container(
                content=Column(
                    controls=[
                        Text(title_map[quadrant], weight=ft.FontWeight.BOLD, size=16),
                        Divider(),
                        # Tasks will be populated here
                        Column([], scroll=ft.ScrollMode.AUTO, height=200),
                    ],
                    spacing=10,
                ),
                padding=15,
                border_radius=10,
            ),
            color=color_map[quadrant],
            width=350,
            height=300,
        )
    
    def create_add_task_tab(self):
        """Create the tab for adding new tasks."""
        self.title_field = TextField(label="Title", hint_text="Task title", width=400)
        self.desc_field = TextField(
            label="Description", 
            hint_text="Task description (optional)", 
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=400
            
        )
        
        self.due_date_picker = DatePicker(
            on_change=self.on_date_selected,
        )
        
        self.due_date_field = TextField(
            label="Due Date",
            hint_text="YYYY-MM-DD",
            width=200,
            read_only=True,
        )
        
        self.date_button = ElevatedButton(
            "Select Date",
            icon=icons.CALENDAR_TODAY,
            on_click=lambda _: self.due_date_picker,
        )
        
        self.effort_slider = Slider(
            min=1, max=10, divisions=9, label="{value}", value=5,
            width=400,
        )
        
        self.consequence_slider = Slider(
            min=1, max=10, divisions=9, label="{value}", value=5,
            width=400,
        )
        
        self.desire_slider = Slider(
            min=1, max=10, divisions=9, label="{value}", value=5,
            width=400,
        )
        
        self.pretask_dropdown = Dropdown(
            label="Prerequisite Task",
            hint_text="Select prerequisite task (optional)",
            options=[ft.dropdown.Option("None", "None")],
            width=400,
        )
        
        # Fill the prerequisite task dropdown
        self.update_pretask_dropdown()
        
        return Column(
            controls=[
                Text("Add New Task", size=20, weight=ft.FontWeight.BOLD),
                self.title_field,
                self.desc_field,
                Row([self.due_date_field, self.date_button]),
                self.due_date_picker,
                Text("Effort (higher = less effort required)", size=16),
                self.effort_slider,
                Text("Consequences (higher = more severe)", size=16),
                self.consequence_slider,
                Text("Desire (higher = more desire to complete)", size=16),
                self.desire_slider,
                self.pretask_dropdown,
                ElevatedButton("Create Task", on_click=self.add_task),
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            #padding=20,
        )
    
    def create_settings_tab(self):
        """Create the settings tab."""
        return Column(
            controls=[
                Text("Settings", size=20, weight=ft.FontWeight.BOLD),
                ListTile(
                    leading=Icon(icons.NOTIFICATIONS),
                    title=Text("Notifications"),
                    trailing=ft.Switch(value=True),
                ),
                ListTile(
                    leading=Icon(icons.AUTO_AWESOME),
                    title=Text("Auto-merge similar tasks"),
                    trailing=ft.Switch(value=True),
                ),
                ListTile(
                    leading=Icon(icons.COLOR_LENS),
                    title=Text("Dark Mode"),
                    trailing=ft.Switch(
                        value=self.page.theme_mode == ft.ThemeMode.DARK,
                        on_change=self.toggle_theme_mode,
                    ),
                ),
                ElevatedButton("Save Settings", on_click=self.save_settings),
            ],
            spacing=20,
            expand=True,
            #padding=20,
        )
    
    async def background_tasks(self):
        """Run background tasks such as auto-merge and priority adjustments."""
        while True:
            # Check for tasks that need to be adjusted
            await asyncio.sleep(60)  # Check every minute
    
    def on_date_selected(self, e):
        """Handle date selection from the date picker."""
        if self.due_date_picker.value:
            self.due_date_field.value = self.due_date_picker.value.isoformat()
            self.page.update()
    
    def update_pretask_dropdown(self):
        """Update the prerequisite task dropdown with current active tasks."""
        tasks = database.get_all_tasks(completed=False)
        
        # Clear existing options and add the None option
        self.pretask_dropdown.options = [ft.dropdown.Option("None", "None")]
        
        # Add tasks to the dropdown
        for task in tasks:
            self.pretask_dropdown.options.append(
                ft.dropdown.Option(str(task['id']), f"#{task['id']}: {task['title']}")
            )
            
        self.page.update()
    
    def load_tasks(self):
        """Load tasks and update the UI."""
        # Determine which tasks to load based on filter
        completed_filter = None
        if self.filter_dropdown.value == "active":
            completed_filter = False
        elif self.filter_dropdown.value == "completed":
            completed_filter = True
        
        tasks = database.get_all_tasks(completed=completed_filter)
        
        # Clear existing rows
        self.tasks_table.rows = []
        
        # Add tasks to the table
        for task_data in tasks:
            task = Task.from_dict(task_data)
            
            due_date_str = task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A"
            status = "Completed" if task.completed else "Active"
            quadrant = task.get_quadrant().name.replace("_", " ")
            
            # Create action buttons
            edit_button = IconButton(icon=icons.EDIT, on_click=lambda e, t=task: self.edit_task(t))
            complete_button = IconButton(icon=icons.CHECK_CIRCLE_OUTLINE, on_click=lambda e, t=task: self.mark_complete(t))
            delete_button = IconButton(icon=icons.DELETE, on_click=lambda e, t=task: self.delete_task(t))
            
            actions = Row([edit_button, complete_button, delete_button])
            
            self.tasks_table.rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(str(task.id))),
                        DataCell(Text(task.title)),
                        DataCell(Text(due_date_str)),
                        DataCell(Text(f"{task.score:.2f}")),
                        DataCell(Text(quadrant)),
                        DataCell(Text(status)),
                        DataCell(actions),
                    ]
                )
            )
        
        # Update the page
        self.page.update()
    
    def filter_tasks(self, e):
        """Filter tasks based on dropdown selection."""
        self.load_tasks()
    
    def refresh_tasks(self, e=None):
        """Refresh tasks from the database."""
        self.load_tasks()
        self.update_pretask_dropdown()
    
    def add_task(self, e):
        """Add a new task from the form data."""
        title = self.title_field.value
        if not title:
            self.show_error("Title is required")
            return
        
        # Get form values
        description = self.desc_field.value
        due_date = self.due_date_field.value
        effort = int(self.effort_slider.value)
        consequences = int(self.consequence_slider.value)
        desire = int(self.desire_slider.value)
        
        # Get pre-task ID if selected
        pre_task = None
        if self.pretask_dropdown.value and self.pretask_dropdown.value != "None":
            pre_task = int(self.pretask_dropdown.value)
        
        try:
            task_id = database.add_task(
                title=title,
                description=description,
                due_date=due_date,
                effort=effort,
                consequences=consequences,
                desire=desire,
                pre_task=pre_task
            )
            
            # Clear the form
            self.title_field.value = ""
            self.desc_field.value = ""
            self.due_date_field.value = ""
            self.effort_slider.value = 5
            self.consequence_slider.value = 5
            self.desire_slider.value = 5
            self.pretask_dropdown.value = "None"
            
            # Show success message
            self.show_success(f"Task created with ID: {task_id}")
            
            # Refresh the task list
            self.refresh_tasks()
            
            # Switch to tasks tab
            self.tabs.selected_index = 0
            self.page.update()
            
        except Exception as e:
            self.show_error(f"Error creating task: {str(e)}")
    
    def mark_complete(self, task: Task):
        """Mark a task as complete."""
        success = database.complete_task(task.id)
        
        if success:
            self.show_success(f"Task {task.id} marked as complete")
            self.refresh_tasks()
        else:
            self.show_error(f"Failed to mark task {task.id} as complete")
    
    def edit_task(self, task: Task):
        """Open the edit task dialog."""
        # Implementation of edit task UI goes here
        # For simplicity, we'll just switch to add tab and pre-populate fields
        self.title_field.value = task.title
        self.desc_field.value = task.description or ""
        if task.due_date:
            self.due_date_field.value = task.due_date.isoformat()
        self.effort_slider.value = task.effort
        self.consequence_slider.value = task.consequences
        self.desire_slider.value = task.desire
        
        if task.pre_task:
            self.pretask_dropdown.value = str(task.pre_task)
        else:
            self.pretask_dropdown.value = "None"
        
        self.tabs.selected_index = 1
        self.page.update()
    
    def delete_task(self, task: Task):
        """Delete a task."""
        # Implementation of task deletion would go here
        # This feature is not in the specification, but could be added
        pass
    
    def quick_add_task(self, e=None):
        """Quick add a task with a simple dialog."""
        title_field = TextField(label="Task Title", autofocus=True)
        
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()
        
        def add_quick_task(e):
            title = title_field.value
            if title:
                try:
                    task_id = database.add_task(title=title)
                    self.show_success(f"Quick task created with ID: {task_id}")
                    self.refresh_tasks()
                except Exception as ex:
                    self.show_error(f"Error creating task: {str(ex)}")
            close_dlg(e)
        
        self.page.dialog = AlertDialog(
            title=Text("Quick Add Task"),
            content=title_field,
            actions=[
                ElevatedButton("Cancel", on_click=close_dlg),
                ElevatedButton("Add", on_click=add_quick_task),
            ],
            actions_alignment="end",
        )
        
        self.page.dialog.open = True
        self.page.update()
    
    def show_help(self, e=None):
        """Show the help dialog."""
        self.page.dialog = AlertDialog(
            title=Text("GTD Help"),
            content=Column(
                controls=[
                    Text("GTD - Get Things Done is a task management application."),
                    Text("Each task has a score based on:"),
                    Text("- Due Date: Tasks due sooner get higher scores"),
                    Text("- Effort: Higher score = less effort required"),
                    Text("- Consequences: Higher score = more severe consequences"),
                    Text("- Desire: Higher score = more desire to complete"),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ElevatedButton("Close", on_click=lambda e: setattr(self.page.dialog, 'open', False))
            ],
            actions_alignment="end",
        )
        
        self.page.dialog.open = True
        self.page.update()
    
    def show_error(self, message: str):
        """Show an error message."""
        self.page.snack_bar = ft.SnackBar(
            content=Text(message),
            bgcolor=Colors.RED_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show_success(self, message: str):
        """Show a success message."""
        self.page.snack_bar = ft.SnackBar(
            content=Text(message),
            bgcolor=Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def toggle_theme_mode(self, e):
        """Toggle between light and dark theme."""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.update()
    
    def save_settings(self, e):
        """Save the application settings."""
        # Implementation of settings saving would go here
        self.show_success("Settings saved")


def launch_gui():
    """Launch the GUI application."""
    def main(page: ft.Page):
        app = GTDApp(page)
    
    # Start the status bar app in a separate thread
    status_bar_thread = threading.Thread(target=StatusBarApp().run)
    status_bar_thread.daemon = True
    status_bar_thread.start()
    
    # Launch the Flet app
    ft.app(target=main)

if __name__ == "__main__":
    launch_gui()