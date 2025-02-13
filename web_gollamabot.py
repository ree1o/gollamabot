import subprocess
import time
import requests
import streamlit as st
from sentence_transformers import SentenceTransformer
import ollama
from duckduckgo_search import DDGS
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import whisper
import os
from gtts import gTTS
import tempfile

MONGO_URI = "mongodb+srv://runarkenz:1335r6000qr@cluster0.q7ygq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "chatbot"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
chats_collection = db["chats"]

def is_ollama_running():
    try:
        response = requests.get("http://127.0.0.1:11434")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def start_ollama():
    subprocess.Popen(['ollama', 'start'])
    time.sleep(5)

if not is_ollama_running():
    print("Starting Ollama...")
    start_ollama()
else:
    print("Ollama is already running.")

model = SentenceTransformer('all-MiniLM-L6-v2')

whisper_model = whisper.load_model("base")

st.title("ChatGollama")
st.sidebar.header("Chats")

def get_chats():
    return list(chats_collection.find({}, {"_id": 1, "title": 1}))

if st.sidebar.button("Create New Chat"):
    new_chat = {"title": "New Chat", "messages": [], "created_at": datetime.utcnow()}
    chat_id = str(chats_collection.insert_one(new_chat).inserted_id)
    st.session_state.current_chat = chat_id
    st.rerun()

chats = get_chats()
chat_options = {str(chat["_id"]): chat.get("title", "Unnamed Chat") for chat in chats}

if "current_chat" not in st.session_state and chat_options:
    st.session_state.current_chat = list(chat_options.keys())[0]

selected_chat = st.sidebar.selectbox("Existing Chats", options=chat_options.keys(), format_func=lambda x: chat_options[x], index=list(chat_options.keys()).index(st.session_state.current_chat) if st.session_state.current_chat in chat_options else 0)

if selected_chat:
    st.session_state.current_chat = selected_chat

if "current_chat" in st.session_state:
    chat_id = st.session_state.current_chat
    chat_data = chats_collection.find_one({"_id": chat_id})

    if not chat_data:
        st.error("Chat not found! Creating a new one.")
        new_chat = {"_id": chat_id, "title": "New Chat", "messages": [], "created_at": datetime.utcnow()}
        chats_collection.insert_one(new_chat)
        chat_data = new_chat

    chat_title = chat_data.get("title", "Unnamed Chat")

    st.write(f"### {chat_title}")

    chat_history = chat_data["messages"] if chat_data else []

    for msg in chat_history:
        role = "You" if msg["role"] == "user" else "Ollama"
        st.write(f"**{role}:** {msg['content']}")

    def record_audio(duration=5, samplerate=44100):
        st.info("🎙 Say something...")
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
        sd.wait()
        return samplerate, audio

    def speech_to_text(audio_data, samplerate):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name
            wav.write(temp_wav_path, samplerate, audio_data)

        try:
            result = whisper_model.transcribe(temp_wav_path, language="en")
            return result["text"]
        finally:
            os.remove(temp_wav_path)

    def text_to_speech(text):
        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio_path = temp_audio.name
            tts.save(temp_audio_path)
        return temp_audio_path

    auto_send = st.sidebar.checkbox("Auto-send Voice Query", value=True)

    if "query" not in st.session_state:
        st.session_state.query = ""

    query = st.text_input("Message to ChatGollama:", value=st.session_state.query)
    send_button = st.button("Send")

    if st.button("🎤 Record Voice"):
        samplerate, audio_data = record_audio()
        recognized_text = speech_to_text(audio_data, samplerate)
        st.write("📝 Recognized:", recognized_text)

        if auto_send:
            query = recognized_text
            st.session_state.query = ""
            send_button = True
        else:
            st.session_state.query = recognized_text

    if send_button and query.strip():
        if len(chat_history) == 0:
            new_title = f"{query[:50]}"
            chats_collection.update_one(
                {"_id": chat_id},
                {"$set": {"title": new_title}}
            )

        chats_collection.update_one(
            {"_id": chat_id},
            {"$push": {"messages": {"role": "user", "content": query}}}
        )


        search_results = list(DDGS().text(query, max_results=5))
        sources = [res['href'] for res in search_results if 'href' in res]
        web_content = " ".join(res['body'] for res in search_results if 'body' in res)

        prompt = f"Web Search Data: {web_content}\nQuestion: {query}\nAnswer:"
        try:
            response = ollama.chat(
                model="llama2",
                messages=[{"role": "user", "content": prompt}]
            )

            ollama_content = response.get('message', {}).get('content', str(response))

            ollama_response = {
                "role": "ollama",
                "content": ollama_content,
                "sources": sources
            }

            chats_collection.update_one(
                {"_id": chat_id},
                {"$push": {"messages": ollama_response}}
            )

            audio_file = text_to_speech(ollama_content)
            st.audio(audio_file, format="audio/mp3")

            st.session_state.query = ""

            st.rerun()

        except Exception as e:
            st.error(f"Error interacting with Ollama: {e}")

else:
    st.write("Create or load a chat to start a conversation.")