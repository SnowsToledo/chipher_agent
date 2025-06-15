import streamlit as st
import os
import time
import docx2txt
from anthropic import BaseModel
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('multi-qa-mpnet-base-dot-v1')

corpus = []

for i, doc in enumerate(os.listdir("Docs")):
    if doc.endswith(".docx"):
        corpus.append({"id":i, "text":docx2txt.process(f"Docs/{doc}")})


doc_embeddings = {
    doc["id"]: model.encode(doc["text"], convert_to_tensor = True) for doc in corpus
}


class QueryRequest(BaseModel):
    query: str

def query_rag(request: QueryRequest):
  query_embedding = model.encode(request, convert_to_tensor = True)
  best_doc = {}
  best_score = float("-inf")
  client = genai.Client(api_key=api_key)
  #TODO buscar doc mais próximo da query
  for doc in corpus:
    score = util.cos_sim(query_embedding, doc_embeddings[doc["id"]])
    if score > best_score:
      best_score = score
      best_doc = doc

    prompt = f"Você é um assintente de IA para uma empresa júnior de ciência de dados e responderá a funcionários da empresa, responda educadamente.Caso a pergunta não seja adequada aos conchecimentos dos documentos, diga que você não é capaz de responder. Responda baseada apenas baseado nestes documento: {best_doc['text']}\n\nUser: {request}\nAssistant:"
    try:
        #TODO eenviar doc e prompt para o gemini
        response = client.models.generate_content_stream(
        model="gemini-1.5-flash",
        contents=prompt
        )
        return response

    except Exception as e:
        raise Exception(str(e))

st.write("Chipher AI Agent para auxiliar os dataístas")

st.caption("Este é um agente construído para auxiliar dataístas com perguntas e respostas sobre  documentos internos e contratos.")
with st.sidebar:
    api_key = st.text_input("Google API Key", key="chatbot_api_key", type="password")
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Croac croac, cuá! Eu sou o Chipher, um corvo inteligente que adora ajudar dataístas com perguntas e respostas sobre documentos internos e contratos."}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input():
    # Add user message to chat history
    if not api_key:
        st.info("Por favor informe sua chave api google para continuar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = query_rag(prompt)
        # Simulate stream of response with milliseconds delay
        for chunk in assistant_response:
            full_response += chunk.text + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
