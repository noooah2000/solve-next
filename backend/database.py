from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine, Session, Relationship


class PracticeStatus(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    WITH_HINT = "WITH_HINT"
    STUCK = "STUCK"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationship
    logs: List["Log"] = Relationship(back_populates="user")


class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    problem_id: str
    problem_title: str
    difficulty: str
    tags: str  # Store as comma-separated string
    practice_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attempt_count: int = Field(default=1)
    status: PracticeStatus
    note: Optional[str] = None
    is_deleted: bool = Field(default=False)  # Soft delete flag
    
    # Relationship
    user: Optional[User] = Relationship(back_populates="logs")


# Database setup
sqlite_url = "sqlite:///solvenext.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for FastAPI to get database session"""
    with Session(engine) as session:
        yield session