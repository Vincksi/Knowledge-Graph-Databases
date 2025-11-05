#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration from environment variables
APP_HOST=${APP_HOST:-app}
APP_PORT=${APP_PORT:-8000}
PG_HOST=${PG_HOST:-postgres}
PG_USER=${POSTGRES_USER:-postgres}
PG_PASSWORD=${POSTGRES_PASSWORD:-postgres}
PG_DB=${POSTGRES_DB:-shop}

# Export password for psql
export PGPASSWORD=$PG_PASSWORD

# Function to run psql commands
run_psql() {
    psql -h $PG_HOST -U $PG_USER -d $PG_DB -c "$1"
}

echo -e "${GREEN}Starting container checks...${NC}"

# Check FastAPI health endpoint
echo -e "\n${YELLOW}1. Checking FastAPI health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s http://$APP_HOST:$APP_PORT/health || true)
echo "Health endpoint response: $HEALTH_RESPONSE"

if [[ $HEALTH_RESPONSE == *'"ok":true'* ]]; then
    echo -e "${GREEN}✓ FastAPI health check passed${NC}"
else
    echo -e "${RED}✗ FastAPI health check failed${NC}"
    exit 1
fi

# Run Postgres sanity checks
echo -e "\n${YELLOW}2. Running Postgres sanity checks...${NC}"

echo "Querying orders table:"
if ! run_psql "SELECT * FROM orders LIMIT 5;"; then
    echo -e "${RED}✗ First Postgres query failed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ First Postgres query succeeded${NC}"
fi

echo -e "\nChecking database time:"
if ! run_psql "SELECT now();"; then
    echo -e "${RED}✗ Second Postgres query failed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Second Postgres query succeeded${NC}"
fi

# Run and validate ETL process
echo -ne "\n${YELLOW}3. Running ETL process...${NC}"
if ! ETL_OUTPUT=$(python3 /app/etl.py 2>&1); then
    echo -e "\n${RED}✗ ETL Failed${NC}"
    echo "$ETL_OUTPUT"
    exit 1
elif echo "$ETL_OUTPUT" | grep -q "ETL Process Completed Successfully"; then
    echo -e "\n${GREEN}✓ ETL Done${NC}"
else
    echo -e "\n${RED}✗ ETL output validation failed${NC}"
    echo "$ETL_OUTPUT"
    exit 1
fi

echo -e "\n${GREEN}All checks completed successfully!${NC}"
