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

def validate_task(task_data):
    required = ['title', 'description', 'status', 'priority']
    for field in required:
        if field not in task_data:
            return False, f"Missing required field: {field}"
    return True, None
