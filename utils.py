import difflib
import sqlite3
import os
import database
from typing import List, Dict, Any
import datetime
import json
import re
from difflib import SequenceMatcher

def similarity_ratio(a: str, b: str) -> float:
    """Calculate the similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def check_for_similar_tasks(task_id: int, similarity_threshold: float = 0.8) -> bool:
    """Check if there are any similar tasks to the given one and merge if necessary."""
    # Get the task
    task = database.get_task(task_id)
    if not task:
        return False
    
    # Get all active tasks except the current one
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM tasks WHERE id != ? AND completed = 0
    ''', (task_id,))
    
    other_tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Check for similar tasks
    similar_tasks = []
    for other_task in other_tasks:
        similarity = similarity_ratio(task['title'], other_task['title'])
        
        if similarity >= similarity_threshold:
            similar_tasks.append((other_task, similarity))
    
    # If similar tasks found, merge with the highest similarity one
    if similar_tasks:
        # Sort by similarity (highest first)
        similar_tasks.sort(key=lambda x: x[1], reverse=True)
        most_similar_task, similarity = similar_tasks[0]
        
        # Merge tasks
        merge_tasks(task_id, most_similar_task['id'])
        return True
    
    return False

def merge_tasks(task_id1: int, task_id2: int) -> int:
    """Merge two tasks, keeping the one with higher score and increasing repetitions."""
    task1 = database.get_task(task_id1)
    task2 = database.get_task(task_id2)
    
    if not task1 or not task2:
        return None
    
    # Determine which task has the higher score
    if task1['score'] >= task2['score']:
        keep_task = task1
        delete_task = task2
    else:
        keep_task = task2
        delete_task = task1
    
    # Update the kept task's repetitions
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE tasks 
    SET repetitions = repetitions + ?, 
        score = score + 1
    WHERE id = ?
    ''', (delete_task['repetitions'], keep_task['id']))
    
    # Delete the other task
    cursor.execute('DELETE FROM tasks WHERE id = ?', (delete_task['id'],))
    
    conn.commit()
    conn.close()
    
    return keep_task['id']

def parse_natural_language_date(text: str) -> datetime.datetime:
    """Parse natural language date expressions into datetime objects."""
    text = text.lower()
    
    # Get current date
    now = datetime.datetime.now()
    
    # Handle "today"
    if "today" in text:
        return now
    
    # Handle "tomorrow"
    if "tomorrow" in text:
        return now + datetime.timedelta(days=1)
    
    # Handle "next week"
    if "next week" in text:
        return now + datetime.timedelta(days=7)
    
    # Handle "next month"
    if "next month" in text:
        if now.month == 12:
            return datetime.datetime(now.year + 1, 1, now.day)
        else:
            return datetime.datetime(now.year, now.month + 1, min(now.day, 28))
    
    # Handle "in X days/weeks/months"
    in_pattern = r"in (\d+) (day|days|week|weeks|month|months)"
    match = re.search(in_pattern, text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == "day" or unit == "days":
            return now + datetime.timedelta(days=amount)
        elif unit == "week" or unit == "weeks":
            return now + datetime.timedelta(days=7 * amount)
        elif unit == "month" or unit == "months":
            month = now.month + amount
            year = now.year + month // 12
            month = month % 12
            if month == 0:
                month = 12
                year -= 1
            return datetime.datetime(year, month, min(now.day, 28))
    
    # Try standard date formats
    date_formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%b %d %Y", "%B %d %Y"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
    
    # No date found
    return None

def extract_task_info_from_text(text: str) -> Dict[str, Any]:
    """Extract task information from natural language text."""
    task_info = {
        "title": "",
        "description": None,
        "due_date": None,
        "effort": 5,
        "consequences": 5,
        "desire": 5
    }
    
    # Extract title (assume it's the first sentence or up to a certain length)
    title_match = re.match(r'^([^.!?]{3,80})[.!?]?', text.strip())
    if title_match:
        task_info["title"] = title_match.group(1).strip()
        description = text[len(title_match.group(0)):].strip()
        if description:
            task_info["description"] = description
    else:
        task_info["title"] = text[:80].strip()
        if len(text) > 80:
            task_info["description"] = text[80:].strip()
    
    # Extract due date
    due_date_patterns = [
        r"due\s+(?:by|on)?\s+(.+?)(?:\.|$|\n)",
        r"deadline(?:\s+is)?\s+(.+?)(?:\.|$|\n)",
        r"complete\s+by\s+(.+?)(?:\.|$|\n)"
    ]
    
    for pattern in due_date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_text = match.group(1).strip()
            parsed_date = parse_natural_language_date(date_text)
            if parsed_date:
                task_info["due_date"] = parsed_date.isoformat()
                break
    
    # Extract effort level
    effort_patterns = [
        r"(?:takes|requires)\s+(\w+)\s+(?:effort|time|work)",
        r"(?:easy|simple|quick|difficult|hard|challenging)\s+task"
    ]
    
    effort_keywords = {
        "minimal": 9, "little": 8, "some": 6, "moderate": 5, 
        "significant": 3, "substantial": 2, "considerable": 2, "lot": 2,
        "easy": 8, "simple": 8, "quick": 9, "difficult": 2, "hard": 2, "challenging": 2
    }
    
    for pattern in effort_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            keyword = match.group(1).lower() if match.group(1) else match.group(0).split()[0].lower()
            if keyword in effort_keywords:
                task_info["effort"] = effort_keywords[keyword]
                break
    
    # Extract consequences and desire based on language cues
    urgency_keywords = ["urgent", "critical", "important", "crucial", "vital", "essential"]
    desire_keywords = ["want", "hope", "wish", "excited", "looking forward", "eager"]
    
    urgency_score = 5
    desire_score = 5
    
    # Check for urgency/consequence keywords
    for keyword in urgency_keywords:
        if keyword in text.lower():
            urgency_score += 1
    
    # Check for desire keywords
    for keyword in desire_keywords:
        if keyword in text.lower():
            desire_score += 1
    
    task_info["consequences"] = min(10, urgency_score)
    task_info["desire"] = min(10, desire_score)
    
    return task_info
