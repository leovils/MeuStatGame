import json
import pandas as pd
from datetime import datetime
import os

def generate_report():
    print("Iniciando geração de relatorio final e varredura no banco de dados...")

    db_path = 'local_db.json'
    questions_path = 'questions.json'

    if not os.path.exists(db_path):
        print(f"Erro: Arquivo '{db_path}' não encontrado. A sala está vazia.")
        return False

    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        print(f"Erro ao ler banco de dados: {e}")
        return False

    q_map = {}
    if os.path.exists(questions_path):
        try:
            with open(questions_path, 'r', encoding='utf-8') as f:
                questions_db = json.load(f)
                q_map = {q['id']: q['text'] for q in questions_db}
        except:
            pass

    students = db.get("students", {})
    responses = db.get("responses", [])

    student_responses = {}
    for r in responses:
        email = r.get("email")
        if not email:
            continue
        
        if email not in student_responses:
            student_responses[email] = []
        
        q_text = q_map.get(r['question_id'], f"Pergunta ID: {r['question_id']}")
        
        student_responses[email].append({
            "q_text": q_text,
            "answer": r["answer"],
            "is_correct": r["is_correct"],
            "score_awarded": r["score_awarded"]
        })

    report_data = []

    for email, info in students.items():
        name = info.get("name", "")
        course = info.get("course", "")
        nickname = info.get("nickname", "")
        total_score = info.get("score", 0)
        
        resps = student_responses.get(email, [])
        
        acertos = sum(1 for r in resps if r["is_correct"])
        erros = len(resps) - acertos
        
        detalhes = []
        for i, r in enumerate(resps, 1):
            status = "✔ ACERTOU" if r["is_correct"] else "❌ ERROU"
            detalhes.append(f"Q{i} [{status}]: '{r['answer']}' (+{r['score_awarded']} pts)")
            
        resumo_perguntas = "  ||  ".join(detalhes)
        
        report_data.append({
            "Nome": name,
            "E-mail": email,
            "Nickname": nickname,
            "Programa/Turma": course,
            "Nota Final (Pontos)": total_score,
            "Acertos": acertos,
            "Erros": erros,
            "Histórico de Respostas": resumo_perguntas
        })

    if not report_data:
        print("Nenhum dado real foi processado no relatorio (0 Alunos).")
        return None

    df = pd.DataFrame(report_data)
    df = df.sort_values(by="Nota Final (Pontos)", ascending=False)
    return df.to_csv(index=False, sep=";").encode('utf-8-sig')

if __name__ == "__main__":
    generate_report()
