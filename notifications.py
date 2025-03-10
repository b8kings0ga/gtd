import platform
import subprocess
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_notification(title: str, subtitle: str = "", message: str = "", sound: bool = False) -> bool:
    """Send a system notification.
    
    Args:
        title: The notification title
        subtitle: The notification subtitle
        message: The notification message
        sound: Whether to play a sound
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            # Use AppleScript to display notification
            script = f'''
            display notification "{message}" with title "{title}" subtitle "{subtitle}" {"sound name \"Ping\"" if sound else ""}
            '''
            subprocess.run(["osascript", "-e", script], check=True)
            logger.info(f"Sent macOS notification: {title}")
            return True
            
        elif system == "Linux":
            # Use notify-send for Linux
            sound_arg = ["--urgency=critical"] if sound else []
            subtitle_msg = f"{subtitle}\n{message}" if subtitle else message
            subprocess.run(["notify-send", title, subtitle_msg] + sound_arg, check=True)
            logger.info(f"Sent Linux notification: {title}")
            return True
            
        elif system == "Windows":
            # Use PowerShell for Windows
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            combined_message = f"{subtitle}\n{message}" if subtitle else message
            toaster.show_toast(title, combined_message, duration=10, threaded=True)
            logger.info(f"Sent Windows notification: {title}")
            return True
            
        else:
            logger.error(f"Unsupported platform: {system}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False

def send_task_due_notification(task_id: int, task_title: str, due_date: datetime) -> bool:
    """Send a notification for a task that is due soon.
    
    Args:
        task_id: The ID of the task
        task_title: The title of the task
        due_date: The due date of the task
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    now = datetime.now()
    time_diff = due_date - now
    hours_remaining = time_diff.total_seconds() / 3600
    
    # Create appropriate time message
    if hours_remaining <= 1:
        time_msg = "due within an hour!"
    elif hours_remaining <= 2:
        time_msg = "due in about 2 hours"
    elif hours_remaining <= 24:
        time_msg = f"due in {int(hours_remaining)} hours"
    else:
        days = int(hours_remaining / 24)
        time_msg = f"due in {days} day{'s' if days > 1 else ''}"
    
    return send_notification(
        title=f"Task #{task_id}: {task_title}",
        subtitle=time_msg,
        message=f"Due on {due_date.strftime('%Y-%m-%d %H:%M')}",
        sound=True
    )


if __name__ == "__main__":
    # Test notification
    send_notification(
        title="GTD Notification Test",
        subtitle="This is a test subtitle",
        message="This is a test message from the GTD app",
        sound=True
    )
