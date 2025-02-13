🤖 GoLLamaBot - AI-Powered Chatbot
GoLLamaBot is an AI-powered chatbot that works both as a Streamlit web app and a Telegram bot. It utilizes Ollama for LLM-based responses, DuckDuckGo Search for web-enhanced answers, Whisper for speech recognition, and MongoDB Atlas for storing chat history.

🚀 Features
Chat with AI powered by Ollama (Llama 2)
Web-enhanced responses using DuckDuckGo Search
Speech-to-Text support (voice messages in Telegram & Streamlit)
Text-to-Speech responses (Streamlit version)
Chat history stored in MongoDB Atlas
Works in both Web (Streamlit) and Telegram

🛠️ Setup
1️⃣ Install Dependencies
First, install the required dependencies:

pip install -r requirements.txt

2️⃣ Install Ollama
Ollama is required to run the AI model. Install it with:

curl -fsSL https://ollama.com/install.sh | sh
Then, download the model (Llama 2 in this case):

ollama pull llama2

3️⃣ Set Up MongoDB Atlas
Make sure you have a MongoDB Atlas database. Update the MONGO_URI in the code:

MONGO_URI = "your_mongodb_connection_string"

4️⃣ Run the Web App (Streamlit)
Start the Streamlit chatbot:

streamlit run web_gollamabot.py

5️⃣ Run the Telegram Bot
Set up a Telegram bot token by talking to @BotFather.
Update the TELEGRAM_TOKEN in tg_gollamabot.py:

TELEGRAM_TOKEN = "your_telegram_bot_token"
Then, start the bot:

python tg_gollamabot.py

🎤 Voice Features
Send a voice message (Telegram) → The bot transcribes it using Whisper and responds.
Record voice in Streamlit → The app converts speech to text and sends it to the chatbot.
Text-to-Speech in Streamlit → The bot’s responses are converted to audio using gTTS.

🖥️ Usage
🔹 Web App (Streamlit)
Open the app by running streamlit run web_gollamabot.py
Start a new chat or select an existing one from the sidebar.
Type your message or record your voice.
The chatbot responds with text and optionally plays an audio response.

🔹 Telegram Bot
Start the bot by sending /start.
Send a text message or voice message.
The bot will process your message and send a reply.
