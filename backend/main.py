from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import create_db_and_tables
from .routers import auth, logs, users, problems, ai


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup logic
    create_db_and_tables()
    yield
    # Shutdown logic (pass for now)


# Initialize FastAPI app
app = FastAPI(title="SolveNext API", lifespan=lifespan)

# Include routers
app.include_router(auth.router, tags=["Auth"])
app.include_router(logs.router, tags=["Logs"])
app.include_router(users.router, tags=["Users"])
app.include_router(problems.router, tags=["Problems"])
app.include_router(ai.router, tags=["AI"])


@app.get("/")
def read_root():
    """Root endpoint - welcome message"""
    return {
        "message": "Welcome to SolveNext API",
        "version": "1.0.0",
        "endpoints": {
            "signup": "POST /auth/signup",
            "login": "POST /auth/login",
            "create_log": "POST /logs",
            "get_user_logs": "GET /users/{user_id}/logs",
            "update_log": "PATCH /logs/{log_id}",
            "delete_log": "DELETE /logs/{log_id}",
            "get_trash": "GET /users/{user_id}/logs/trash",
            "restore_log": "POST /logs/{log_id}/restore",
            "empty_trash": "DELETE /users/{user_id}/logs/trash/empty",
            "get_recommendations": "POST /recommendations"
        }
    }
