# TDS Virtual Teaching Assistant

An AI-powered virtual teaching assistant for IIT Madras' Tools in Data Science course that automatically answers student questions based on course content and Discourse forum discussions.

## Features

- 🔍 **Discourse Scraping**: Automatically scrapes course forum posts
- 🧠 **AI-Powered Responses**: Uses OpenAI GPT models for intelligent answers
- 🔗 **Contextual Links**: Provides relevant Discourse links with answers
- 📊 **Vector Search**: Semantic search through course content and posts
- ⚡ **Fast API**: REST API with <30 second response times
- 🖼️ **Image Support**: Handles base64 encoded image attachments

## Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd tds-virtual-ta
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Scrape Discourse data
python src/scraper/discourse_scraper.py

# Start API server
python src/api/main.py
```

## API Usage

```bash
curl "http://localhost:8000/api/" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I use pandas for data analysis?"}'
```
