import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")  # Free model

def generate_question(role: str, difficulty: str) -> str:
    prompt = f"""
    Generate ONE interview question for a {difficulty} level {role} position.
    Make it a realistic question a real interviewer would ask.
    Return ONLY the question, nothing else.
    """
    print("Generating question...")
    print("Role:", role)
    print("Difficulty:", difficulty)
    print("Model:", model)
    response = model.generate_content(prompt)
    return response.text.strip()

def evaluate_answer(question: str, answer: str, role: str) -> dict:
    prompt = f"""
    You are an expert interviewer for a {role} position.
    
    Question asked: {question}
    Candidate's answer: {answer}
    
    Evaluate this answer and respond in this EXACT format:
    SCORE: [number from 0 to 100]
    FEEDBACK: [2-3 sentences of constructive feedback]
    STRENGTHS: [one sentence on what was good]
    IMPROVEMENTS: [one sentence on what to improve]
    """
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Parse the response
    lines = text.split("\n")
    result = {"score": 50, "feedback": "", "strengths": "", "improvements": ""}
    for line in lines:
        if line.startswith("SCORE:"):
            try:
                result["score"] = int(line.replace("SCORE:", "").strip())
            except:
                result["score"] = 50
        elif line.startswith("FEEDBACK:"):
            result["feedback"] = line.replace("FEEDBACK:", "").strip()
        elif line.startswith("STRENGTHS:"):
            result["strengths"] = line.replace("STRENGTHS:", "").strip()
        elif line.startswith("IMPROVEMENTS:"):
            result["improvements"] = line.replace("IMPROVEMENTS:", "").strip()
    return result