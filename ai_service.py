import google.generativeai as genai
import PyPDF2
import io
import json
import uuid

def extract_text_from_pdf(pdf_bytes):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def extract_text_from_txt(txt_bytes):
    return txt_bytes.decode('utf-8', errors='ignore')

def generate_questions(api_key, document_text, prompt_context, n_easy, n_medium, n_hard):
    genai.configure(api_key=api_key)
    
    # Buscar modelos permitidos dinamicamente pela API para evitar o Erro 404 de Versão/Região
    valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if not valid_models:
        raise Exception("Sua conta não tem nenhum modelo Gemini de geração de texto habilitado!")
        
    model_name = valid_models[0] # Fallback universal
    for m in valid_models:
        if 'gemini-1.5-flash' in m:
            model_name = m
            break
        elif 'gemini-1.5-pro' in m:
            model_name = m
        elif 'gemini-pro' in m:
            model_name = m
            
    print(f"==================================================")
    print(f"[IA] Modelo selecionado automaticamente: {model_name}")
    print(f"==================================================")
            
    model = genai.GenerativeModel(model_name)
    
    total_questions = n_easy + n_medium + n_hard
    if total_questions == 0:
        return []

    system_instruction = f"""
    Você é um professor universitário especialista em criar questões de múltipla escolha.
    Crie um total de {total_questions} perguntas baseadas estritamente no documento fornecido.
    A distribuição obrigatória de dificuldade das perguntas:
    - {n_easy} fáceis ('easy')
    - {n_medium} médias ('medium')
    - {n_hard} difíceis ('hard')
    
    Diretriz do usuário sobre o foco das perguntas:
    "{prompt_context}"

    A saída DEVE ser ESTRITAMENTE um array JSON contendo os objetos das perguntas.
    Formato OBRIGATÓRIO (nenhum outro campo):
    [
      {{
        "id": "q_ai_geradoX",
        "text": "O texto da pergunta",
        "options": ["Opção incorreta", "Opção certa", "Outra incorreta", "Outra incorreta"],
        "answer": "Opção certa",
        "difficulty": "easy"
      }}
    ]

    O campo "answer" deve ter a string OBRIGATORIAMENTE IDÊNTICA a uma das strings em "options".
    NÃO responda nada além do próprio json.
    """

    full_prompt = f"{system_instruction}\n\nDocumento Fonte:\n---\n{document_text}\n---"

    try:
        response = model.generate_content(full_prompt)
        response_text = response.text.strip()
        
        # Extração robista: encontra o primeiro '[' e o último ']' caindo fora conversas da IA
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx+1]
            try:
                questions = json.loads(json_str)
            except Exception as parse_e:
                print(f"Erro ao parsear JSON. String era: {json_str}")
                raise Exception(f"A Inteligência Artificial retornou um texto com formato inválido para JSON: {parse_e}")
        else:
            print("Resposta da IA crua:", response_text)
            raise Exception("A IA falhou em formatar a resposta no formato de lista (Array). Tente novamente.")
            
        # Ensure fresh unique IDs
        for q in questions:
            q["id"] = f"q_ai_{uuid.uuid4().hex[:8]}"
            
        return questions
    except Exception as e:
        raise Exception(f"Erro na geração (verifique cotas ou formato): {str(e)}")
