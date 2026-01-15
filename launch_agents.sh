#!/bin/bash

# Multi-Agent System Launcher
# This script launches all 7 agents in the binary tree structure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Multi-Agent System Launcher${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down all agents...${NC}"
    pkill -f "leaf_agent.py" 2>/dev/null || true
    pkill -f "intermediate_agent.py" 2>/dev/null || true
    pkill -f "root_agent.py" 2>/dev/null || true
    echo -e "${GREEN}All agents stopped.${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Kill any existing agents
echo -e "${YELLOW}Cleaning up any existing agents...${NC}"
pkill -f "leaf_agent.py" 2>/dev/null || true
pkill -f "intermediate_agent.py" 2>/dev/null || true
pkill -f "root_agent.py" 2>/dev/null || true
sleep 1

# Create logs directory
mkdir -p logs

echo -e "${GREEN}Starting agents...${NC}"

# Start leaf agents (Level 3)
echo -e "  Starting leaf agents..."
python leaf_agent.py --name leaf_0 > logs/leaf_0.log 2>&1 &
python leaf_agent.py --name leaf_1 > logs/leaf_1.log 2>&1 &
python leaf_agent.py --name leaf_2 > logs/leaf_2.log 2>&1 &
python leaf_agent.py --name leaf_3 > logs/leaf_3.log 2>&1 &

# Wait for leaf agents to start
sleep 2

# Start intermediate agents (Level 2)
echo -e "  Starting intermediate agents..."
python intermediate_agent.py --name intermediate_left > logs/intermediate_left.log 2>&1 &
python intermediate_agent.py --name intermediate_right > logs/intermediate_right.log 2>&1 &

# Wait for intermediate agents to start
sleep 2

# Start root agent (Level 1)
echo -e "  Starting root agent..."
python root_agent.py > logs/root.log 2>&1 &

# Wait for root agent to start
sleep 2

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All agents started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Agent Ports:"
echo -e "  Root:               http://localhost:8000"
echo -e "  Intermediate Left:  http://localhost:8001"
echo -e "  Intermediate Right: http://localhost:8002"
echo -e "  Leaf 0:             http://localhost:8003"
echo -e "  Leaf 1:             http://localhost:8004"
echo -e "  Leaf 2:             http://localhost:8005"
echo -e "  Leaf 3:             http://localhost:8006"
echo ""
echo -e "Logs available in: ${SCRIPT_DIR}/logs/"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all agents${NC}"

# Wait for all background processes
wait
