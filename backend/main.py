from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import random

app = FastAPI(
    title="Personalized Exam Simulator",
    description="Offline, adaptive Olympiad/mock exam generator and evaluator.",
    version="1.0.0"
)

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class ExamRequest(BaseModel):
    subject: str  # "physics", "chemistry", "biology", or "random"
    grade: str    # "11", "12", or "random"
    num_questions: int = 10
    difficulty: str = "random"  # "easy", "medium", "hard", or "random"
    topic: str = "random"       # "random" or user input
    language: str = "en"
    user_id: str

class AnswerSubmission(BaseModel):
    user_id: str
    exam_id: str
    answers: dict  # {question_id: answer}

class FeedbackRequest(BaseModel):
    user_id: str
    exam_id: str

# --- In-memory user state (for demo, replace with persistent storage for production) ---
user_progress = {}
exams = {}

# --- Helper functions ---

DB_CONFIG = [
    # (subject, grade, db_path, table_name)
    ("Biology", "11", "NCERT_Biology_11th/Biology_11th_Cleaned.sqlite", "Biology_11th_Cleaned"),
    ("Biology", "12", "NCERT_Biology_12th/Biology_12th_Cleaned.sqlite", "Biology_12th_Cleaned"),
    ("Chemistry", "11", "NCERT_Chemistry_11th/Chemsitry_11th_Cleaned.sqlite", "Chemsitry_11th_Cleaned"),
    ("Chemistry", "12", "NCERT_Chemistry_12th/Chemsitry_12th_Cleaned.sqlite", "Chemsitry_12th_Cleaned"),
    ("Physics", "11", "NCERT_Physics_11th/Physics_11th_Cleaned.sqlite", "Physics_11th_Cleaned"),
    ("Physics", "12", "NCERT_Physics_12th/Physics_12th_Cleaned.sqlite", "Physics_12th_Cleaned"),
]

def get_db_configs(subject, grade):
    # subject/grade can be "random"
    subjects = ["Biology", "Chemistry", "Physics"]
    grades = ["11", "12"]
    selected = []
    if subject == "random":
        subject_choices = [random.choice(subjects)]
    else:
        subject_choices = [subject.capitalize()]
    if grade == "random":
        grade_choices = [random.choice(grades)]
    else:
        grade_choices = [str(grade)]
    for s in subject_choices:
        for g in grade_choices:
            for conf in DB_CONFIG:
                if conf[0] == s and conf[1] == g:
                    selected.append(conf)
    return selected

def fetch_questions_with_filters(subject, grade, num_questions, difficulty="random", topic="random"):
    dbs = get_db_configs(subject, grade)
    all_questions = []
    for subj, grd, db_path, table in dbs:
        if not os.path.exists(db_path):
            continue
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        # Build query
        query = f"SELECT * FROM {table}"
        params = []
        where_clauses = []
        if topic != "random":
            where_clauses.append("Topic LIKE ?")
            params.append(f"%{topic}%")
        if difficulty != "random":
            where_clauses.append("Difficulty = ?")
            params.append(difficulty.capitalize())
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        for row in rows:
            q = dict(zip(columns, row))
            all_questions.append(q)
        conn.close()
    if not all_questions:
        raise HTTPException(status_code=404, detail="No questions found for the selected filters.")
    # If difficulty is random, pick random difficulties per question
    if difficulty == "random":
        # Shuffle and sample
        sampled = random.sample(all_questions, min(num_questions, len(all_questions)))
    else:
        sampled = random.sample(all_questions, min(num_questions, len(all_questions)))
    return sampled

# --- API Endpoints ---

@app.get("/subjects")
def list_subjects():
    # Hardcoded for now; could scan DBs
    return {
        "subjects": [
            {"subject": "Biology", "grades": ["11th", "12th"]},
            {"subject": "Chemistry", "grades": ["11th", "12th"]},
            {"subject": "Physics", "grades": ["11th", "12th"]},
        ]
    }

from datetime import datetime

@app.post("/generate_exam")
def generate_exam(req: ExamRequest):
    # subject: "physics", "chemistry", "biology", or "random"
    # grade: "11", "12", or "random"
    # topic: "random" or user input
    # difficulty: "easy", "medium", "hard", or "random"
    questions = fetch_questions_with_filters(
        req.subject,
        req.grade,
        req.num_questions,
        req.difficulty,
        req.topic
    )
    exam_id = f"{req.user_id}_{random.randint(10000,99999)}"
    test_obj = {
        "exam_id": exam_id,
        "user_id": req.user_id,
        "filters": {
            "subject": req.subject,
            "grade": req.grade,
            "topic": req.topic,
            "difficulty": req.difficulty,
            "num_questions": req.num_questions,
            "language": req.language
        },
        "questions": questions,
        "answers": {},
        "score": None,
        "status": "created",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    exams[exam_id] = test_obj
    user_progress.setdefault(req.user_id, []).append(exam_id)
    return test_obj

@app.post("/submit_answers")
def submit_answers(sub: AnswerSubmission):
    exam = exams.get(sub.exam_id)
    if not exam or exam["user_id"] != sub.user_id:
        raise HTTPException(status_code=404, detail="Exam not found for user.")
    exam["answers"] = sub.answers
    # Auto-evaluate (assume 'answer' column in DB)
    correct = 0
    total = len(exam["questions"])
    for q in exam["questions"]:
        qid = str(q.get("id") or q.get("question_id") or q.get("QID") or q.get("qid") or q.get("index") or "")
        user_ans = sub.answers.get(qid)
        correct_ans = str(q.get("answer") or q.get("Answer") or q.get("correct_answer") or "")
        if user_ans is not None and user_ans.strip().lower() == correct_ans.strip().lower():
            correct += 1
    score = correct / total if total else 0
    exam["score"] = score
    return {"score": score, "correct": correct, "total": total}

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    # Stub for Gemma-powered feedback
    exam = exams.get(req.exam_id)
    if not exam or exam["user_id"] != req.user_id:
        raise HTTPException(status_code=404, detail="Exam not found for user.")
    # Placeholder: In real app, use AI to generate feedback
    score = exam.get("score")
    if score is None:
        return {"feedback": "Please submit answers first."}
    if score == 1.0:
        fb = "Excellent! You got all questions correct."
    elif score >= 0.7:
        fb = "Good job! Review the questions you missed for improvement."
    elif score >= 0.4:
        fb = "Keep practicing. Focus on your weak areas."
    else:
        fb = "Don't give up! Try easier questions or review the material."
    return {"feedback": fb}

@app.get("/exam/{exam_id}")
def get_exam(exam_id: str):
    exam = exams.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")
    return exam

@app.get("/")
def root():
    return {"message": "Personalized Exam Simulator backend is running."}
