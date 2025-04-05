# Cheatsheet Generator 🚀

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)](https://openai.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-orange)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered tool that generates customized educational content using OpenAI's GPT models. Create comprehensive cheatsheets, quizzes, flashcards, and practice problems tailored to your learning needs.

## ✨ Features

### 📚 Content Generation
- **Smart Cheatsheets**
  - Markdown formatting with syntax highlighting
  - Customizable sections and depth
  - Code examples with explanations
  - Visual diagrams and tables

- **Interactive Quizzes**
  - Multiple-choice questions with detailed explanations
  - Adjustable difficulty levels
  - Topic-specific question generation
  - Performance tracking

- **Study Flashcards**
  - Spaced repetition system
  - Customizable card formats
  - Progress tracking
  - Export to various formats

- **Practice Problems**
  - Step-by-step solutions
  - Difficulty progression
  - Topic-specific problems
  - Performance analytics

### 📊 Analytics & Debug
- **Token Usage Tracking**
  - Real-time monitoring
  - Cost analysis and optimization
  - Historical usage trends
  - Function-specific metrics

- **Vector Database Integration**
  - ChromaDB for efficient storage
  - Advanced querying capabilities
  - Persistent data across sessions
  - Thread-safe operations

## 🔄 Recent Updates

### Database Migration & Performance Improvements
- 🚀 Migrated from SQLite to ChromaDB for improved vector-based querying
- 🔒 Added thread-safe operations and automatic retry mechanisms
- 🔍 Implemented advanced filtering capabilities for analytics
- ⚡ Enhanced error handling and logging system

## 🛠️ Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/cheatsheet-generator.git
cd cheatsheet-generator
```

### 2. API Key Setup
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_api_key_here
```

### 3. Installation

#### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
cd src
gradio main.py
```

#### Docker Setup
```bash
# Build image
docker build -t cheatsheet-generator .

# Run container
docker run -p 7860:7860 --env-file .env cheatsheet-generator
```

The application will be available at `http://localhost:7860`



## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
