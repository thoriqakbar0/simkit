
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from ship_llm import AI
from fastapi.responses import StreamingResponse
import os
from pydantic import BaseModel
from typing import Literal, List

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("API_KEY"))
ai = AI(client, "gpt-4o-mini")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def stuff():
    return "ello"

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class MessageHistory(BaseModel):
    messages: List[Message]

@ai.text(stream=True)
def test_ai(chat: MessageHistory):
    """
    You are a helpful assistant. refer to yourself as simkitty. where you help user making few simulation using simpy
    """
    return chat

@app.post("/ai")
def hello(chat: MessageHistory):
    response = test_ai(chat.messages)
    def generate_response(response):
        for chunk in response:
            yield chunk

    return StreamingResponse(
        generate_response(response),
        media_type="text/event-stream"
    )
