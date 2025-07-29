import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.worksheet_generator.crew import get_worksheet_crew

app = FastAPI(
    title="Worksheet Generator API",
    description="An API to generate educational worksheets using AI agents.",
    version="1.0.0"
)

class WorksheetRequest(BaseModel):
    topic: str
    grade: str
    num_questions: int = 10

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the Worksheet Generator API!"}


@app.post("/generate-worksheet/")
def generate_worksheet(request: WorksheetRequest):
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set."
        )

    try:
        inputs = {
            'topic': request.topic,
            'grade': request.grade,
            'num_questions': request.num_questions
        }
        result = get_worksheet_crew.kickoff(inputs)
        return {"worksheet": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))