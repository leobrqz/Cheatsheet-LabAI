# Cheatsheet Generator

This project is a Gradio-based application that generates customized cheatsheets based on user inputs.

## Setup Instructions

### 1. API Key Setup

Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

#### Local Setup

1. Install Requirements:
```bash
pip install -r requirements.txt
```

2. Start the Application:
```bash
gradio main.py
```

The application will be available at `http://localhost:7860`

#### Docker Setup

1. Build the Docker Image:
```bash
docker build -t cheatsheet-generator .
```

2. Run the Container:
```bash
docker run -p 7860:7860 --env-file .env cheatsheet-generator
```

The application will be available at `http://localhost:7860`
