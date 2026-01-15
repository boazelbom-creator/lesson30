"""Configuration for the multi-agent system."""

# Port assignments for each agent
PORTS = {
    "root": 8000,
    "intermediate_left": 8001,
    "intermediate_right": 8002,
    "leaf_0": 8003,
    "leaf_1": 8004,
    "leaf_2": 8005,
    "leaf_3": 8006,
}

# Initial tree structure (parent -> children mapping)
TREE_STRUCTURE = {
    "root": ["intermediate_left", "intermediate_right"],
    "intermediate_left": ["leaf_0", "leaf_1"],
    "intermediate_right": ["leaf_2", "leaf_3"],
}

BASE_URL = "http://localhost"


def get_agent_url(agent_name: str) -> str:
    """Get the full URL for an agent."""
    return f"{BASE_URL}:{PORTS[agent_name]}"
