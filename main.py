# main.py
"""
FastAPI ➜ LangGraph ➜ MongoDB MCP (stdio) with **Gemini-2.0-Flash**

Install
-------
pip install fastapi uvicorn langgraph langchain-mcp-adapters \
            langchain-google-genai google-generativeai  # Gemini wrapper

Environment
-----------
export GOOGLE_API_KEY=...
export MONGODB_URI="mongodb://localhost:27017/?directConnection=true"

Run
---
uvicorn main:app --reload
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import logging
from fastapi.responses import PlainTextResponse
import re
from fastapi.middleware.cors import CORSMiddleware

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI  # Use OpenAI GPT-4o

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
agent = None
mcp_client = None

load_dotenv()

logging.basicConfig(level=logging.INFO)

DEFAULT_DB_INSTRUCTION = (
    "Always respond ONLY with a human readable summary of the todos. "
    "The MongoDB database is 'chatapp2'. "
    "The collection for todos is 'todos'. "
    "You have access to MongoDB tools via MCP and may use them, including for chain-of-thought (COT) calls if needed. "
    "Never reveal that you are a MongoDB agent or mention MongoDB, MCP, or database internals to the user. Always act as a helpful assistant. "
    "When you receive a request about todos, first sample a few documents from the 'todos' collection to understand the schema and possible field values. "
    "Then, use that information to construct and run the correct query to answer the user's request. "
    "Finally, summarize the results in a human readable way. "
)

class ChatRequest(BaseModel):
    prompt: str


@app.on_event("startup")
async def startup() -> None:
    global agent, mcp_client

    # 1️⃣  start MongoDB MCP server locally over stdio
    mcp_client = MultiServerMCPClient(
        {
            "mongodb": {
                "command": "npx",
                "args": [
                    "-y",
                    "mongodb-mcp-server",
                    "--connectionString",
                    os.environ.get("MONGODB_URI"),
                ],
                "transport": "stdio",
            }
        }
    )

    tools = await mcp_client.get_tools()

    # 2️⃣  GPT-4o LLM (OpenAI)
    llm = ChatOpenAI(
        model="gpt-4.1",
        temperature=0.0,
        streaming=True,
    )

    # 3️⃣  build ReAct agent
    agent = create_react_agent(model=llm, tools=tools)


@app.on_event("shutdown")
async def shutdown() -> None:
    if mcp_client:
        await mcp_client.aclose()


@app.post("/chat", response_class=PlainTextResponse)
async def chat(req: ChatRequest):
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")
    prompt = (
        DEFAULT_DB_INSTRUCTION +
        " Always respond ONLY with a human readable summary of the todos in the chatapp database, with no extra commentary, no JSON, and no code formatting. Do not use markdown or code fences. "
        + req.prompt
    )
    msg = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    # If the agent returns a dict with 'messages', extract the last message's 'content'
    if isinstance(msg, dict) and "messages" in msg and isinstance(msg["messages"], list):
        last_message = msg["messages"][-1]
        if hasattr(last_message, "content"):
            response_content = last_message.content
        elif isinstance(last_message, dict):
            response_content = last_message.get("content", "")
        else:
            response_content = str(last_message)
    else:
        response_content = getattr(msg, "content", msg)
    # Remove markdown code fences and JSON blocks
    response_content = re.sub(r"```[a-zA-Z]*\\n.*?```", "", response_content, flags=re.DOTALL)
    response_content = re.sub(r"```.*?```", "", response_content, flags=re.DOTALL)
    # If the response still looks like JSON, return a fallback message
    if response_content.strip().startswith("{") and response_content.strip().endswith("}"):
        return "Sorry, I could not generate a summary."
    return response_content.strip()
