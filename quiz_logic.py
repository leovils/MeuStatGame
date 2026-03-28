import json
import random
import os

QUESTIONS_FILE = 'questions.json'

def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_question_by_id(q_id):
    qs = load_questions()
    for q in qs:
        if q["id"] == q_id:
            return q
    return None

def generate_round(round_number, num_questions=10):
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            qs = json.load(f)
    except Exception as e:
        print(f"\n================ ERROR JSON ================")
        print(f"O seu arquivo questions.json contém um erro de formatação (syntax).")
        print(f"Verifique se não esqueceu de fechar Chaves ou Aspas. O sistema o considerou ilegível e pulou a rodada.")
        print(f"Motivo exato: {e}")
        print("============================================\n")
        qs = []
    
    if not qs:
        return []
    
    # In a real app, difficulty would scale with the round number.
    # Using random sampling for now. If fewer questions available, just duplicate.
    if len(qs) < num_questions:
        return random.choices(qs, k=num_questions)
    else:
        return random.sample(qs, num_questions)

def calculate_score(time_taken, max_time=30, base_score=100, is_correct=True):
    if not is_correct:
        return 0
    
    # 10% speed bonus if answered instantly, decays to 0% at max_time
    if time_taken <= 0:
        time_taken = 0.1
    if time_taken >= max_time:
        return base_score
    
    bonus_percentage = ((max_time - time_taken) / max_time) * 0.10
    total_score = base_score * (1 + bonus_percentage)
    return int(round(total_score))
