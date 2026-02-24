import json
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# RAM storage (per user)
user_files = {}

# Converter
def convert_json(data):
    output = []

    if isinstance(data, list):
        for entry in data:
            if "accounts" in entry and isinstance(entry["accounts"], list):
                for acc in entry["accounts"]:
                    output.append({
                        "uid": acc.get("uid"),
                        "password": acc.get("password"),
                        "account_id": str(acc.get("uid")) + "3",
                        "name": acc.get("name"),
                        "region": acc.get("region", "IND"),
                        "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "thread_id": 1
                    })
    return output


async def ac_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_files[user_id] = []
    await update.message.reply_text("📁 Send your JSON files.\nWhen finished, type `/done`")


async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_files:
        await update.message.reply_text("❗ Start with /ac first.")
        return

    document = update.message.document

    if not document.file_name.endswith(".json"):
        await update.message.reply_text("❌ Only .json files allowed.")
        return

    file = await document.get_file()
    bytes_data = await file.download_as_bytearray()

    user_files[user_id].append(bytes_data)
    await update.message.reply_text(f"✔ Saved: {document.file_name}")


async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_files or not user_files[user_id]:
        await update.message.reply_text("❗ No files uploaded.")
        return

    await update.message.reply_text("⏳ Processing...")

    merged = []

    for file_bytes in user_files[user_id]:
        try:
            data = json.loads(file_bytes.decode("utf-8"))
            merged.extend(convert_json(data))
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    final_bytes = json.dumps(merged, indent=4).encode("utf-8")

    await update.message.reply_document(
        document=final_bytes,
        filename="all_accounts.json"
    )

    user_files[user_id] = []
    await update.message.reply_text("🎉 All files merged & converted!")


BOT_TOKEN = "8430808840:AAFHwcZy1lbdFfO0N_0plqIaUmHciLbYed0"

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("ac", ac_cmd))
app.add_handler(CommandHandler("done", done_cmd))
app.add_handler(MessageHandler(filters.Document.ALL, file_handler))

app.run_polling()