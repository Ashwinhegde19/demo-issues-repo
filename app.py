from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Sample tasks data
tasks = [
    {"id": 1, "title": "Task 1", "status": "pending", "priority": "high", "assignee_id": 1},
    {"id": 2, "title": "Task 2", "status": "completed", "priority": "medium", "assignee_id": 2},
    {"id": 3, "title": "Task 3", "status": "in_progress", "priority": "low", "assignee_id": 1},
    {"id": 4, "title": "Task 4", "status": "pending", "priority": "high", "assignee_id": 3},
    {"id": 5, "title": "Task 5", "status": "completed", "priority": "low", "assignee_id": 2},
]

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """
    Get tasks with optional filtering and pagination.
    
    Query parameters:
    - status: Filter by task status (pending, in_progress, completed)
    - priority: Filter by priority level (low, medium, high)
    - assignee_id: Filter by assignee ID
    - limit: Number of tasks per page (default: 10, max: 100)
    - offset: Number of tasks to skip (default: 0)
    """
    filtered_tasks = tasks.copy()
    
    # Filter by status
    status = request.args.get('status')
    if status:
        filtered_tasks = [t for t in filtered_tasks if t['status'] == status]
    
    # Filter by priority
    priority = request.args.get('priority')
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority]
    
    # Filter by assignee_id
    assignee_id = request.args.get('assignee_id', type=int)
    if assignee_id is not None:
        filtered_tasks = [t for t in filtered_tasks if t['assignee_id'] == assignee_id]
    
    # Pagination
    total_count = len(filtered_tasks)
    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # Validate pagination parameters
    if limit < 1:
        limit = 10
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0
    
    # Apply pagination
    paginated_tasks = filtered_tasks[offset:offset + limit]
    
    return jsonify({
        "tasks": paginated_tasks,
        "count": len(paginated_tasks),
        "total_count": total_count,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        },
        "filters_applied": {
            "status": status,
            "priority": priority,
            "assignee_id": assignee_id
        }
    })

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.get_json()
    new_task = {
        "id": len(tasks) + 1,
        "title": data.get('title'),
        "status": data.get('status', 'pending'),
        "priority": data.get('priority', 'medium'),
        "assignee_id": data.get('assignee_id')
    }
    tasks.append(new_task)
    return jsonify(new_task), 201

if __name__ == '__main__':
    app.run(debug=True)
