# Cheatsheet Generator

An AI-powered tool that generates customized cheatsheets, quizzes, flashcards, and practice problems based on user inputs.

## Recent Updates

- **Token Usage Tracking**: Added persistent storage of token usage in SQLite database
- **Debug Logs**: Implemented detailed token usage monitoring and cost analysis
- **Database Integration**: Added SQLite support for storing generation history and outputs
- **Docker Support**: Added containerization for easy deployment
- **Enhanced Templates**: Added customizable templates for different content types

## Features

- **Content Generation**
  - Customizable cheatsheets with markdown formatting
  - Multiple-choice quizzes with explanations
  - Interactive flashcards for study
  - Practice problems with solutions
  - Smart content summarization

- **Debug & Analytics**
  - Real-time token usage tracking
  - Cost analysis and statistics
  - Persistent storage of generation history
  - Detailed usage logs

## Setup Instructions

### 1. API Key Setup

Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

### 2. Choose Your Setup Method

#### Option A: Local Setup

1. Install Requirements:
```bash
pip install -r requirements.txt
```

2. Start the Application:
```bash
# From the project root directory
python -m src.main
```

The application will start, and you can access it in your browser locally.

#### Option B: Docker Setup

1. Build the Docker Image:
```bash
docker build -t cheatsheet-generator .
```

2. Run the Container:
```bash
docker run -p 7860:7860 --env-file .env cheatsheet-generator
```

The application will be available at `http://localhost:7860`
