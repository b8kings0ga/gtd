import sqlite3
import os
import datetime
from typing import List, Dict, Optional, Any
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gtd.db")

def init_db():
    """Initialize the database with the tasks table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        completed INTEGER DEFAULT 0,
        effort INTEGER DEFAULT 5,
        consequences INTEGER DEFAULT 5,
        desire INTEGER DEFAULT 5,
        repetitions INTEGER DEFAULT 1,
        score REAL,
        pre_task INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pre_task) REFERENCES tasks(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def calculate_score(task: Dict[str, Any]) -> float:
    """Calculate the score of a task based on various factors."""
    score = 0
    
    # Due date factor
    if task.get('due_date'):
        due_date = datetime.datetime.fromisoformat(task['due_date'])
        now = datetime.datetime.now()
        days_remaining = (due_date - now).days
        
        if days_remaining <= 0:
            score += 10  # Overdue or due today
        elif days_remaining <= 2:
            score += 8   # Due within 2 days
        elif days_remaining <= 7:
            score += 5   # Due within a week
        else:
            score += 2   # Due later
    
    # Effort factor (inverted: less effort = higher score)
    score += int(task.get('effort', 5))
    
    # Consequences factor
    score += int(task.get('consequences', 5))
    
    # Desire factor
    score += int(task.get('desire', 5))
    
    # Repetitions factor
    score += int(task.get('repetitions', 1) - 1)
    
    return score

def add_task(title: str, description: str = None, due_date: str = None, 
             effort: int = 5, consequences: int = 5, desire: int = 5,
             pre_task: int = None) -> int:
    """Add a new task to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    task = {
        'title': title,
        'description': description,
        'due_date': due_date,
        'effort': effort,
        'consequences': consequences,
        'desire': desire,
        'repetitions': 1
    }
    
    score = calculate_score(task)
    
    cursor.execute('''
    INSERT INTO tasks (title, description, due_date, effort, consequences, desire, pre_task, score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, due_date, effort, consequences, desire, pre_task, score))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # After adding, check for similar tasks and potentially merge
    # from utils import check_for_similar_tasks
    # check_for_similar_tasks(task_id)
    
    return task_id

def get_task(task_id: int) -> Dict[str, Any]:
    """Get a task by its ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM tasks WHERE id = ?
    ''', (task_id,))
    
    task = cursor.fetchone()
    conn.close()
    
    if task:
        return dict(task)
    return None

def get_highest_score_task() -> Dict[str, Any]:
    """Get the task with the highest score that isn't completed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM tasks 
    WHERE completed = 0 
    ORDER BY score DESC 
    LIMIT 1
    ''')
    
    task = cursor.fetchone()
    conn.close()
    
    if task:
        return dict(task)
    return None

def update_task(task_id: int, **kwargs) -> bool:
    """Update a task by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get the current task data
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = dict(cursor.fetchone())
    
    # Update the task data with new values
    task.update(kwargs)
    
    # Recalculate score
    score = calculate_score(task)
    task['score'] = score
    
    # Build the SET clause for the SQL query
    set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
    set_clause += ', score = ?, updated_at = CURRENT_TIMESTAMP'
    
    # Build the parameters for the query
    params = list(kwargs.values()) + [score, task_id]
    
    # Execute the update
    cursor.execute(f'''
    UPDATE tasks SET {set_clause} WHERE id = ?
    ''', params)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def complete_task(task_id: int) -> bool:
    """Mark a task as completed."""
    return update_task(task_id, completed=1)

def get_all_tasks(completed: bool = None) -> List[Dict[str, Any]]:
    """Get all tasks, optionally filtered by completion status."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM tasks'
    params = []
    
    if completed is not None:
        query += ' WHERE completed = ?'
        params.append(int(completed))
    
    query += ' ORDER BY score DESC'
    
    cursor.execute(query, params)
    tasks = [dict(task) for task in cursor.fetchall()]
    conn.close()
    
    return tasks

def increase_repetition(task_id: int) -> bool:
    """Increase the repetition count for a task and update its score."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE tasks 
    SET repetitions = repetitions + 1,
        score = score + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (task_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success
