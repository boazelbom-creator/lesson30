#!/bin/bash

# Stop all agents

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}Stopping all agents...${NC}"

pkill -f "leaf_agent.py" 2>/dev/null || true
pkill -f "intermediate_agent.py" 2>/dev/null || true
pkill -f "root_agent.py" 2>/dev/null || true

sleep 1

echo -e "${GREEN}All agents stopped.${NC}"
