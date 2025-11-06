import os, uuid, asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
import uvicorn

# --------------------------
# Config
# --------------------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BIN_CHANNEL = os.getenv("BIN_CHANNEL", "@Dupolobn")  # can be @username or -100XXXX
DATABASE_URL = os.getenv("DATABASE_URL", "")
FQDN = os.getenv("FQDN", "").rstrip("/")
PORT = int(os.getenv("PORT", 8080))

# --------------------------
# MongoDB Setup
# --------------------------
mongo = MongoClient(DATABASE_URL)
db = mongo["filetolink_db"]
collection = db["files"]

# --------------------------
# FastAPI Setup
# --------------------------
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "online", "message": "File To Link Bot is working!"}

@app.get("/dl/{file_id}")
async def download(file_id: str):
    data = collection.find_one({"_id": file_id})
    if not data:
        return {"error": "File not found"}
    return RedirectResponse(url=data["file_url"])

@app.get("/watch/{file_id}")
async def watch(file_id: str):
    data = collection.find_one({"_id": file_id})
    if not data:
        return {"error": "File not found"}
    file_url = data["file_url"]
    html = f"""
    <html>
    <head><title>{data['file_name']}</title></head>
    <body style='text-align:center;'>
        <video width='90%' height='auto' controls autoplay>
            <source src='{file_url}' type='video/mp4'>
        </video>
        <p><a href='{file_url}' download>Download File</a></p>
    </body></html>
    """
    return html

# --------------------------
# Pyrogram Bot Setup
# --------------------------
bot = Client("FileToLinkBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def resolve_bin_channel():
    global BIN_CHANNEL
    try:
        chat = await bot.get_chat(BIN_CHANNEL)
        BIN_CHANNEL = chat.id
        print(f"✅ BIN_CHANNEL resolved: {BIN_CHANNEL}")
    except Exception as e:
        print(f"❌ Failed to resolve BIN_CHANNEL: {e}")

@bot.on_message(filters.private & filters.media)
async def handle_file(client, message):
    try:
        # 2GB check
        if message.document and message.document.file_size > 2_000_000_000:
            return await message.reply_text("⚠️ Sorry! Telegram bots can only handle files up to 2 GB.")

        # Copy to channel
        file = await message.copy(chat_id=BIN_CHANNEL)
        file_id = str(uuid.uuid4())
        file_url = f"https://t.me/{file.chat.username}/{file.id}" if file.chat.username else file.link

        # Insert into DB
        collection.insert_one({
            "_id": file_id,
            "file_name": message.document.file_name if message.document else "Media",
            "file_url": file_url
        })

        # Build links
        dl_link = f"{FQDN}/dl/{file_id}"
        watch_link = f"{FQDN}/watch/{file_id}"
        share_link = f"https://t.me/{client.me.username}?start=file_{file_id}"

        buttons = [
            [InlineKeyboardButton("📥 Download", url=dl_link)],
            [InlineKeyboardButton("🎬 Watch Online", url=watch_link)],
            [InlineKeyboardButton("🔗 Share", url=share_link)]
        ]

        await message.reply_text(
            f"**✅ Your Link Generated!**\n\n📂 File Name: `{message.document.file_name if message.document else 'Media'}`\n\n📥 [Download]({dl_link})\n🖥 [Watch]({watch_link})",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        await message.reply_text(f"⚠️ Oops! Error: {e}")

# --------------------------
# Run bot + web server
# --------------------------
async def main():
    await bot.start()
    await resolve_bin_channel()
    print("✅ Bot started successfully!")
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
