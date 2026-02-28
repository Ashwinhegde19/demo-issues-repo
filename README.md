# Demo Issues Repo

This is a demo repository for showcasing GitHub issues.

## API Endpoints

### GET /tasks
Retrieve tasks with optional filtering.

**Query Parameters:**
- `status` - Filter by status: `pending`, `in_progress`, `completed`
- `priority` - Filter by priority: `low`, `medium`, `high`
- `assignee_id` - Filter by assignee ID (integer)

**Examples:**
```
GET /tasks?status=pending
GET /tasks?priority=high
GET /tasks?status=pending&priority=high
GET /tasks?assignee_id=1
```

### POST /tasks
Create a new task.

**Request Body:**
```json
{
  "title": "New Task",
  "status": "pending",
  "priority": "medium",
  "assignee_id": 1
}
```

## Running the App

```bash
pip install flask
python app.py
```

## Issues

See [Issues](../../issues) for the list of open tasks.
