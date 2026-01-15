"""Root agent (Level 1) - Receives tasks, distributes to intermediates, aggregates results."""

import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from models import Task, IntermediateResult, RootResult, HealthResponse, UpdateChildrenRequest
from config import PORTS, get_agent_url, TREE_STRUCTURE


class RootAgent:
    def __init__(self):
        self.name = "root"
        self.children = TREE_STRUCTURE["root"].copy()
        self.intermediate_children = {
            "intermediate_left": TREE_STRUCTURE["intermediate_left"].copy(),
            "intermediate_right": TREE_STRUCTURE["intermediate_right"].copy(),
        }
        self.tokens_by_intermediate = {
            "intermediate_left": 0,
            "intermediate_right": 0,
        }
        self.load_balance_threshold = 0.3  # 30% difference triggers rebalancing
        self.total_tasks = 0

    async def forward_task_to_intermediate(self, intermediate_name: str, task: Task) -> IntermediateResult:
        """Forward a task to an intermediate agent."""
        url = f"{get_agent_url(intermediate_name)}/task"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=task.model_dump())
            response.raise_for_status()
            return IntermediateResult(**response.json())

    async def process_task(self, task: Task) -> RootResult:
        """Distribute task to intermediates and aggregate results."""
        self.total_tasks += 1

        # Forward to both intermediates in parallel
        tasks = [
            self.forward_task_to_intermediate(child, task)
            for child in self.children
        ]

        intermediate_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and track tokens
        successful_results = []
        for i, result in enumerate(intermediate_results):
            if isinstance(result, IntermediateResult):
                successful_results.append(result)
                self.tokens_by_intermediate[result.agent_name] += result.total_tokens
            elif isinstance(result, Exception):
                print(f"Error from intermediate '{self.children[i]}': {result}")

        total_tokens = sum(r.total_tokens for r in successful_results)

        return RootResult(
            task_id=task.task_id,
            total_tokens=total_tokens,
            intermediate_results=successful_results
        )

    async def check_and_rebalance(self) -> dict:
        """Check load imbalance and rebalance if necessary."""
        left_tokens = self.tokens_by_intermediate["intermediate_left"]
        right_tokens = self.tokens_by_intermediate["intermediate_right"]
        total = left_tokens + right_tokens

        if total == 0:
            return {"rebalanced": False, "reason": "No tokens processed yet"}

        left_ratio = left_tokens / total
        right_ratio = right_tokens / total

        imbalance = abs(left_ratio - right_ratio)

        if imbalance < self.load_balance_threshold:
            return {
                "rebalanced": False,
                "reason": f"Imbalance {imbalance:.2%} below threshold {self.load_balance_threshold:.0%}",
                "left_tokens": left_tokens,
                "right_tokens": right_tokens
            }

        # Determine heavier and lighter intermediate
        if left_tokens > right_tokens:
            heavier = "intermediate_left"
            lighter = "intermediate_right"
        else:
            heavier = "intermediate_right"
            lighter = "intermediate_left"

        heavier_children = self.intermediate_children[heavier]
        lighter_children = self.intermediate_children[lighter]

        # Can't rebalance if heavier has only one child
        if len(heavier_children) <= 1:
            return {
                "rebalanced": False,
                "reason": f"Cannot rebalance: {heavier} has only {len(heavier_children)} children",
                "left_tokens": left_tokens,
                "right_tokens": right_tokens
            }

        # Move one leaf from heavier to lighter
        leaf_to_move = heavier_children.pop()
        lighter_children.append(leaf_to_move)

        # Update the intermediate agents
        try:
            await self._update_intermediate_children(heavier, heavier_children)
            await self._update_intermediate_children(lighter, lighter_children)

            # Reset token counters after rebalancing
            self.tokens_by_intermediate["intermediate_left"] = 0
            self.tokens_by_intermediate["intermediate_right"] = 0

            return {
                "rebalanced": True,
                "moved_leaf": leaf_to_move,
                "from": heavier,
                "to": lighter,
                "new_structure": {
                    "intermediate_left": self.intermediate_children["intermediate_left"],
                    "intermediate_right": self.intermediate_children["intermediate_right"]
                }
            }
        except Exception as e:
            # Rollback on failure
            lighter_children.remove(leaf_to_move)
            heavier_children.append(leaf_to_move)
            return {"rebalanced": False, "reason": f"Failed to update intermediates: {e}"}

    async def _update_intermediate_children(self, intermediate_name: str, new_children: list[str]):
        """Send update_children request to an intermediate agent."""
        url = f"{get_agent_url(intermediate_name)}/update_children"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={"new_children": new_children})
            response.raise_for_status()

    def get_health(self) -> HealthResponse:
        """Return health status."""
        return HealthResponse(
            status="healthy",
            agent_name=self.name,
            agent_type="root",
            children=self.children
        )


def create_app() -> FastAPI:
    """Create FastAPI app for the root agent."""
    agent = RootAgent()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print(f"Root agent starting with children: {agent.children}")
        yield
        print("Root agent shutting down...")

    app = FastAPI(
        title="Root Agent",
        lifespan=lifespan
    )

    @app.post("/task", response_model=RootResult)
    async def handle_task(task: Task):
        """Receive a task, distribute to intermediates, and return aggregated results."""
        try:
            return await agent.process_task(task)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Return health status."""
        return agent.get_health()

    @app.post("/rebalance")
    async def rebalance():
        """Manually trigger load balancing check."""
        return await agent.check_and_rebalance()

    @app.get("/stats")
    async def get_stats():
        """Return agent statistics and current tree structure."""
        return {
            "agent_name": agent.name,
            "total_tasks": agent.total_tasks,
            "tokens_by_intermediate": agent.tokens_by_intermediate,
            "tree_structure": agent.intermediate_children,
            "load_balance_threshold": agent.load_balance_threshold
        }

    @app.post("/set_threshold")
    async def set_threshold(threshold: float):
        """Set the load balance threshold (0.0 to 1.0)."""
        if not 0.0 <= threshold <= 1.0:
            raise HTTPException(status_code=400, detail="Threshold must be between 0.0 and 1.0")
        agent.load_balance_threshold = threshold
        return {"threshold": agent.load_balance_threshold}

    return app


if __name__ == "__main__":
    import uvicorn

    port = PORTS["root"]
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=port)
