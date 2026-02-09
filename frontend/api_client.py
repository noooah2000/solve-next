"""
API Client Module for SolveNext Frontend

This module handles all HTTP communication with the FastAPI backend.
No Streamlit code should be present in this file.
"""

import requests

# Backend API base URL
API_BASE_URL = "http://127.0.0.1:8000"


def check_backend_connection():
    """Check if backend server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def signup(username: str):
    """Sign up a new user via backend API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/signup",
            params={"username": username},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return True, data, "Account created successfully!"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, None, f"Sign up failed: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, None, f"Connection error: {str(e)}"


def login(username: str):
    """Login user via backend API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            params={"username": username},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return True, data, "Login successful!"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, None, f"Login failed: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, None, f"Connection error: {str(e)}"


def create_log(username: str, problem_slug: str, status: str, note: str):
    """Create a new practice log"""
    try:
        payload = {
            "username": username,
            "problem_slug": problem_slug,
            "status": status,
            "note": note if note else None
        }
        response = requests.post(
            f"{API_BASE_URL}/logs",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return True, "Log saved successfully!"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Error: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def get_user_logs(user_id: int):
    """Get user's practice history"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/users/{user_id}/logs",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.RequestException:
        return []


def delete_log(log_id: int):
    """Delete a specific practice log"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/logs/{log_id}",
            timeout=5
        )
        if response.status_code == 200:
            return True, "Log deleted successfully!"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Error: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def get_trash_logs(user_id: int):
    """Get user's trashed logs"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/users/{user_id}/logs/trash",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.RequestException:
        return []


def restore_log(log_id: int):
    """Restore a soft-deleted log"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/logs/{log_id}/restore",
            timeout=5
        )
        if response.status_code == 200:
            return True, "Log restored successfully!"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Error: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def empty_trash(user_id: int):
    """Permanently delete all trash logs"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/users/{user_id}/logs/trash/empty",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return True, data.get("message", "Trash emptied!")
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Error: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def update_log(log_id: int, status: str, practice_date: str, note: str):
    """Update a practice log"""
    try:
        payload = {
            "status": status,
            "practice_date": practice_date,
            "note": note if note else None
        }
        response = requests.patch(
            f"{API_BASE_URL}/logs/{log_id}",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            return True, "Log updated successfully!"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Error: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def get_recommendations(username: str, tags: list, difficulty: str, count: int):
    """Get AI-powered recommendations"""
    try:
        payload = {
            "username": username,
            "tags": tags,
            "difficulty": difficulty,
            "count": count
        }
        response = requests.post(
            f"{API_BASE_URL}/recommendations",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", response.text)
            return False, error_detail
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"
