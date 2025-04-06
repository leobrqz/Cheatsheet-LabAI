# Cheatsheet Generator 🚀

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)](https://openai.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-orange)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered tool that generates customized educational content using OpenAI's GPT models. Create comprehensive cheatsheets, quizzes, flashcards, and practice problems tailored to your learning needs.

## 🔄 Recent Updates

### Architecture & Performance Improvements
- 🚀 Enhanced ChromaDB integration with thread-safe operations, connection pooling, and robust error handling
- 🔍 Advanced token usage tracking with caching, filtering, and analytics capabilities
- ⚡ Implemented rate limiting and exponential backoff for API calls
- 🔒 Added comprehensive error handling with custom exception hierarchy
- 📊 Improved template management system with CRUD operations and validation

## ✨ Features

### 📚 Content Generation
- **Smart Cheatsheets**: AI-powered content generation with customizable templates, complexity levels, and audience targeting
- **Interactive Quizzes**: Dynamic question generation with multiple formats and difficulty levels
- **Study Flashcards**: Intelligent flashcard creation with customizable formats
- **Practice Problems**: Context-aware problem generation with detailed solutions
- **Content Summarization**: Smart content summarization with adjustable focus levels

### 🛠️ Template Management
- **Custom Templates**: Create, edit, and manage custom content templates
- **Template Categories**: Organize templates by type (study, coding, reference)
- **Template Validation**: Built-in validation for template structure and content
- **Default Templates**: Pre-configured templates for common use cases

### 📊 Analytics & Monitoring
- **Token Usage Tracking**: Real-time monitoring with advanced filtering and caching
- **Performance Analytics**: Function-specific metrics and usage patterns
- **Cost Analysis**: Detailed cost tracking and reporting by function and date
- **Query Builder**: Flexible query system for advanced analytics

### 🔒 System Architecture
- **Thread-Safe Operations**: Robust concurrency handling with proper locking mechanisms
- **Error Recovery**: Automatic retry mechanisms with exponential backoff
- **Resource Management**: Proper cleanup and resource handling
- **Caching System**: Efficient caching with TTL for improved performance

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
