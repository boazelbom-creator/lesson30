"""Leaf agent (Level 3) - Processes tasks and returns token counts."""

import argparse
import random
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from models import Task, LeafResult, HealthResponse


class LeafAgent:
    def __init__(self, name: str):
        self.name = name
        self.tasks_processed = 0
        self.total_tokens = 0

    async def process_task(self, task: Task) -> LeafResult:
        """Simulate work by processing a task and returning tokens processed."""
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Generate random tokens processed (simulating work)
        tokens = random.randint(100, 1000)

        self.tasks_processed += 1
        self.total_tokens += tokens

        return LeafResult(
            agent_name=self.name,
            tokens_processed=tokens,
            task_id=task.task_id
        )

    def get_health(self) -> HealthResponse:
        """Return health status."""
        return HealthResponse(
            status="healthy",
            agent_name=self.name,
            agent_type="leaf",
            children=[]
        )


def create_app(agent_name: str) -> FastAPI:
    """Create FastAPI app for a leaf agent."""
    agent = LeafAgent(agent_name)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print(f"Leaf agent '{agent_name}' starting...")
        yield
        print(f"Leaf agent '{agent_name}' shutting down...")

    app = FastAPI(
        title=f"Leaf Agent - {agent_name}",
        lifespan=lifespan
    )

    @app.post("/task", response_model=LeafResult)
    async def handle_task(task: Task):
        """Process a task and return the result."""
        return await agent.process_task(task)

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Return health status."""
        return agent.get_health()

    @app.get("/stats")
    async def get_stats():
        """Return agent statistics."""
        return {
            "agent_name": agent.name,
            "tasks_processed": agent.tasks_processed,
            "total_tokens": agent.total_tokens
        }

    return app


if __name__ == "__main__":
    import uvicorn
    from config import PORTS

    parser = argparse.ArgumentParser(description="Run a leaf agent")
    parser.add_argument("--name", required=True, help="Agent name (leaf_0, leaf_1, leaf_2, leaf_3)")
    args = parser.parse_args()

    if args.name not in PORTS:
        print(f"Error: Unknown agent name '{args.name}'")
        exit(1)

    port = PORTS[args.name]
    app = create_app(args.name)
    uvicorn.run(app, host="0.0.0.0", port=port)
