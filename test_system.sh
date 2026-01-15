#!/bin/bash

# Test script for the Multi-Agent System
# Run this after launching all agents with ./launch_agents.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Multi-Agent System Tests${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Test 1: Health checks for all agents
echo -e "${BLUE}Test 1: Health Checks${NC}"
echo "--------------------"

echo "Root Agent (port 8000):"
curl -s ${BASE_URL}:8000/health | python3 -m json.tool
echo ""

echo "Intermediate Left (port 8001):"
curl -s ${BASE_URL}:8001/health | python3 -m json.tool
echo ""

echo "Intermediate Right (port 8002):"
curl -s ${BASE_URL}:8002/health | python3 -m json.tool
echo ""

echo "Leaf 0 (port 8003):"
curl -s ${BASE_URL}:8003/health | python3 -m json.tool
echo ""

# Test 2: Submit a task to the root
echo -e "${BLUE}Test 2: Submit Task to Root${NC}"
echo "---------------------------"
echo "Sending task to root agent..."
curl -s -X POST ${BASE_URL}:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task-001", "description": "Process this data", "data": {"key": "value"}}' \
  | python3 -m json.tool
echo ""

# Test 3: Check stats
echo -e "${BLUE}Test 3: Check Agent Stats${NC}"
echo "-------------------------"
echo "Root stats:"
curl -s ${BASE_URL}:8000/stats | python3 -m json.tool
echo ""

# Test 4: Submit multiple tasks
echo -e "${BLUE}Test 4: Submit Multiple Tasks${NC}"
echo "-----------------------------"
for i in {1..5}; do
  echo "Sending task $i..."
  curl -s -X POST ${BASE_URL}:8000/task \
    -H "Content-Type: application/json" \
    -d "{\"task_id\": \"task-00$i\", \"description\": \"Task number $i\"}" \
    | python3 -m json.tool
  echo ""
done

# Test 5: Check updated stats
echo -e "${BLUE}Test 5: Check Stats After Tasks${NC}"
echo "-------------------------------"
echo "Root stats:"
curl -s ${BASE_URL}:8000/stats | python3 -m json.tool
echo ""

# Test 6: Trigger rebalancing
echo -e "${BLUE}Test 6: Trigger Load Rebalancing${NC}"
echo "--------------------------------"
echo "Checking if rebalancing is needed..."
curl -s -X POST ${BASE_URL}:8000/rebalance | python3 -m json.tool
echo ""

# Test 7: Check tree structure after potential rebalancing
echo -e "${BLUE}Test 7: Check Tree Structure${NC}"
echo "----------------------------"
echo "Intermediate Left children:"
curl -s ${BASE_URL}:8001/health | python3 -m json.tool
echo ""
echo "Intermediate Right children:"
curl -s ${BASE_URL}:8002/health | python3 -m json.tool
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All tests completed!${NC}"
echo -e "${GREEN}========================================${NC}"
