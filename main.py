from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models, auth, ai_service
from database import engine, get_db

# This creates all the database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─── Page Routes (return HTML pages) ───────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="dashboard.html"
)

@app.get("/interview", response_class=HTMLResponse)
def interview_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="interview.html"
)

# ─── Auth Routes ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        name=data.name,
        email=data.email,
        hashed_password=auth.hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_access_token({"sub": user.email})
    return {"token": token, "name": user.name}

@app.post("/api/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.create_access_token({"sub": user.email})
    return {"token": token, "name": user.name}

# ─── Interview Routes ────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    role: str
    difficulty: str

class AnswerRequest(BaseModel):
    session_id: int
    answer: str

@app.post("/api/get-question")
def get_question(
    data: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    question = ai_service.generate_question(data.role, data.difficulty)
    session = models.InterviewSession(
        user_id=current_user.id,
        role=data.role,
        difficulty=data.difficulty,
        question=question
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "question": question}

@app.post("/api/submit-answer")
def submit_answer(
    data: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id == data.session_id,
        models.InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = ai_service.evaluate_answer(session.question, data.answer, session.role)
    session.user_answer = data.answer
    session.ai_feedback = result["feedback"]
    session.score = result["score"]
    db.commit()
    return result

@app.get("/api/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    sessions = db.query(models.InterviewSession).filter(
        models.InterviewSession.user_id == current_user.id
    ).order_by(models.InterviewSession.created_at.desc()).limit(10).all()
    
    return [
        {
            "role": s.role,
            "difficulty": s.difficulty,
            "question": s.question,
            "score": s.score,
            "feedback": s.ai_feedback,
            "date": str(s.created_at)
        }
        for s in sessions
    ]