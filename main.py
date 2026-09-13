import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import google.generativeai as genai

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"UserBot Live!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    server.serve_forever()

API_ID = int(os.environ["API_ID"].strip())
API_HASH = os.environ["API_HASH"].strip()
SESSION_STRING = os.environ["SESSION_STRING"].strip()
GEMINI_KEY = os.environ["GEMINI_API_KEY"].strip()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-3.6-flash")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r"(?i)^/summary", outgoing=True))
async def handle_summary(event):
    parts = event.raw_text.strip().split()
    target_peer = None
    limit = 100

    if len(parts) > 1:
        param = parts[1]
        if param.isdigit():
            limit = int(param)
            target_peer = event.chat_id
        else:
            target_peer = param
            if len(parts) > 2 and parts[2].isdigit():
                limit = int(parts[2])
    elif event.is_private and event.chat_id == (await client.get_me()).id:
        target_peer = None
    else:
        target_peer = event.chat_id

    status_msg = await event.reply("Malik, Geminia aapan kaam pe lag gail ba...")

    collected_text = []

    if target_peer:
        try:
            entity = await client.get_entity(target_peer)
            chat_title = getattr(entity, 'title', getattr(entity, 'first_name', 'Chat'))
            collected_text.append(f"--- Chat: {chat_title} (Last {limit} messages) ---")
            async for msg in client.iter_messages(entity, limit=limit):
                if msg.text:
                    sender = await msg.get_sender()
                    sender_name = getattr(sender, "first_name", "User") or "User"
                    collected_text.append(f"{sender_name}: {msg.text}")
        except Exception as e:
            await status_msg.edit(f"Sorry malik, Nalayak bani hm: {str(e)}")
            return
    else:
        async for dialog in client.iter_dialogs(limit=15):
            if dialog.unread_count > 0:
                collected_text.append(f"\n--- Chat: {dialog.name} ({dialog.unread_count} unread) ---")
                async for msg in client.iter_messages(dialog.id, limit=dialog.unread_count):
                    if msg.text:
                        sender = await msg.get_sender()
                        sender_name = getattr(sender, "first_name", "User") or "User"
                        collected_text.append(f"{sender_name}: {msg.text}")

    if not collected_text or len(collected_text) <= 1:
        await status_msg.edit("Malik, enjoy kara koi message naikhe kaile!")
        return

    raw_data = "\n".join(reversed(collected_text))[:8500]
    prompt = (
        "Summarize these Telegram messages clearly into concise English bullet points. "
        "Highlight important updates, action items, or announcements:\n\n"
        f"{raw_data}"
    )

    try:
        response = model.generate_content(prompt)
        await status_msg.edit(response.text)
    except Exception as err:
        await status_msg.edit(f"Malik, Geminia kaam naikhe karal chahat: {str(err)}")

async def main():
    await client.start()
    print("UserBot running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    asyncio.run(main())
    
