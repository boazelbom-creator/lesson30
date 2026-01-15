"""Shared data models for the multi-agent system."""

from typing import Optional
from pydantic import BaseModel


class Task(BaseModel):
    """Task to be processed by agents."""
    task_id: str
    description: str
    data: Optional[dict] = None


class LeafResult(BaseModel):
    """Result from a leaf agent."""
    agent_name: str
    tokens_processed: int
    task_id: str


class IntermediateResult(BaseModel):
    """Aggregated result from an intermediate agent."""
    agent_name: str
    total_tokens: int
    leaf_results: list[LeafResult]
    task_id: str


class RootResult(BaseModel):
    """Final aggregated result from root agent."""
    task_id: str
    total_tokens: int
    intermediate_results: list[IntermediateResult]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent_name: str
    agent_type: str
    children: list[str]


class UpdateChildrenRequest(BaseModel):
    """Request to update an agent's children."""
    new_children: list[str]
