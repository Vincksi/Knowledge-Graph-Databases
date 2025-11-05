#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting container checks...${NC}"

# Check FastAPI health endpoint
echo -e "\n${YELLOW}1. Checking FastAPI health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s http://127.0.0.1:8000/health || true)
echo "Health endpoint response: $HEALTH_RESPONSE"

if [[ $HEALTH_RESPONSE == *"\"ok\":true"* ]]; then
    echo -e "${GREEN}✓ FastAPI health check passed${NC}"
else
    echo -e "${RED}✗ FastAPI health check failed${NC}"
    exit 1
fi

# Run Postgres sanity checks
echo -e "\n${YELLOW}2. Running Postgres sanity checks...${NC}"

echo "Querying orders table:"
docker compose exec -T postgres psql -U postgres -d shop -c "SELECT * FROM orders LIMIT 5;"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ First Postgres query succeeded${NC}"
else
    echo -e "${RED}✗ First Postgres query failed${NC}"
    exit 1
fi

echo -e "\nChecking database time:"
docker compose exec -T postgres psql -U postgres -d shop -c "SELECT now();"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Second Postgres query succeeded${NC}"
else
    echo -e "${RED}✗ Second Postgres query failed${NC}"
    exit 1
fi

# Run and validate ETL process
echo -ne "\n${YELLOW}3. Running ETL process...${NC}"
ETL_OUTPUT=$(docker compose exec -T app python3 /app/etl.py 2>&1)

if echo "$ETL_OUTPUT" | grep -q "ETL Process Completed Successfully"; then
    echo -e "\n${GREEN}✓ ETL Done${NC}"
else
    echo -e "\n${RED}✗ ETL Failed${NC}"
    echo "$ETL_OUTPUT"
    exit 1
fi

echo -e "\n${GREEN}All checks completed successfully!${NC}"