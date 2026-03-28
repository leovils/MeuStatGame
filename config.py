import os
import streamlit as st

def get_secret(key):
    try:
        # Na nuvem, o Streamlit gerencia os segredos autonomamente por aqui
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, "")
