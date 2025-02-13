import subprocess
import time
import requests
import ollama
from sentence_transformers import SentenceTransformer
from duckduckgo_search import DDGS
from pymongo import MongoClient
from datetime import datetime
import whisper
import os
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

TELEGRAM_TOKEN = "7575830756:AAGaHWRGsWK72YpcMtQ-Cjxsbh0RfDMa_X4"

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

def voice_to_text(audio_path):
    result = whisper_model.transcribe(audio_path, language="en")
    return result["text"]

async def generate_response(user_message: str, chat_id: str) -> str:
    chat_id = str(chat_id)
    
    chat_entry = chats_collection.find_one({"_id": chat_id})
    if not chat_entry:
        chats_collection.insert_one({"_id": chat_id, "messages": [], "created_at": datetime.utcnow()})

    chats_collection.update_one(
        {"_id": chat_id},
        {"$push": {"messages": {"role": "user", "content": user_message}}}
    )

    search_results = list(DDGS().text(user_message, max_results=5))
    web_content = " ".join(res['body'] for res in search_results if 'body' in res)

    prompt = f"Web Search Data: {web_content}\nQuestion: {user_message}\nAnswer:"
    response = ollama.chat(
        model="llama2",
        messages=[{"role": "user", "content": prompt}]
    )

    ollama_content = response.get('message', {}).get('content', str(response))

    chats_collection.update_one(
        {"_id": chat_id},
        {"$push": {"messages": {"role": "ollama", "content": ollama_content}}}
    )

    return ollama_content

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! I'm GoLLamaBot. Write me message or voice meassage")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    chat_id = str(update.message.chat_id)

    response_text = await generate_response(user_message, chat_id)
    await update.message.reply_text(response_text)

async def handle_voice(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    voice = update.message.voice

    file = await context.bot.get_file(voice.file_id)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
        temp_audio_path = temp_audio.name
        await file.download_to_drive(temp_audio_path)

    recognized_text = voice_to_text(temp_audio_path)

    os.remove(temp_audio_path)

    await update.message.reply_text(f"Recognized: {recognized_text}")

    response_text = await generate_response(recognized_text, chat_id)
    
    await update.message.reply_text(response_text)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("GoLLamaBot launched...")
    app.run_polling()

if __name__ == "__main__":
    main()
