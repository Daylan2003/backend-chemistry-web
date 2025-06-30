from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os

# Replace with your real Gemini API key
GEMINI_API_KEY = " "

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GradeRequest(BaseModel):
    question: str
    students_answer: str
    prompt: str = None  # Optional

@app.post("/grade")
def grade_answer(data: GradeRequest):
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
        prompt = f"""
        You are a teacher grading a student's answer to a chemistry question.

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
    except Exception as e:
        return {"error": str(e)}

class AnswerRequest(BaseModel):
    answer: str

@app.post("/evaluate-answer")
async def evaluate_answer(req: AnswerRequest):
    student_answer = req.answer.strip().lower()
    # Simple check for keywords (customize as needed)
    correct = "mass" in student_answer and "space" in student_answer
    return {"correct": correct}
