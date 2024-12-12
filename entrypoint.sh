#!/bin/bash

sleep 10

# Run database migrations
flask db init || true  # Skip if already initialized
flask db migrate
flask db upgrade

# Start the Flask application
exec python3 run.py

