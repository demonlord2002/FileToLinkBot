from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
from config import DATABASE_URL, FQDN, BIN_CHANNEL
from pyrogram import Client
import os

app = FastAPI()

mongo = MongoClient(DATABASE_URL)
db = mongo["filetolink"]
files = db["files"]

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("webbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.get("/")
async def home():
    return {"status": "online", "message": "File To Link Bot Active"}

@app.get("/dl/{file_id}")
async def download(file_id: str):
    file = files.find_one({"_id": file_id})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    async with bot:
        file_link = await bot.export_chat_invite_link(BIN_CHANNEL)
    return RedirectResponse(url=file_link)

@app.get("/watch/{file_id}")
async def watch(file_id: str):
    return RedirectResponse(url=f"{FQDN}/dl/{file_id}")
