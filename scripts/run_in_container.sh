#!/bin/bash
# Run the script in the Docker container without requiring a TTY
docker exec surgeon-match-api-1 python /app/scripts/create_test_api_key.py
