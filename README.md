# Cheatsheet Generator

An AI-powered tool that generates customized cheatsheets, quizzes, flashcards, and practice problems based on user inputs.

## Recent Updates

- **Token Usage Tracking**: Added persistent storage of token usage in SQLite database with historical data preservation
- **Debug Logs**: Implemented detailed token usage monitoring and cost analysis with real-time statistics
- **Database Integration**: Added SQLite support for storing generation history and outputs with automatic directory creation
- **Docker Support**: Added containerization for easy deployment with optimized image size and environment configuration
- **Enhanced Templates**: Added customizable templates for different content types with markdown formatting support

## Features

- **Content Generation**
  - Customizable cheatsheets with markdown formatting and syntax highlighting
  - Multiple-choice quizzes with explanations and difficulty levels
  - Interactive flashcards for study with spaced repetition support
  - Practice problems with solutions and step-by-step explanations
  - Smart content summarization with customizable focus areas

- **Debug & Analytics**
  - Real-time token usage tracking with persistent storage
  - Cost analysis and statistics with historical trends
  - Persistent storage of generation history across sessions
  - Detailed usage logs with function-specific metrics
  - SQLite database for reliable data persistence

## Setup Instructions

### 1. API Key Setup

Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

### Setup Method

#### Local Setup

1. Install Requirements:
```bash
pip install -r requirements.txt
```

2. Start the Application:
```bash
# From the project root directory
gradio -m src.main
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
