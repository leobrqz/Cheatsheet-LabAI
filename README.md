# Cheatsheet AI Lab 🚀

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)](https://openai.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-orange)](https://www.trychroma.com/)
[![LangChain](https://img.shields.io/badge/LangChain-LLM%20Framework-purple)](https://python.langchain.com/)
[![Gradio](https://img.shields.io/badge/Gradio-UI%20Framework-red)](https://gradio.app/)


An AI-powered educational content generator leveraging OpenAI's GPT models and ChromaDB for vector storage. Features include dynamic cheatsheet generation, interactive learning tools, and token usage analytics. Built with thread-safe operations and robust error handling.



## Recent Updates

### Architecture & Performance Improvements
- Enhanced ChromaDB with thread-safe operations and error handling with backoff
- Token usage tracking with filtering and analytics
- Error handling with exponential backoff for API calls
- Error handling and logging system
- Template management with CRUD operations

## ✨ Features

### 📚 Content Generation
- **Smart Cheatsheets**: AI-powered content generation with customizable templates
- **Interactive Quizzes**: Dynamic question generation with multiple formats
- **Study Flashcards**: Flashcard creation with customizable formats
- **Practice Problems**: Problem generation with detailed solutions
- **Content Summarization**: Smart content summarization with adjustable focus

### 🛠️ Template Management
- **Custom Templates**: Create, edit, and manage custom content templates
- **Template Types**: Template categorization (Default/Custom)
- **Default Templates**: Pre-configured templates for common use cases

### 📊 Analytics & Monitoring
- **Token Usage Tracking**: Usage monitoring with filtering capabilities
- **Cost Analysis**: Detailed cost tracking and reporting
- **Query Builder**: Flexible query system for token usage analysis

### 🔒 System Architecture
- **Thread-Safe Operations**: Concurrency handling with locks
- **Error Handling**: Error recovery with logging
- **Resource Management**: Proper cleanup and resource handling

## 🛠️ Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/leobrqz/Cheatsheet-LabAI
cd Cheatsheet-LabAI
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
docker build -t Cheatsheet-LabAI .

# Run container
docker run -p 7860:7860 --env-file .env Cheatsheet-LabAI
```

The application will be available at `http://localhost:7860`



