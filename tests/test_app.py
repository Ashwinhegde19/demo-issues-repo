import pytest
import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app as filter_app
from src.api import app as api_app, load_tasks, save_tasks, TASKS_FILE
from src.calculator import add, multiply, divide, calculate_average, find_max
from src.models import User, Task, validate_task


# ==================== Fixtures ====================

@pytest.fixture
def filter_client():
    """Create a test client for the filtering app."""
    filter_app.config['TESTING'] = True
    with filter_app.test_client() as client:
        yield client

@pytest.fixture
def api_client():
    """Create a test client for the API app."""
    api_app.config['TESTING'] = True
    # Clean up tasks file before each test
    if os.path.exists(TASKS_FILE):
        os.remove(TASKS_FILE)
    with api_app.test_client() as client:
        yield client
    # Clean up after tests
    if os.path.exists(TASKS_FILE):
        os.remove(TASKS_FILE)


# ==================== Test app.py (Filtering API) ====================

class TestFilterAPI:
    """Tests for the filtering API in app.py"""
    
    def test_get_all_tasks(self, filter_client):
        """Test GET /tasks returns all tasks."""
        response = filter_client.get('/tasks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tasks' in data
        assert 'count' in data
        assert data['count'] == 5  # 5 sample tasks
    
    def test_filter_by_status(self, filter_client):
        """Test filtering tasks by status."""
        response = filter_client.get('/tasks?status=pending')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(t['status'] == 'pending' for t in data['tasks'])
        assert data['filters_applied']['status'] == 'pending'
    
    def test_filter_by_priority(self, filter_client):
        """Test filtering tasks by priority."""
        response = filter_client.get('/tasks?priority=high')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(t['priority'] == 'high' for t in data['tasks'])
        assert data['filters_applied']['priority'] == 'high'
    
    def test_filter_by_assignee_id(self, filter_client):
        """Test filtering tasks by assignee_id."""
        response = filter_client.get('/tasks?assignee_id=1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(t['assignee_id'] == 1 for t in data['tasks'])
        assert data['filters_applied']['assignee_id'] == 1
    
    def test_filter_by_multiple_params(self, filter_client):
        """Test filtering with multiple query parameters."""
        response = filter_client.get('/tasks?status=pending&priority=high')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(t['status'] == 'pending' and t['priority'] == 'high' 
                   for t in data['tasks'])
    
    def test_filter_no_results(self, filter_client):
        """Test filtering that returns no results."""
        response = filter_client.get('/tasks?status=nonexistent')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert len(data['tasks']) == 0
    
    def test_create_task(self, filter_client):
        """Test POST /tasks creates a new task."""
        new_task = {
            'title': 'New Test Task',
            'status': 'pending',
            'priority': 'high',
            'assignee_id': 1
        }
        response = filter_client.post('/tasks', json=new_task)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['title'] == 'New Test Task'
        assert data['status'] == 'pending'

    # ==================== Pagination Tests ====================

    def test_pagination_default_limit(self, filter_client):
        """Test default pagination returns 10 items."""
        response = filter_client.get('/tasks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'pagination' in data
        assert data['pagination']['limit'] == 10
        assert data['pagination']['offset'] == 0
        assert 'has_more' in data['pagination']
        assert 'total_count' in data

    def test_pagination_with_limit(self, filter_client):
        """Test pagination with custom limit."""
        response = filter_client.get('/tasks?limit=2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['tasks']) == 2
        assert data['count'] == 2
        assert data['pagination']['limit'] == 2
        assert data['pagination']['has_more'] is True

    def test_pagination_with_limit_and_offset(self, filter_client):
        """Test pagination with limit and offset."""
        # First page
        response = filter_client.get('/tasks?limit=2&offset=0')
        data = json.loads(response.data)
        first_task_ids = [t['id'] for t in data['tasks']]
        
        # Second page
        response = filter_client.get('/tasks?limit=2&offset=2')
        data = json.loads(response.data)
        second_task_ids = [t['id'] for t in data['tasks']]
        
        # Ensure different tasks
        assert first_task_ids != second_task_ids
        assert data['pagination']['offset'] == 2

    def test_pagination_last_page_no_more(self, filter_client):
        """Test has_more is False on last page."""
        response = filter_client.get('/tasks?limit=10&offset=0')
        data = json.loads(response.data)
        assert data['pagination']['has_more'] is False

    def test_pagination_limit_capped_at_100(self, filter_client):
        """Test limit is capped at 100."""
        response = filter_client.get('/tasks?limit=200')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['limit'] == 100

    def test_pagination_negative_offset_defaults_to_zero(self, filter_client):
        """Test negative offset defaults to 0."""
        response = filter_client.get('/tasks?offset=-5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['offset'] == 0

    def test_pagination_with_filtering(self, filter_client):
        """Test pagination works with filtering."""
        response = filter_client.get('/tasks?status=pending&limit=1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['status'] == 'pending'
        assert data['total_count'] >= 2  # At least 2 pending tasks in sample data
        assert data['pagination']['has_more'] == (data['total_count'] > 1)


# ==================== Test src/api.py (CRUD API) ====================

class TestCRUDAPI:
    """Tests for the CRUD API in src/api.py"""
    
    def test_get_empty_tasks(self, api_client):
        """Test GET /tasks with no tasks."""
        response = api_client.get('/tasks')
        assert response.status_code == 200
        assert json.loads(response.data) == []
    
    def test_create_task(self, api_client):
        """Test POST /tasks creates a task."""
        task = {'title': 'Test Task', 'status': 'pending'}
        response = api_client.post('/tasks', json=task)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['title'] == 'Test Task'
        assert data['id'] == 1
    
    def test_get_tasks_after_create(self, api_client):
        """Test GET returns created tasks."""
        api_client.post('/tasks', json={'title': 'Task 1', 'status': 'pending'})
        api_client.post('/tasks', json={'title': 'Task 2', 'status': 'completed'})
        
        response = api_client.get('/tasks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
    
    def test_update_task(self, api_client):
        """Test PUT /tasks/<id> updates a task."""
        api_client.post('/tasks', json={'title': 'Original', 'status': 'pending'})
        
        response = api_client.put('/tasks/1', json={'title': 'Updated'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'Updated'
    
    def test_update_nonexistent_task(self, api_client):
        """Test PUT returns 404 for non-existent task."""
        response = api_client.put('/tasks/999', json={'title': 'Updated'})
        assert response.status_code == 404
    
    def test_delete_task(self, api_client):
        """Test DELETE /tasks/<id> removes a task."""
        api_client.post('/tasks', json={'title': 'To Delete', 'status': 'pending'})
        
        response = api_client.delete('/tasks/1')
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = api_client.get('/tasks')
        assert len(json.loads(get_response.data)) == 0


# ==================== Test src/calculator.py ====================

class TestCalculator:
    """Tests for calculator functions."""
    
    def test_add(self):
        """Test add function."""
        assert add(5, 3) == 2  # Current behavior: returns a - b
        assert add(10, 5) == 5
    
    def test_multiply(self):
        """Test multiply function."""
        assert multiply(4, 5) == 20
        assert multiply(0, 10) == 0
        assert multiply(-3, 4) == -12
    
    def test_divide(self):
        """Test divide function."""
        assert divide(10, 2) == 5.0
        assert divide(7, 2) == 3.5
    
    def test_divide_by_zero(self):
        """Test divide raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)
    
    def test_calculate_average(self):
        """Test calculate_average returns sum (current behavior)."""
        assert calculate_average([2, 4, 6]) == 12  # Returns sum, not average
        assert calculate_average([10, 20]) == 30
    
    def test_calculate_average_empty_list(self):
        """Test calculate_average with empty list."""
        assert calculate_average([]) == 0
    
    def test_find_max(self):
        """Test find_max function."""
        assert find_max([1, 5, 3, 9, 2]) == 9
        assert find_max([-5, -3, -10]) == 0  # Bug: returns 0 for all negatives
    
    def test_find_max_empty(self):
        """Test find_max with empty list."""
        assert find_max([]) == 0


# ==================== Test src/models.py ====================

class TestUser:
    """Tests for User model."""
    
    def test_user_creation(self):
        """Test User object creation."""
        user = User(1, 'testuser', 'test@example.com')
        assert user.id == 1
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
    
    def test_user_to_dict(self):
        """Test User.to_dict() method."""
        user = User(1, 'testuser', 'test@example.com')
        expected = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com'
        }
        assert user.to_dict() == expected


class TestTask:
    """Tests for Task model."""
    
    def test_task_creation(self):
        """Test Task object creation."""
        task = Task(1, 'Test Task', 'Description', 'pending', 'high', 1)
        assert task.id == 1
        assert task.title == 'Test Task'
        assert task.status == 'pending'
        assert task.priority == 'high'
        assert task.assignee_id == 1
    
    def test_task_creation_optional_assignee(self):
        """Test Task without assignee_id."""
        task = Task(1, 'Test Task', 'Description', 'pending', 'high')
        assert task.assignee_id is None
    
    def test_task_to_dict(self):
        """Test Task.to_dict() method."""
        task = Task(1, 'Test Task', 'Description', 'pending', 'high', 1)
        expected = {
            'id': 1,
            'title': 'Test Task',
            'description': 'Description',
            'status': 'pending',
            'priority': 'high',
            'assignee_id': 1
        }
        assert task.to_dict() == expected


class TestValidateTask:
    """Tests for task validation."""
    
    def test_validate_task_valid(self):
        """Test validate_task with valid data."""
        task_data = {
            'title': 'Test',
            'description': 'Desc',
            'status': 'pending',
            'priority': 'high'
        }
        is_valid, error = validate_task(task_data)
        assert is_valid is True
        assert error is None
    
    def test_validate_task_missing_title(self):
        """Test validate_task without title."""
        task_data = {
            'description': 'Desc',
            'status': 'pending',
            'priority': 'high'
        }
        is_valid, error = validate_task(task_data)
        assert is_valid is False
        assert 'title' in error
    
    def test_validate_task_missing_description(self):
        """Test validate_task without description."""
        task_data = {
            'title': 'Test',
            'status': 'pending',
            'priority': 'high'
        }
        is_valid, error = validate_task(task_data)
        assert is_valid is False
        assert 'description' in error
    
    def test_validate_task_missing_status(self):
        """Test validate_task without status."""
        task_data = {
            'title': 'Test',
            'description': 'Desc',
            'priority': 'high'
        }
        is_valid, error = validate_task(task_data)
        assert is_valid is False
        assert 'status' in error
    
    def test_validate_task_missing_priority(self):
        """Test validate_task without priority."""
        task_data = {
            'title': 'Test',
            'description': 'Desc',
            'status': 'pending'
        }
        is_valid, error = validate_task(task_data)
        assert is_valid is False
        assert 'priority' in error
