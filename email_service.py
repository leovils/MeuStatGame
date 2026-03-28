import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
from config import get_secret

def send_summary_email(to_email, student_name, score, rank, total_students, detailed_text, acertos, total_q):
    try:
        sender_email = get_secret("smtp_email")
        sender_password = get_secret("smtp_password")
        
        if not sender_email or not sender_password:
            import streamlit as st
            st.error("❌ ATENÇÃO: As credenciais 'smtp_email' e 'smtp_password' sumiram ou não estão configuradas corretamente nos secrets da Nuvem!")
            return False
            
        subject = f"📊 Seu Relatório Detalhado no Quiz de Estatística!"
        
        body = f"""Olá {student_name}. Aqui está um relatório da sua participação recente no nosso Quiz Estatístico!

Sua Posição no Ranking da Turma: {rank}º lugar (de {total_students} participantes)
Pontuação Final (com bônus de velocidade): {score} pontos

==================================================
RELATÓRIO EXPLÍCITO DE RESPOSTAS
==================================================
{detailed_text}
==================================================

RESULTADO FINAL: Você obteve {acertos} acertos de um total de {total_q} perguntas.
Mantenha o ótimo trabalho e continue praticando as revisões!

Atenciosamente,
Prof. Leo Vils
"""
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        
        import streamlit as st
        st.toast(f"✅ O servidor do Gmail CONFIRMOU o pacote despachado para: {to_email}!")
        return True
    except Exception as e:
        import streamlit as st
        # Mostrar o erro brutal na tela para nós podermos debugar sem caçar os logs
        st.error(f"Erro no EMAIL: {str(e)}")
        print(f"================ ERROR EMAIL ================")
        print(f"Erro ao tentar enviar e-mail para {to_email}.")
        print(f"Motivo: {e}")
        print("============================================")
        return False
        
def broadcast_emails(leaderboard_df, full_db, questions_list):
    total_students = len(leaderboard_df)
    success_count = 0
    
    students_db = full_db.get("students", {})
    responses = full_db.get("responses", [])
    
    q_map = {q["id"]: {"text": q["text"], "correct": q["answer"]} for q in questions_list}
    
    print(f"\n[E-mail] Tentando enviar {total_students} e-mails detalhados...")
    
    for index, row in leaderboard_df.iterrows():
        # df.index from database is 1-based, so rank is precisely index!
        rank = index 
        nickname = row["Nickname"]
        score = row["Pontuação"]
        
        email = None
        name = "Aluno"
        for db_email, info in students_db.items():
            if info["nickname"] == nickname:
                email = db_email
                name = info["name"]
                break
                
        if email:
            acertos = 0
            detailed_text = ""
            student_responses = [r for r in responses if r.get("email") == email]
            total_q = len(student_responses)
            
            for i, r in enumerate(student_responses, 1):
                q_id = r.get("question_id")
                q_info = q_map.get(q_id, {"text": "Pergunta expirada/desconhecida", "correct": "???"})
                
                is_correct = r.get("is_correct", False)
                if is_correct:
                    acertos += 1
                    status = "✅ ACERTOU"
                else:
                    status = "❌ ERROU"
                    
                detailed_text += f"\nQ{i}: {q_info['text']}\n"
                detailed_text += f"> Você escolheu: '{r.get('answer')}' -> {status}\n"
                if not is_correct:
                    detailed_text += f"> A resposta certa era: '{q_info['correct']}'\n"
                    
            print(f" -> Disparando relatório minucioso para {email}...")
            if send_summary_email(email, name, score, rank, total_students, detailed_text.strip(), acertos, total_q):
                success_count += 1
                
    print(f"[E-mail] Processo finalizado. {success_count}/{total_students} enviados com sucesso.\n")
    return success_count
