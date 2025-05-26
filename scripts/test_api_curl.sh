#!/bin/bash
# Curl-based test script for SurgeonMatch API endpoints
# Following SurgeonMatch Project Standards for testing

# Configuration
API_BASE_URL="http://localhost:8888"
API_KEY="7716103218ca43bed0aabe70c382eea2cecd676e990190bf66c701712b1a6136"
API_PREFIX="/api/v1"

# Text colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to test an endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2
    local method=${3:-GET}
    local data=${4:-""}
    
    echo -e "\n${YELLOW}Testing ${method} ${endpoint}: ${description}${NC}"
    
    # Build the curl command
    if [ "$method" = "GET" ]; then
        response=$(curl -s -X $method -H "X-API-Key: $API_KEY" "${API_BASE_URL}${endpoint}")
    else
        response=$(curl -s -X $method -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" -d "$data" "${API_BASE_URL}${endpoint}")
    fi
    
    # Check if the response is valid JSON
    if echo "$response" | jq . > /dev/null 2>&1; then
        # Get HTTP status code
        status_code=$(curl -s -o /dev/null -w "%{http_code}" -X $method -H "X-API-Key: $API_KEY" "${API_BASE_URL}${endpoint}")
        
        if [[ $status_code -ge 200 && $status_code -lt 300 ]]; then
            echo -e "${GREEN}✓ Success (HTTP $status_code)${NC}"
            echo -e "Response: $(echo "$response" | jq -r '.' | head -n 10)"
            if [[ $(echo "$response" | jq -r '.' | wc -l) -gt 10 ]]; then
                echo -e "... (response truncated)"
            fi
            return 0
        else
            echo -e "${RED}✗ Failed (HTTP $status_code)${NC}"
            echo -e "Response: $response"
            return 1
        fi
    else
        echo -e "${RED}✗ Failed (Invalid JSON response)${NC}"
        echo -e "Response: $response"
        return 1
    fi
}

# Main test execution
echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  SurgeonMatch API Endpoint Testing${NC}"
echo -e "${YELLOW}=======================================${NC}"
echo -e "Base URL: ${API_BASE_URL}"
echo -e "API Key: ${API_KEY:0:8}...${API_KEY:(-8)}"
echo -e "API Prefix: ${API_PREFIX}"

# Health Check Endpoints
test_endpoint "/health" "Root Health Check"
test_endpoint "${API_PREFIX}/health" "API Health Check"

# Surgeons Endpoints
test_endpoint "${API_PREFIX}/surgeons" "List all surgeons"

# Get the first surgeon's ID from the response
SURGEON_ID=$(curl -s -H "X-API-Key: $API_KEY" "${API_BASE_URL}${API_PREFIX}/surgeons" | jq -r '.[0].id')
if [ -n "$SURGEON_ID" ] && [ "$SURGEON_ID" != "null" ]; then
    echo -e "\n${YELLOW}Found surgeon ID: $SURGEON_ID${NC}"
    test_endpoint "${API_PREFIX}/surgeons/${SURGEON_ID}" "Get surgeon details"
    test_endpoint "${API_PREFIX}/surgeons/${SURGEON_ID}/claims" "Get surgeon claims"
    test_endpoint "${API_PREFIX}/surgeons/${SURGEON_ID}/quality-metrics" "Get surgeon quality metrics"
else
    echo -e "\n${RED}No surgeon ID found for further testing${NC}"
fi

# Claims Endpoints
test_endpoint "${API_PREFIX}/claims" "List all claims"

# Get the first claim's ID from the response
CLAIM_ID=$(curl -s -H "X-API-Key: $API_KEY" "${API_BASE_URL}${API_PREFIX}/claims" | jq -r '.[0].id')
if [ -n "$CLAIM_ID" ] && [ "$CLAIM_ID" != "null" ]; then
    echo -e "\n${YELLOW}Found claim ID: $CLAIM_ID${NC}"
    test_endpoint "${API_PREFIX}/claims/${CLAIM_ID}" "Get claim details"
else
    echo -e "\n${RED}No claim ID found for further testing${NC}"
fi

# Quality Metrics Endpoints
test_endpoint "${API_PREFIX}/quality-metrics" "List all quality metrics"

# Get the first quality metric's ID from the response
METRIC_ID=$(curl -s -H "X-API-Key: $API_KEY" "${API_BASE_URL}${API_PREFIX}/quality-metrics" | jq -r '.[0].id')
if [ -n "$METRIC_ID" ] && [ "$METRIC_ID" != "null" ]; then
    echo -e "\n${YELLOW}Found quality metric ID: $METRIC_ID${NC}"
    test_endpoint "${API_PREFIX}/quality-metrics/${METRIC_ID}" "Get quality metric details"
else
    echo -e "\n${RED}No quality metric ID found for further testing${NC}"
fi

echo -e "\n${YELLOW}=======================================${NC}"
echo -e "${GREEN}API Endpoint Testing Completed${NC}"
echo -e "${YELLOW}=======================================${NC}"
