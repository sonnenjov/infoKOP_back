#!/bin/bash

echo "Building for Render..."

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations (optional - can also be done as pre-deploy command)
# python manage.py migrate

echo "Build completed!"