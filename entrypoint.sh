#!/bin/bash

sleep 10

# Run database migrations
flask db init || true  # Skip if already initialized
sleep 10
flask db migrate
sleep 10
flask db upgrade
sleep 10

# Start the Flask application
exec python3 run.py

