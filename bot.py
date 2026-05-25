import os
import re
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq

if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

BOT_TOKEN = "ВАШ_ТОКЕН_СЮДА"
GROQ_KEY = "ВАШ_GROQ_КЛЮЧ_СЮДА"

client = Groq(api_key=GROQ_KEY)

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка AI: {e}"

def get_youtube_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я пересказываю YouTube видео.\n\n"
        "Просто скинь мне ссылку на видео!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    youtube_id = get_youtube_id(text)

    if youtube_id:
        await update.message.reply_text("Получаю субтитры...")
        try:
            ytt = YouTubeTranscriptApi()
            transcript = ytt.fetch(youtube_id, languages=['ru', 'en', 'a.ru', 'a.en'])
            full_text = " ".join([t.text for t in transcript])
            full_text = full_text.encode('utf-8', errors='ignore').decode('utf-8')
            await update.message.reply_text("Анализирую видео...")
            summary = ask_ai(
                f"Summarize this video transcript in Russian, list main points:\n\n{full_text[:3000]}"
            )
            await update.message.reply_text(f"Резюме:\n\n{summary}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
    else:
        summary = ask_ai(
            f"Summarize this text briefly in Russian:\n\n{text}"
        )
        await update.message.reply_text(f"Пересказ:\n\n{summary}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot started!")
app.run_polling()