import streamlit as st
import datetime
import json
from database import get_leaderboard, get_game_state, update_game_state
from quiz_logic import generate_round
from streamlit_autorefresh import st_autorefresh
from ai_service import extract_text_from_pdf, extract_text_from_txt, generate_questions
import warnings
warnings.filterwarnings("ignore")

def show_host_view():
    st.title("👨‍🏫 Quiz Estatístico - Telão do Professor")
    
    # Auto-refresh to keep the leaderboard and time synced
    st_autorefresh(interval=2000, limit=None, key="host_refresh")
    
    tab_jogo, tab_ai = st.tabs(["🎮 Gestão do Jogo", "🤖 Gerador de Perguntas com IA"])
    
    with tab_jogo:
        game_state = get_game_state()
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.subheader("Leaderboard 🏆")
            lb = get_leaderboard()
            if not lb.empty:
                st.dataframe(lb, hide_index=True, use_container_width=True)
                
                # Botão para baixar a planilha diretamente do Streamlit
                csv = lb.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Planilha Geral",
                    data=csv,
                    file_name=f"Planilha_Geral_Notas.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.write("Nenhum aluno registrado ainda.")
                
        with col1:
            st.subheader("Controle do Jogo")
            
            if game_state.get("game_over"):
                st.success("🎉 O Jogo Finalizou Definitivamente!")
                if "email_msg" in st.session_state:
                    if "❌" in st.session_state["email_msg"]:
                        st.error(st.session_state["email_msg"])
                    else:
                        st.success(st.session_state["email_msg"])
                st.info("A Planilha Geral com todos os resultados da turma está pronta! Clique abaixo para salvar no seu computador.")
                
                from gerar_relatorio import generate_report
                csv_final = generate_report()
                if csv_final:
                    st.download_button(
                        label="📥 BAIXAR O RELATÓRIO OFICIAL COMPLETO (EXCEL)",
                        data=csv_final,
                        file_name=f"Relatorio_Final_Quiz.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                st.markdown("---")
                st.warning("Para dar aula para uma turma diferente com as mesmas perguntas do dia, você pode zerar a sala.")
                if st.button("🔄 Zerar Tudo e Começar Nova Turma", type="primary"):
                    from database import reset_room
                    reset_room()
                    st.rerun()
                return

            if not game_state.get("is_active"):
                st.write("O jogo está pausado ou não foi iniciado.")
                if st.button("▶️ Iniciar Rodada 1", type="primary"):
                    qs = generate_round(1, 10)
                    update_game_state({
                        "is_active": True,
                        "current_round": 1,
                        "round_questions": qs,
                        "current_q_index": 0,
                        "current_question": 0,
                        "show_answer": False
                    })
                    st.rerun()
            else:
                qs = game_state.get("round_questions", [])
                idx = game_state.get("current_q_index", 0)
                
                st.info(f"Rodada {game_state.get('current_round')} - Pergunta {idx + 1} de {len(qs)}")
                
                if idx >= len(qs):
                    st.success("🏁 Rodada finalizada!")
                    if st.button("⏹️ Encerrar Jogo Definitivamente", type="primary"):
                        try:
                            from database import _load_db
                            from email_service import broadcast_emails
                            import time
                            db = _load_db()
                            lb = get_leaderboard()
                            qs_all = []
                            try:
                                qs_all = json.load(open('questions.json', 'r', encoding='utf-8'))
                            except:
                                pass
                            sent = broadcast_emails(lb, db, qs_all)
                            st.session_state['email_msg'] = f"✅ Jogo encerrado! O motor de e-mail tentou processar {sent} envios."
                        except Exception as e:
                            st.session_state['email_msg'] = f"❌ Erro Crítico do Python ao enviar E-mails: {str(e)}"
                        update_game_state({"game_over": True})
                        st.rerun()
                    return
                    
                current_q = qs[idx]
                is_q_active = (game_state.get("current_question") == current_q["id"])
                
                if not is_q_active:
                    st.markdown(f"**Próxima Pergunta a ser lançada:**")
                    st.info(f"{current_q['text']}")
                    if st.button("🚀 Lançar Pergunta para Alunos", type="primary"):
                        update_game_state({
                            "current_question": current_q["id"],
                            "question_start_time": datetime.datetime.now().isoformat(),
                            "show_answer": False
                        })
                        st.rerun()
                else:
                    st.write(f"### {current_q['text']}")
                    start_time = datetime.datetime.fromisoformat(game_state["question_start_time"])
                    now = datetime.datetime.now()
                    elapsed = (now - start_time).total_seconds()
                    rem = max(0, int(30 - elapsed))
                    
                    # Progress bar for visual effect
                    progress = max(0, min(100, int((rem / 30) * 100)))
                    st.progress(progress, text=f"⏱️ Tempo restante: {rem}s")
                    
                    if not game_state.get("show_answer"):
                        if st.button("👀 Mostrar Resposta Correta"):
                            update_game_state({"show_answer": True})
                            st.rerun()
                    else:
                        st.success(f"**Resposta Correta:** {current_q['answer']}")
                        if st.button("⏭️ Avançar para a próxima pergunta", type="primary"):
                            update_game_state({
                                "current_question": 0,
                                "current_q_index": idx + 1,
                                "show_answer": False
                            })
                            st.rerun()

    with tab_ai:
        st.subheader("Gerar Novas Perguntas (Gemini AI)")
        st.write("Faça upload de um PDF ou Texto para criar novas perguntas automaticamente com base no conteúdo.")
        
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            st.warning("⚠️ Você precisa adicionar `GEMINI_API_KEY = 'sua_chave'` no arquivo `.streamlit/secrets.toml` antes de usar essa funcionalidade.")
            
        uploaded_file = st.file_uploader("Documento Base", type=["pdf", "txt"])
        prompt_ctx = st.text_area("Diretrizes de Geração", placeholder="Ex: Crie as questões usando as referências do Capítulo 2 focadas no Teorema do Limite Central...")
        
        cc1, cc2, cc3 = st.columns(3)
        n_easy = cc1.number_input("Qtd. Fáceis", min_value=0, max_value=50, value=2)
        n_med = cc2.number_input("Qtd. Médias", min_value=0, max_value=50, value=2)
        n_hard = cc3.number_input("Qtd. Difíceis", min_value=0, max_value=50, value=1)
        
        if st.button("🤖 Processar Documento e Gerar", type="primary"):
            if not api_key:
                st.error("Configure sua API Key primeiro.")
            elif not uploaded_file:
                st.error("Por favor, anexe um arquivo PDF ou TXT!")
            else:
                with st.spinner("Analisando o documento e gerando testes com Gemini... ISSO PODE DEMORAR ALGUNS SEGUNDOS."):
                    try:
                        if uploaded_file.name.endswith('.pdf'):
                            text_content = extract_text_from_pdf(uploaded_file.read())
                        else:
                            text_content = extract_text_from_txt(uploaded_file.read())
                            
                        st.info(f"📄 Documento processado: {len(text_content)} caracteres lidos.")
                        
                        questions = generate_questions(api_key, text_content, prompt_ctx, n_easy, n_med, n_hard)
                        
                        if questions:
                            st.success(f"🎊 Sucesso! Obtidas {len(questions)} novas perguntas! Salvando em questions.json...")
                            
                            try:
                                with open('questions.json', 'r', encoding='utf-8') as f:
                                    db_qs = json.load(f)
                            except FileNotFoundError:
                                db_qs = []
                                
                            db_qs.extend(questions)
                            
                            with open('questions.json', 'w', encoding='utf-8') as f:
                                json.dump(db_qs, f, indent=4, ensure_ascii=False)
                            
                            st.json(questions)
                        else:
                            st.warning("Nenhuma pergunta gerada. Verifique se as quantidades > 0.")
                            
                    except Exception as e:
                        st.error(f"Erro ao gerar: {e}")
