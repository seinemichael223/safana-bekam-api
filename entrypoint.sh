#!/bin/bash

sleep 6

# Run database migrations
flask db init || true  # Skip if already initialized
sleep 1
flask db migrate
sleep 1
flask db upgrade

# Start the Flask application
exec python3 run.py

