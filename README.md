# gtd
## GTD - Get Things Done Todo App

GTD is an innovative todo app designed to help you manage your tasks efficiently using a four-quadrant system. This app leverages modern technologies to provide a seamless experience across different interfaces.

### Task Scoring System

The task scoring system in GTD is designed to prioritize tasks based on several factors. Each task is assigned a score that helps determine its importance and urgency. The score is calculated using the following criteria:

1. **Due Date**: Tasks with a closer due date receive a higher score. For example, a task due tomorrow might have a score of 10, while a task with no due date has a score of 0.
2. **Effort Score**: This score represents the amount of effort required to complete the task. It ranges from 1 to 10, with higher scores indicating less time required.
3. **Consequences**: This score reflects the impact of not completing the task. It ranges from 1 to 10, with higher scores indicating more severe consequences.
4. **Desire Score**: This score indicates how much you want to complete the task. It ranges from 1 to 10, with higher scores indicating a stronger desire to complete the task.
5. **Repetitions**: If a task is mentioned or created multiple times, its score increases by 1 for each repetition. This ensures that frequently mentioned tasks are prioritized.

The overall task score is a combination of these factors, helping you focus on the most important and urgent tasks first.

### Features

- **Create Tasks**: Add tasks with a title, optional description, due date, pre-task, effort score, consequences, and desire score. Tasks are saved to a SQLite database.
- **Get Tasks**: Retrieve the highest score task with all its details via command line or MCP server.
- **Natural Language Processing**: Create tasks using natural language prompts through the MCP server.
- **Complete Tasks**: Mark tasks as done and update their status.
- **Edit Tasks**: Update task information and save changes to the database.
- **Auto Merge**: Automatically merge similar tasks based on title similarities and adjust their scores accordingly.

### Technology Stack

- **uv**: Package management
- **flet**: Graphical interface
- **typer**: Command-line interface
- **langchain**: Model processing using OpenAPI proxy URL and API key
- **mcp python sdk**: SDK server
- **nuitika**: Application packaging
- **inquirerpy**: Command-line queries
- **async**: Background tasks for auto-merging and priority adjustments

### Usage

GTD can be used through various interfaces:
- **Command Line**: Manage tasks using the command-line interface.
- **Flet Interface**: Use the graphical interface for a more visual experience.
- **MCP Server**: Connect through the MCP server for natural language task management.

### Installation

To install GTD, ensure you have the necessary dependencies and follow the installation instructions provided in the repository.

### Example Commands

1. **Create Task**: 
    ```python
    gtd create "Buy milk" --description "Buy milk from the store" --duedate "2023-10-10" --effort 2 --consequences 5 --desire 8
    ```
2. **Get Task**:
    ```python
    gtd getone
    ```
3. **Complete Task**:
    ```python
    gtd done 1
    ```
4. **Edit Task**:
    ```python
    gtd edit 1 --title "Buy almond milk"
    ```

### Interface
Once the app is opened, it stays in the status bar. When the settings in the status bar are pressed, users can make adjustments to the settings.

### Auto Merge

The app automatically merges similar tasks and adjusts their scores based on repetitions, ensuring that frequently mentioned tasks are prioritized.

### Notifications

Stay on top of your tasks with notifications, ensuring you never miss an important deadline.

GTD will notify you through the apple nitification when a task is due in 48 hours.

GTD is designed to stay on the status bar of your Mac, providing quick access to your tasks and notifications.

# GTD MCP Server

A Model Context Protocol (MCP) server that implements Getting Things Done (GTD) functionality.

## Overview

This server provides tools and resources for managing tasks, projects, and contexts using the GTD methodology. It integrates with AI assistants through the Model Context Protocol to help you stay organized.

## Features

- **Capture**: Quickly capture tasks into your inbox
- **Process**: Organize tasks into projects and appropriate lists
- **Review**: Structured prompts for daily and weekly reviews
- **Track**: Monitor progress across projects and tasks

## Installation

Install the MCP server dependencies:

