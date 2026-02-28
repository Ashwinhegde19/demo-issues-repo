from flask import Flask, jsonify, request
import json
import os
from src.models import validate_task

app = Flask(__name__)

TASKS_FILE = 'tasks.json'

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f)

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = load_tasks()
    return jsonify(tasks)

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task with input validation."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    is_valid, errors = validate_task(data)
    if not is_valid:
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    tasks = load_tasks()
    task = {
        'id': len(tasks) + 1,
        'title': data['title'],
        'description': data.get('description', ''),
        'status': data['status'],
        'priority': data['priority'],
        'assignee_id': data.get('assignee_id')
    }
    tasks.append(task)
    save_tasks(tasks)
    return jsonify(task), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task with input validation."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    tasks = load_tasks()
    for task in tasks:
        if task['id'] == task_id:
            # Merge existing fields with update for validation
            merged = {**task, **data}
            is_valid, errors = validate_task(merged)
            if not is_valid:
                return jsonify({"error": "Validation failed", "fields": errors}), 400

            task.update(data)
            save_tasks(tasks)
            return jsonify(task)

    return jsonify({"error": "Task not found"}), 404

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    tasks = load_tasks()
    original_len = len(tasks)
    tasks = [t for t in tasks if t['id'] != task_id]
    if len(tasks) == original_len:
        return jsonify({"error": "Task not found"}), 404
    save_tasks(tasks)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
