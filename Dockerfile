# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Expose the port Gradio will run on
EXPOSE 7860

# Command to run the application
CMD ["gradio", "src/main.py"] 