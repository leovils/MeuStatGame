import streamlit as st
from views.student_view import show_student_view
from views.host_view import show_host_view

st.set_page_config(
    page_title="Statistical Quiz App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.sidebar.title("Navegação")
    st.sidebar.write("Selecione a sua visualização:")
    
    role = st.sidebar.radio("Função", ["Aluno (Responder Quiz)", "Professor (Gerenciar Tela)"], index=0)
    
    st.sidebar.markdown("---")
    st.sidebar.info("🎓 **Dica de Teste Local:** Abra duas abas no seu navegador. Numa delas, selecione 'Aluno', e na outra, selecione 'Professor'.")
    
    if role == "Aluno (Responder Quiz)":
        show_student_view()
    else:
        senha = st.sidebar.text_input("🔒 Senha do Professor:", type="password")
        # Tenta buscar a senha nos secrets, senao default eh 1234
        import config
        senha_correta = config.get_secret("host_password")
        if not senha_correta: senha_correta = "1234" # fallback
        
        if senha == senha_correta:
            show_host_view()
        elif senha != "":
            st.error("❌ Senha incorreta! Acesso negado.")
        else:
            st.warning("⚠️ Por favor, insira a senha do professor na barra lateral esquerda para acessar o painel de controle.")

if __name__ == "__main__":
    main()
