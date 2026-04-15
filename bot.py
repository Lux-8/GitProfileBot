import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

TOKEN = "8546708900:AAHQQsJq_F2JL8si049Z0HACul1eI27pDsc"

users_lang = {}

texts = {
    "ru": {
        "start": "Привет! 👋\nОтправь GitHub username (например: torvalds)",
        "invalid": "❌ Это не похоже на GitHub username.",
        "not_found": "❌ Пользователь не найден.",
        "again": "🔄 Искать снова",
    },
    "en": {
        "start": "Hello! 👋\nSend GitHub username (example: torvalds)",
        "invalid": "❌ This doesn't look like a GitHub username.",
        "not_found": "❌ User not found.",
        "again": "🔄 Search again",
    }
}

def lang_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇷🇺 RU", callback_data="ru"),
            InlineKeyboardButton("🇬🇧 EN", callback_data="en"),
        ]
    ])

def again_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(texts[lang]["again"], callback_data="again")]
    ])

# проверка username
def is_valid_username(username: str) -> bool:
    return re.match(r"^[a-zA-Z0-9-]{1,39}$", username) is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_lang[user_id] = "en"

    await update.message.reply_text(
        texts["en"]["start"],
        reply_markup=lang_keyboard()
    )

# смена языка
async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    users_lang[user_id] = query.data
    lang = query.data

    await query.answer()

    await query.edit_message_text(
        texts[lang]["start"],
        reply_markup=lang_keyboard()
    )

async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang = users_lang.get(user_id, "en")

    await query.edit_message_text(
        texts[lang]["start"],
        reply_markup=lang_keyboard()
    )

# обработка username
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = users_lang.get(user_id, "en")

    username = update.message.text.strip()
    if not is_valid_username(username):
        await update.message.reply_text(
            texts[lang]["invalid"],
            reply_markup=again_keyboard(lang)
        )
        return

    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)

    if response.status_code != 200:
        await update.message.reply_text(
            texts[lang]["not_found"],
            reply_markup=again_keyboard(lang)
        )
        return

    data = response.json()

    card = f"""
╭━━━ ✦ GitHub Profile ✦ ━━━╮
👤 Name: {data.get('name') or 'No name'}
🔗 Username: {data.get('login')}
📦 Repos: {data.get('public_repos')}
👥 Followers: {data.get('followers')}
📝 Bio: {data.get('bio') or 'No bio'}
🌐 URL: {data.get('html_url')}
╰━━━━━━━━━━━━━━━━━━━━━━╯
"""

    await update.message.reply_text(
        card,
        reply_markup=again_keyboard(lang)
    )

# запуск
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(change_lang, pattern="^(ru|en)$"))
app.add_handler(CallbackQueryHandler(again, pattern="again"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()