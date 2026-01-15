"""Intermediate agent (Level 2) - Forwards tasks to leaves and aggregates results."""

import argparse
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from models import Task, LeafResult, IntermediateResult, HealthResponse, UpdateChildrenRequest
from config import PORTS, get_agent_url, TREE_STRUCTURE


class IntermediateAgent:
    def __init__(self, name: str, children: list[str]):
        self.name = name
        self.children = children
        self.total_tokens_processed = 0

    async def forward_task_to_child(self, child_name: str, task: Task) -> LeafResult:
        """Forward a task to a child leaf agent."""
        url = f"{get_agent_url(child_name)}/task"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=task.model_dump())
            response.raise_for_status()
            return LeafResult(**response.json())

    async def process_task(self, task: Task) -> IntermediateResult:
        """Forward task to all children and aggregate results."""
        if not self.children:
            return IntermediateResult(
                agent_name=self.name,
                total_tokens=0,
                leaf_results=[],
                task_id=task.task_id
            )

        # Forward task to all children in parallel
        tasks = [
            self.forward_task_to_child(child, task)
            for child in self.children
        ]

        leaf_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors and collect successful results
        successful_results = []
        for result in leaf_results:
            if isinstance(result, LeafResult):
                successful_results.append(result)
            elif isinstance(result, Exception):
                print(f"Error from child: {result}")

        total_tokens = sum(r.tokens_processed for r in successful_results)
        self.total_tokens_processed += total_tokens

        return IntermediateResult(
            agent_name=self.name,
            total_tokens=total_tokens,
            leaf_results=successful_results,
            task_id=task.task_id
        )

    def update_children(self, new_children: list[str]):
        """Update the list of children."""
        self.children = new_children
        print(f"Agent '{self.name}' updated children to: {self.children}")

    def get_health(self) -> HealthResponse:
        """Return health status."""
        return HealthResponse(
            status="healthy",
            agent_name=self.name,
            agent_type="intermediate",
            children=self.children
        )


def create_app(agent_name: str) -> FastAPI:
    """Create FastAPI app for an intermediate agent."""
    initial_children = TREE_STRUCTURE.get(agent_name, [])
    agent = IntermediateAgent(agent_name, initial_children)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print(f"Intermediate agent '{agent_name}' starting with children: {agent.children}")
        yield
        print(f"Intermediate agent '{agent_name}' shutting down...")

    app = FastAPI(
        title=f"Intermediate Agent - {agent_name}",
        lifespan=lifespan
    )

    @app.post("/task", response_model=IntermediateResult)
    async def handle_task(task: Task):
        """Forward task to children and return aggregated results."""
        try:
            return await agent.process_task(task)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Return health status."""
        return agent.get_health()

    @app.post("/update_children")
    async def update_children(request: UpdateChildrenRequest):
        """Update the agent's children list (for load balancing)."""
        agent.update_children(request.new_children)
        return {"status": "updated", "new_children": agent.children}

    @app.get("/stats")
    async def get_stats():
        """Return agent statistics."""
        return {
            "agent_name": agent.name,
            "children": agent.children,
            "total_tokens_processed": agent.total_tokens_processed
        }

    return app


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="Run an intermediate agent")
    parser.add_argument("--name", required=True, help="Agent name (intermediate_left, intermediate_right)")
    args = parser.parse_args()

    if args.name not in PORTS:
        print(f"Error: Unknown agent name '{args.name}'")
        exit(1)

    port = PORTS[args.name]
    app = create_app(args.name)
    uvicorn.run(app, host="0.0.0.0", port=port)
