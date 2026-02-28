class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

class Task:
    def __init__(self, id, title, description, status, priority, assignee_id=None):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.assignee_id = assignee_id

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assignee_id': self.assignee_id
        }


VALID_STATUSES = ('pending', 'in_progress', 'completed')
VALID_PRIORITIES = ('low', 'medium', 'high')


def validate_task(task_data):
    """Validate task data with field-level error reporting.

    Rules:
    - title: required, string, 3-100 characters
    - description: required, string, max 500 characters
    - status: required, one of pending/in_progress/completed
    - priority: required, one of low/medium/high

    Returns:
        (True, None) on success
        (False, dict) on failure -- dict maps field names to error messages
    """
    errors = {}

    # title: required, 3-100 chars
    if 'title' not in task_data:
        errors['title'] = 'Missing required field: title'
    elif not isinstance(task_data['title'], str):
        errors['title'] = 'Title must be a string'
    elif len(task_data['title']) < 3 or len(task_data['title']) > 100:
        errors['title'] = 'Title must be between 3 and 100 characters'

    # description: required, max 500 chars
    if 'description' not in task_data:
        errors['description'] = 'Missing required field: description'
    elif not isinstance(task_data['description'], str):
        errors['description'] = 'Description must be a string'
    elif len(task_data['description']) > 500:
        errors['description'] = 'Description must be at most 500 characters'

    # status: required, enum
    if 'status' not in task_data:
        errors['status'] = 'Missing required field: status'
    elif task_data['status'] not in VALID_STATUSES:
        errors['status'] = f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"

    # priority: required, enum
    if 'priority' not in task_data:
        errors['priority'] = 'Missing required field: priority'
    elif task_data['priority'] not in VALID_PRIORITIES:
        errors['priority'] = f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}"

    if errors:
        return False, errors
    return True, None
