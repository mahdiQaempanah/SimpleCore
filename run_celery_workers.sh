#!/bin/bash

# Django settings module
export DJANGO_SETTINGS_MODULE="SimpleCore.settings"

# Activate your virtual environment if necessary
# source /path/to/your/virtualenv/bin/activate

# Get all market IDs from the Market model in Django
MARKET_IDS=$(python -c "import os; from django import setup; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SimpleCore.settings'); setup(); from core.models import Market; print(' '.join(map(str, Market.objects.values_list('id', flat=True))))")

# Check if we retrieved any market IDs
if [ -z "$MARKET_IDS" ]; then
  echo "No markets found in the database."
  exit 1
fi

# Initialize an empty array to track process IDs
PIDS=()

# Run a separate Celery worker for each market_id
for market_id in $MARKET_IDS; do
  echo "Starting Celery worker for market_$market_id"

  # Run Celery worker for this market_id
  celery -A SimpleCore worker --queues=market_$market_id &

  # Track the background process ID
  CELERY_PID=$!

  # Add the process ID to the array
  PIDS+=($CELERY_PID)
done

# Gracefully handle Ctrl+C (SIGINT) and stop all background workers
trap 'echo "Stopping Celery workers..."; for pid in "${PIDS[@]}"; do kill $pid; done; exit 0' SIGINT

# Wait for all workers to finish (this will block the script until workers are stopped)
wait
