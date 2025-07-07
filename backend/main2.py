from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, List, Dict, Any
import sqlite3
import os
import random
from datetime import datetime
from backend.mcq_generator import generate_mcqs_for_exam

app = FastAPI(
    title="Personalized Exam Simulator (Multi-Subject)",
    description="Offline, adaptive Olympiad/mock exam generator and evaluator with multi-subject support.",
    version="2.0.0"
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

# TopicRequest removed
class SubjectSelection(BaseModel):
    subject: str  # "physics", "chemistry", "biology"
    grade: str    # "11", "12", or "random"
    difficulty: Literal["easy", "medium", "hard"] = "easy"  # Only allow these values

class ExamRequest(BaseModel):
    subjects: list[SubjectSelection]  # List of selected subjects with their options
    language: str = "en"
    user_id: str

class AnswerSubmission(BaseModel):
    user_id: str
    exam_id: str
    answers: dict  # {question_id: answer}

class FeedbackRequest(BaseModel):
    user_id: str
    exam_id: str

class MCQQuestionsRequest(BaseModel):
    questions: List[Dict[str, Any]]

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

def fetch_questions_with_filters(subject, grade, difficulty="easy"):
    dbs = get_db_configs(subject, grade)
    all_questions = []
    for subj, grd, db_path, table in dbs:
        if not os.path.exists(db_path):
            continue
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        # Build query without topic filter
        query = f"SELECT * FROM {table}"
        params = []
        where_clauses = []
        if difficulty:
            where_clauses.append("Difficulty = ?")
            params.append(difficulty.capitalize())
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        for row in rows:
            q = dict(zip(columns, row))
            q["subject"] = subj  # Tag question with subject
            q["grade"] = grd
            all_questions.append(q)
        # DEBUG: Log how many questions were found for this filter
        with open("exam_debug.log", "a", encoding="utf-8") as f:
            f.write(f"DB: {db_path}, Table: {table}, Subject: {subj}, Grade: {grd}, Difficulty: {difficulty}, Found: {len(rows)}\n")
        conn.close()
    if not all_questions:
        raise HTTPException(status_code=404, detail=f"No questions found for {subject} {grade} with the selected filters.")
    # Return all matching questions (no sampling)
    return all_questions

# --- API Endpoints ---

# /get_topics endpoint removed
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

@app.post("/generate_exam")
def generate_exam(req: ExamRequest):
    # req.subjects: list of SubjectSelection
    all_questions = []
    filters = []
    for subj_sel in req.subjects:
        # If grade is "random", pick a random grade and use it for this subject
        grade = subj_sel.grade
        if grade == "random":
            grade = random.choice(["11", "12"])
        # Ignore topic, just fetch by subject, grade, difficulty
        questions = fetch_questions_with_filters(
            subj_sel.subject,
            grade,
            subj_sel.difficulty
        )
        # Limit to 5 questions per subject if more are available
        if len(questions) > 5:
            questions = random.sample(questions, 5)
        all_questions.extend(questions)
        filters.append({
            "subject": subj_sel.subject,
            "grade": grade,
            "difficulty": subj_sel.difficulty
        })
    if not all_questions:
        raise HTTPException(status_code=404, detail="No questions found for the selected filters.")

    exam_id = f"{req.user_id}_{random.randint(10000,99999)}"
    # DEBUG: Log the number and subjects of questions being returned
    with open("exam_debug.log", "a", encoding="utf-8") as f:
        f.write(f"Exam ID: {req.user_id}_{exam_id}\n")
        f.write(f"Requested subjects: {filters}\n")
        f.write(f"Number of questions returned: {len(all_questions)}\n")
        f.write(f"Subjects: {[q.get('subject') for q in all_questions]}\n")
        f.write("="*40 + "\n")

    test_obj = {
        "exam_id": exam_id,
        "user_id": req.user_id,
        "filters": filters,
        "questions": all_questions,
        "answers": {},
        "score": None,
        "status": "created",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    exams[exam_id] = test_obj
    user_progress.setdefault(req.user_id, []).append(exam_id)
    return test_obj

@app.post("/generate_mcqs")
def generate_mcqs(req: MCQQuestionsRequest):
    # Wrap in exam-like dict for compatibility with mcq_generator
    exam = {"questions": req.questions}
    mcq_results = generate_mcqs_for_exam(exam)
    return {"mcqs": mcq_results}

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
    return {"message": "Personalized Exam Simulator backend (multi-subject) is running."}
