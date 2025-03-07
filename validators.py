from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question must be a non-empty string")
    session_id: str = Field(..., min_length=1, description="The unique ID must be a non-empty string")
    bot_token: str = Field(..., min_length=1, description="The admin ID must be a non-empty string")

class ChatResponse(BaseModel):
    answer: str
    questions:list
