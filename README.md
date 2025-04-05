# Cheatsheet Generator 🚀

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)](https://openai.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-orange)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered tool that generates customized educational content using OpenAI's GPT models. Create comprehensive cheatsheets, quizzes, flashcards, and practice problems tailored to your learning needs.

## 🔄 Recent Updates

### Architecture & Performance Improvements
- 🚀 Implemented thread-safe ChromaDB operations with connection pooling and exponential backoff
- 🔍 Enhanced date validation with ISO 8601 support and timezone-aware timestamps
- ⚡ Added custom exception hierarchy with retry mechanisms and comprehensive error logging
- 🔒 Implemented resource cleanup with proper thread-local storage management


## ✨ Features

### 📚 Content Generation
- **Smart Cheatsheets**: AI-powered content generation with customizable templates, complexity levels, and audience targeting
- **Interactive Quizzes**: Dynamic question generation with multiple formats, difficulty levels, and performance tracking
- **Study Flashcards**: Intelligent flashcard creation with spaced repetition and customizable card formats
- **Practice Problems**: Context-aware problem generation with difficulty progression and detailed solutions
- **Content Summarization**: Smart content summarization with adjustable focus and detail levels

### 📊 Analytics & Debug
- **Token Usage Tracking**: Real-time monitoring with advanced filtering and cost analysis
- **Performance Analytics**: Function-specific metrics and usage patterns
- **Vector Database**: Efficient storage with ChromaDB for advanced querying and analytics
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
