from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import datetime
from enum import Enum

class Quadrant(Enum):
    """Four-quadrant system for task classification."""
    URGENT_IMPORTANT = 1      # Urgent and Important
    NOT_URGENT_IMPORTANT = 2  # Not Urgent but Important
    URGENT_NOT_IMPORTANT = 3  # Urgent but Not Important
    NOT_URGENT_NOT_IMPORTANT = 4  # Neither Urgent nor Important

@dataclass
class Task:
    """Task model representing a todo item."""
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    completed: bool = False
    effort: int = 5           # 1-10, higher means less effort
    consequences: int = 5     # 1-10, higher means more severe consequences
    desire: int = 5           # 1-10, higher means more desire to complete
    repetitions: int = 1
    score: float = 0
    pre_task: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a Task object from a dictionary."""
        task_data = dict(data)
        
        # Convert string dates to datetime objects
        for date_field in ['due_date', 'created_at', 'updated_at']:
            if task_data.get(date_field):
                try:
                    task_data[date_field] = datetime.datetime.fromisoformat(task_data[date_field])
                except ValueError:
                    task_data[date_field] = None
        
        # Convert integer to boolean for completed field
        if 'completed' in task_data:
            task_data['completed'] = bool(task_data['completed'])
        
        return cls(**{k: v for k, v in task_data.items() if k in cls.__annotations__})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Task object to a dictionary."""
        result = vars(self).copy()
        
        # Convert datetime objects to ISO format strings
        for date_field in ['due_date', 'created_at', 'updated_at']:
            if result.get(date_field):
                result[date_field] = result[date_field].isoformat()
        
        # Convert boolean to integer for completed field
        if 'completed' in result:
            result['completed'] = int(result['completed'])
            
        return result
    
    def get_quadrant(self) -> Quadrant:
        """Determine which quadrant the task belongs to."""
        is_urgent = False
        is_important = False
        
        # Determine urgency based on due date and score
        if self.due_date:
            days_remaining = (self.due_date - datetime.datetime.now()).days
            is_urgent = days_remaining <= 2  # Consider tasks due within 2 days as urgent
        
        # Determine importance based on consequences and desire
        importance_threshold = 12  # Combined threshold for consequences and desire
        is_important = (self.consequences + self.desire) >= importance_threshold
        
        if is_urgent and is_important:
            return Quadrant.URGENT_IMPORTANT
        elif not is_urgent and is_important:
            return Quadrant.NOT_URGENT_IMPORTANT
        elif is_urgent and not is_important:
            return Quadrant.URGENT_NOT_IMPORTANT
        else:
            return Quadrant.NOT_URGENT_NOT_IMPORTANT
