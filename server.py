from flask import Flask, request, jsonify
from typing import Dict, Any, Optional
import json
import os
import database
from utils import extract_task_info_from_text
from models import Task
import threading
from dotenv import load_dotenv
import logging
import openai
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

# Initialize LangChain components
llm = OpenAI(
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
    temperature=0.7
)

# Define prompt for task extraction
task_extraction_prompt = PromptTemplate(
    input_variables=["text"],
    template="""
    Extract task information from the following text:
    
    {text}
    
    Return a JSON object with these fields:
    - title: A short title for the task
    - description: A longer description (if available)
    - due_date: Due date in YYYY-MM-DD format or null if not specified
    - effort: A score from 1-10 indicating effort (10 = minimal effort)
    - consequences: A score from 1-10 indicating consequences (10 = severe)
    - desire: A score from 1-10 indicating desire to complete (10 = high desire)
    """
)

task_extraction_chain = task_extraction_prompt | llm

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/task', methods=['POST'])
def create_task():
    """Create a new task from JSON input."""
    if not request.json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    required_fields = ['title']
    for field in required_fields:
        if field not in request.json:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        task_id = database.add_task(
            title=request.json.get('title'),
            description=request.json.get('description'),
            due_date=request.json.get('due_date'),
            effort=int(request.json.get('effort', 5)),
            consequences=int(request.json.get('consequences', 5)),
            desire=int(request.json.get('desire', 5)),
            pre_task=request.json.get('pre_task')
        )
        return jsonify({"task_id": task_id, "success": True})
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/task/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a task by ID."""
    task_data = database.get_task(task_id)
    if not task_data:
        return jsonify({"error": "Task not found"}), 404
    
    task = Task.from_dict(task_data)
    return jsonify(task.to_dict())

@app.route('/task/top', methods=['GET'])
def get_top_task():
    """Get the highest priority task."""
    task_data = database.get_highest_score_task()
    if not task_data:
        return jsonify({"message": "No tasks found"}), 404
    
    task = Task.from_dict(task_data)
    return jsonify(task.to_dict())

@app.route('/task/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed."""
    success = database.complete_task(task_id)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Task not found or could not be completed"}), 404

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks, optionally filtered by completion status."""
    completed_param = request.args.get('completed')
    completed = None
    
    if completed_param is not None:
        completed = completed_param.lower() in ('true', '1', 'yes')
    
    tasks = database.get_all_tasks(completed=completed)
    return jsonify([Task.from_dict(task).to_dict() for task in tasks])

@app.route('/nlp/task', methods=['POST'])
def create_task_from_text():
    """Create a task using natural language processing."""
    if not request.json or 'text' not in request.json:
        return jsonify({"error": "Request must include 'text' field"}), 400
    
    text = request.json['text']
    
    try:
        # Use either built-in extraction or LangChain based on complexity
        if len(text) < 100:
            # Use built-in extraction for simpler inputs
            task_info = extract_task_info_from_text(text)
        else:
            # Use LangChain for more complex inputs
            result = task_extraction_chain.run(text)
            try:
                task_info = json.loads(result)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM output: {result}")
                task_info = extract_task_info_from_text(text)
        
        # Create the task
        task_id = database.add_task(
            title=task_info.get('title'),
            description=task_info.get('description'),
            due_date=task_info.get('due_date'),
            effort=task_info.get('effort', 5),
            consequences=task_info.get('consequences', 5),
            desire=task_info.get('desire', 5)
        )
        
        return jsonify({
            "task_id": task_id,
            "task_info": task_info,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error processing NLP request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/task/<int:task_id>/repeat', methods=['POST'])
def increment_repetition(task_id):
    """Increment the repetition count for a task."""
    success = database.increase_repetition(task_id)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Task not found or could not be updated"}), 404

def process_task_creation(title, description, due_date, effort, consequences, desire):
    """Process task creation with proper type handling."""
    try:
        # Ensure all numeric values are integers
        effort = int(effort) if effort else 5
        consequences = int(consequences) if consequences else 5
        desire = int(desire) if desire else 5
        
        # Your task creation logic...
        # Make sure any calculations use consistent types
        
        return True, "Task created successfully"
    except Exception as e:
        return False, f"Error creating task: {str(e)}"

def start_server(host='0.0.0.0', port=5000, debug=False):
    """Start the Flask server."""
    logger.info(f"Starting MCP server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    start_server(debug=True)