from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")  # add this to your .env

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in environment (.env).")
if not INTERNAL_API_KEY:
    raise RuntimeError("Missing INTERNAL_API_KEY in environment (.env).")

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# CORS: for development. In production, restrict to your real frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g. ["https://your-frontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """
    Requires clients to send: X-API-Key: <secret>
    """
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/health")
def health():
    return {"status": "ok"}

class GradeRequest(BaseModel):
    question: str
    students_answer: str
    prompt: Optional[str] = None

@app.post("/grade")
def grade_answer(data: GradeRequest, _: None = Depends(verify_api_key)):
    if data.prompt:
        prompt = f"""{data.prompt}

Question: {data.question}
Student's Answer: {data.students_answer}

Instructions:
- Give one paragraph of feedback explaining what was right or wrong.
- Be clear and kind.

Return only the feedback paragraph.
"""
    else:
        prompt = f"""You are a teacher grading a student's answer to a chemistry question.

Question: {data.question}
Student's Answer: {data.students_answer}

Instructions:
- Give one paragraph of feedback explaining what was right or wrong.
- Be clear and kind.

Return only the feedback paragraph.
"""

    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        response = model.generate_content(prompt)
        return {"result": response.text}
    except Exception:
        # Don't leak internal exception details to clients
        raise HTTPException(status_code=502, detail="Upstream model request failed")

class AnswerRequest(BaseModel):
    answer: str

@app.post("/evaluate-answer")
async def evaluate_answer(req: AnswerRequest, _: None = Depends(verify_api_key)):
    student_answer = req.answer.strip().lower()
    correct = "mass" in student_answer and "space" in student_answer
    return {"correct": correct}

class ChemistryQuestionRequest(BaseModel):
    question: str

@app.post("/answer-chemistry")
async def answer_chemistry_question(
    req: ChemistryQuestionRequest,
    _: None = Depends(verify_api_key),
):
    prompt = f"""You are a chemistry expert. Answer the following chemistry question with detailed explanations, formulas, and proper chemical terminology.

Question: {req.question}

Instructions:
- Provide a comprehensive chemistry answer
- Include relevant chemical concepts and formulas
- Use proper chemical notation and terminology
- Give step-by-step explanations when appropriate
- Focus purely on the chemistry content
- Do not engage in conversation or acknowledge the question format

Return only the chemistry answer."""

    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        response = model.generate_content(prompt)
        return {"answer": response.text}
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream model request failed")
