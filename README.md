# Mongodb MCP Agent with FastAPI Backend


A FastAPI backend that connects LangGraph, MongoDB (via MCP), and OpenAI/LLM models to provide a chat interface for managing and summarizing todos.

## Features
- FastAPI server with a `/chat` endpoint
- Integrates with MongoDB via MCP (MultiServerMCPClient)
- Uses OpenAI GPT-4o via LangGraph
- Summarizes and manages todos in the `chatapp2` database, `todos` collection

## Requirements
- Python 3.8+
- Node.js (for `mongodb-mcp-server` via npx)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd ChatAppBackend
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables
Create a `.env` file in the project root (this file is gitignored) and add:

```
GOOGLE_API_KEY=your_google_api_key_here
MONGODB_URI=mongodb://localhost:27017/?directConnection=true
```

- `OPENAI_API_KEY`: Your OpenAI API key 
- `MONGODB_URI`: MongoDB connection string (default is local)

## Running the Server

```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000` by default.

## Usage Example
Send a chat message using `curl`:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me all todos"}'
```

## Project Structure
- `main.py` — FastAPI app and chat logic
- `requirements.txt` — Python dependencies
- `.gitignore` — Files and folders ignored by git
- `.env` — Your environment variables (not tracked by git)

## License
MIT 
