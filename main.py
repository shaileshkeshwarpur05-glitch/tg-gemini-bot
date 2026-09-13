import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import google.generativeai as genai

# Render port requirement satisfy karne ke liye dummy server
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"UserBot Live!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    server.serve_forever()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"] 
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r"(?i)^/summary" , outgoing=true))
async def handle_summary(event):
    me = await client.get_me()
    # Sirf aapke bhejne par chalega
    if event.sender_id != me.id:
        return

    status_msg = await event.reply("Unread messages nikaal raha hoon, wait karein...")

    collected_text = []
    # Recent dialogs check karega
    async for dialog in client.iter_dialogs(limit=15):
        if dialog.unread_count > 0:
            chat_name = dialog.name
            collected_text.append(f"\n--- Chat: {chat_name} ({dialog.unread_count} unread) ---")
            async for msg in client.iter_messages(dialog.id, limit=dialog.unread_count):
                if msg.text:
                    sender = await msg.get_sender()
                    sender_name = getattr(sender, "first_name", "User") or "User"
                    collected_text.append(f"{sender_name}: {msg.text}")

    if not collected_text:
        await status_msg.edit("Abhi koi naye unread messages nahi hain!")
        return

    raw_data = "\n".join(collected_text)[:8000]
    prompt = (
        "Summarize these unread Telegram chats clearly into concise Hinglish bullet points. "
        "Highlight important updates, tasks, or urgent points:\n\n"
        f"{raw_data}"
    )

    response = model.generate_content(prompt)
    await status_msg.edit(response.text)

async def main():
    await client.start()
    print("UserBot running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    asyncio.run(main())
    
