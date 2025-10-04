# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start the Streamlit web application
streamlit run app.py
```

### Testing Core Functions
```bash
# Use the Jupyter notebook for testing core functionality
jupyter notebook test_core.ipynb
```

### Environment Setup
```bash
# Install dependencies (no requirements.txt exists, install manually)
pip install streamlit openai beautifulsoup4 trafilatura pandas python-dotenv

# Ensure .env file exists with OPENAI_API_KEY
# The application requires OpenAI API access for content analysis
```

## Architecture Overview

This is a **Link Learning Application** that processes web articles and generates flashcards for learning.

### Core Data Flow
1. **Link Processing**: User submits URL → `app.py` calls `process_new_link()` → `core.py` scrapes and analyzes content
2. **AI Analysis**: Content sent to OpenAI API for categorization, tagging, and TLDR generation
3. **Storage**: Results stored in CSV files (`data/links_store.csv`, `data/cards_store.csv`)
4. **Flashcard System**: Generated cards reviewed through spaced repetition interface

### Key Components

**Frontend (`app.py`)**
- Streamlit-based web interface with two main pages: "Add Links" and "Review Cards"
- Session state management for flashcard queue logic (`main_q`, `again_q`, `round_idx`)
- Direct imports from `core.py` for backend functionality

**Backend (`core.py`)**
- Web scraping using BeautifulSoup and Trafilatura
- OpenAI integration with fallback strategies (web tool → local content analysis)
- CSV-based data persistence with pandas DataFrames
- Flashcard generation and spaced repetition logic

**Data Layer**
- `data/links_store.csv`: Processed articles with metadata (title, categories, tags, TLDR, full content)
- `data/cards_store.csv`: Generated flashcards with learning status tracking
- `data/taxonomy.json`: Predefined categories and tags for content classification

### OpenAI Integration Pattern
The application uses a dual-mode approach:
1. **Primary**: `MODEL_WITH_WEB` with web search tool for direct URL analysis
2. **Fallback**: `MODEL_FALLBACK` with locally scraped content if web tool fails
3. **Card Generation**: `MODEL_FOR_CARDS` for generating flashcards from processed content

### Critical Architecture Notes
- **No Database**: Uses CSV files for all data persistence - potential concurrency issues
- **Synchronous Processing**: UI blocks during link processing (no background jobs)
- **Direct Function Coupling**: Streamlit app directly imports and calls core functions
- **Memory-based Operations**: All CSV data loaded into memory for each operation

### Taxonomy System
Content is categorized using:
- **Categories**: AI/ML, Product, Startups, Career, Health, Finance (max 3 per article)
- **Tags**: Rich tagging system with 25+ predefined tags (max 12 per article)
- **Dynamic Updates**: Taxonomy expands when new categories/tags are discovered

### Environment Configuration
Key environment variables in `.env`:
- `OPENAI_API_KEY`: Required for all AI operations
- `MODEL_WITH_WEB`, `MODEL_FALLBACK`, `MODEL_FOR_CARDS`: Configurable OpenAI models
- `MAX_TEXT_CHARS`: Content truncation limit (default: 8000)

### File Structure Context
- Root level contains main application files and CSV data
- `data/` directory mirrors root CSV files (appears to be backup/versioned copies)
- No formal database migrations or schema management
- Configuration hardcoded in `core.py` constants

## Development Patterns

When modifying this codebase:
- CSV operations should be atomic to prevent data corruption
- Test changes using `test_core.ipynb` before modifying the main application
- Be mindful of OpenAI API rate limits and costs
- Consider memory usage when loading large CSV files
- Maintain backward compatibility with existing CSV schema
- testing
- don't run the streamlit run, I will run it on my terminal