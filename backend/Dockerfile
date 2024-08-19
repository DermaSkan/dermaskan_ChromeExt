# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN python -m venv venv
RUN . venv/bin/activate && pip install --upgrade pip && pip3 install -r requirements.txt

# Copy project
COPY . /code/

# Activate virtual environment and run the app
CMD . venv/bin/activate && exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
