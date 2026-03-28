import json
import os
from datetime import datetime
import pandas as pd

DB_FILE = 'local_db.json'

def init_db():
    if not os.path.exists(DB_FILE):
        db_state = {
            "students": {},  # email -> {name, course, nickname, score}
            "responses": [], # List of {email, question_id, answer, time_taken, score_awarded}
            "game_state": {
                "current_round": 1,
                "current_question": 0,    # 0 means not started/waiting
                "question_start_time": None,
                "is_active": False,
                "show_answer": False
            }
        }
        _save_db(db_state)

def _load_db():
    init_db()
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def register_student(name, course, email, nickname):
    db = _load_db()
    
    # Simple validation for unique nickname
    for student_val in db["students"].values():
        if student_val["nickname"].lower() == nickname.lower() and student_val["email"] != email:
            return False, "Nickname já está em uso!"
            
    db["students"][email] = {
        "name": name,
        "course": course,
        "email": email,
        "nickname": nickname,
        "score": 0,
        "registered_at": datetime.now().isoformat()
    }
    _save_db(db)
    return True, "Registrado com sucesso!"

def get_student(email):
    db = _load_db()
    return db["students"].get(email)

def get_leaderboard():
    db = _load_db()
    students = list(db["students"].values())
    if not students:
        return pd.DataFrame(columns=["Nickname", "Nome", "E-mail", "Programa", "Pontuação"])
    
    df = pd.DataFrame(students)
    df = df[["nickname", "name", "email", "course", "score"]].rename(columns={
        "nickname": "Nickname", 
        "name": "Nome", 
        "email": "E-mail", 
        "course": "Programa", 
        "score": "Pontuação"
    })
    df = df.sort_values(by="Pontuação", ascending=False).reset_index(drop=True)
    df.index += 1
    return df

def get_game_state():
    db = _load_db()
    return db["game_state"]

def update_game_state(state_update):
    db = _load_db()
    db["game_state"].update(state_update)
    _save_db(db)

def save_response(email, question_id, answer, time_taken, is_correct, score_awarded):
    db = _load_db()
    
    # Check if already answered
    for resp in db["responses"]:
        if resp["email"] == email and resp["question_id"] == question_id:
            return False
            
    db["responses"].append({
        "email": email,
        "question_id": question_id,
        "answer": answer,
        "time_taken": time_taken,
        "is_correct": is_correct,
        "score_awarded": score_awarded,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update score
    if email in db["students"]:
        db["students"][email]["score"] += score_awarded
        
    _save_db(db)
    return True

def reset_room():
    db = _load_db()
    db["students"] = {}
    db["responses"] = []
    db["game_state"] = {
        "current_round": 1,
        "current_question": 0,
        "question_start_time": None,
        "is_active": False,
        "show_answer": False
    }
    _save_db(db)

# TODO: Integrar com gspread para sincronizar `db` com uma planilha no Google Sheets real.
