import os
import streamlit as st
from openai import OpenAI
import instructor

# 1. Fallback Key Retrieval: Prioritize Streamlit Cloud Secrets over system env variables
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# 2. Strict Key Enforcement Guardrail
if not api_key:
    st.error("🔒 Configuration Error: OpenAI API Key missing. Please configure your Streamlit Secrets or Environment Variables.")
    st.stop()

# 3. Initialize the Pydantic-patched instructor client engine
client = instructor.from_openai(OpenAI(api_key=api_key))

# Keep your existing extraction logic or Pydantic models below this line...