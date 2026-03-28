import streamlit as st
import datetime
from database import register_student, get_student, get_game_state, save_response
from quiz_logic import get_question_by_id, calculate_score
from streamlit_autorefresh import st_autorefresh

def show_student_view():
    st.title("👨‍🎓 Quiz Estatístico - Área do Aluno")
    
    if "student_email" not in st.session_state:
        st.subheader("Registro")
        with st.form("register_form"):
            name = st.text_input("Nome Completo")
            course = st.text_input("Curso")
            email = st.text_input("E-mail")
            nickname = st.text_input("Nickname (Apelido)")
            submit = st.form_submit_button("Entrar no Jogo")
            
            if submit:
                if name and course and email and nickname:
                    success, msg = register_student(name, course, email, nickname)
                    if success:
                        st.session_state.student_email = email
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Por favor, preencha todos os campos!")
        return
        
    # Auto refresh logic for wait room / question state
    st_autorefresh(interval=2000, limit=None, key="student_refresh")
    
    email = st.session_state.student_email
    student = get_student(email)
    st.sidebar.success(f"🎮 Jogador: {student['nickname']} | 🏆 Pontos: {student['score']}")
    
    game_state = get_game_state()
    
    if game_state.get("game_over"):
        st.success("🎉 O Jogo terminou! Muito obrigado por participar! Olhe o seu e-mail para ver todas as correções que preparamos para você.")
        return
        
    if not game_state.get("is_active"):
        st.info("Aguardando o professor iniciar a rodada...")
        return
        
    q_id = game_state.get("current_question")
    if not q_id or q_id == 0:
        st.info("Aguardando o professor lançar a próxima pergunta...")
        return
        
    question = get_question_by_id(q_id)
    if not question:
        st.error("Erro ao carregar a pergunta.")
        return
        
    start_time_str = game_state.get("question_start_time")
    start_time = datetime.datetime.fromisoformat(start_time_str)
    now = datetime.datetime.now()
    elapsed = (now - start_time).total_seconds()
    max_time = 30
    remaining = max(0, int(max_time - elapsed))
    
    st.subheader(f"⏱️ Tempo restante: {remaining}s")
    st.markdown("---")
    
    answered_key = f"answered_{q_id}"
    
    if st.session_state.get(answered_key):
        st.info("✓ Você já respondeu! Aguardando o professor encerrar o relógio...")
        if game_state.get("show_answer"):
            st.write(f"**A resposta correta era:** {question['answer']}")
        return
        
    if remaining == 0:
        st.warning("O tempo acabou!")
        if game_state.get("show_answer"):
            st.write(f"**A resposta correta era:** {question['answer']}")
        return
        
    st.write(f"### {question['text']}")
    
    options = question["options"]
    
    for opt in options:
        if st.button(opt, key=f"btn_{opt}", use_container_width=True):
            ans_time = (datetime.datetime.now() - start_time).total_seconds()
            is_correct = (opt == question["answer"])
            score = calculate_score(ans_time, max_time=30, base_score=100, is_correct=is_correct)
            
            save_response(email, q_id, opt, ans_time, is_correct, score)
            st.session_state[answered_key] = True
            
            if is_correct:
                st.success("Resposta registrada! 🎉")
            else:
                st.info("Resposta registrada! 🤔")
            st.rerun()
