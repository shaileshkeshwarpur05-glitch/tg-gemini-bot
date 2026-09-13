import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Telegram ke messages ya text mujhe bhejo, main summary bana kar dunga.")

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    prompt = f"Summarize the following updates/conversation clearly in Hinglish bullet points:\n\n{user_text}"
    response = model.generate_content(prompt)
    await update.message.reply_text(response.text)

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, summarize))
    app.run_polling()
  
