# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ src/

# Expose the port Gradio will run on
EXPOSE 7860

# Command to run the application
CMD ["gradio", "src/main.py"] 