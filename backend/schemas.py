from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .database import PracticeStatus


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class TopicTag(str, Enum):
    ARRAY = "Array"
    STRING = "String"
    HASH_TABLE = "Hash Table"
    DYNAMIC_PROGRAMMING = "Dynamic Programming"
    MATH = "Math"
    SORTING = "Sorting"
    GREEDY = "Greedy"
    DEPTH_FIRST_SEARCH = "Depth-First Search"
    BREADTH_FIRST_SEARCH = "Breadth-First Search"
    BINARY_SEARCH = "Binary Search"
    TREE = "Tree"
    GRAPH = "Graph"
    BACKTRACKING = "Backtracking"
    LINKED_LIST = "Linked List"
    STACK = "Stack"
    QUEUE = "Queue"
    HEAP = "Heap"
    TRIE = "Trie"
    SLIDING_WINDOW = "Sliding Window"
    TWO_POINTERS = "Two Pointers"


# Request Models
class CreateLogRequest(BaseModel):
    username: str
    problem_slug: str
    status: PracticeStatus
    note: Optional[str] = None


class UpdateLogRequest(BaseModel):
    practice_date: Optional[datetime] = None
    status: Optional[PracticeStatus] = None
    note: Optional[str] = None
    
    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    username: str
    tags: List[TopicTag]
    difficulty: Difficulty
    count: int = 5
    source_list: Optional[str] = None
    target_companies: Optional[List[str]] = None


# Response Models
class LogResponse(BaseModel):
    id: int
    user_id: int
    problem_id: str
    problem_title: str
    difficulty: str
    tags: str
    practice_date: datetime
    attempt_count: int
    status: PracticeStatus
    note: Optional[str] = None
    time_spent: Optional[int] = None
    is_deleted: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class RecommendedProblem(BaseModel):
    problem_title: str
    difficulty: str
    reason: str
    leetcode_url: str


class RecommendationResponse(BaseModel):
    advice: str
    problems: List[RecommendedProblem]