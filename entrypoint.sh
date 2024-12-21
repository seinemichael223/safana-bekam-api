#!/bin/bash

sleep 10

# Run database migrations
flask db init || true  # Skip if already initialized
sleep 20
flask db migrate
sleep 20
flask db upgrade
sleep 20

# Start the Flask application
exec python3 run.py

