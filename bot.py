import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os
import time

# --- Configuration ---
API_TOKEN = '8537226856:AAH1OFtXzNaiWTmWaAisq-HZTcW38BH7bM8'
CHANNEL_ID = '@MuleTechReact'
ADMIN_ID = 7738656478  # የርስዎ ID ተተክቷል
bot = telebot.TeleBot(API_TOKEN)

user_links = {}
USER_FILE = "users.txt"

# --- User Management ---
def save_user(user_id):
    if not os.path.exists(USER_FILE):
        open(USER_FILE, "w").close()
    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(str(user_id) + "\n")

# --- Membership Check ---
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return True

def send_force_join(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("🔄 I have Joined", callback_data="check_sub"))
    bot.send_message(message.chat.id, "⚠️ **Please join our channel to use this bot!**", reply_markup=markup, parse_mode="Markdown")

# --- 1. Broadcast Command (Admin Only) ---
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.reply_to(message, "📌 Usage: `/broadcast Your message here`")
        return
    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()
    bot.send_message(ADMIN_ID, f"⏳ Sending to {len(users)} users...")
    count = 0
    for user in users:
        try:
            bot.send_message(user, msg_text)
            count += 1
            time.sleep(0.1)
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast done! Sent to {count} users.")

# --- 2. Inline Search (@bot query) ---
@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    try:
        search_query = inline_query.query
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch5:{search_query}", download=False)['entries']
        results = []
        for i, entry in enumerate(search_results):
            if entry:
                video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                results.append(types.InlineQueryResultArticle(
                    id=str(i), title=entry.get('title'),
                    input_message_content=types.InputTextMessageContent(video_url),
                    thumb_url=f"https://img.youtube.com/vi/{entry['id']}/mqdefault.jpg"
                ))
        bot.answer_inline_query(inline_query.id, results)
    except: pass

# --- 3. Link Handler ---
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
        return
    save_user(message.from_user.id)
    url = message.text
    user_links[message.chat.id] = url
    
    if "youtube.com" in url or "youtu.be" in url:
        status_msg = bot.send_message(message.chat.id, "🔎 YouTube link detected...")
        markup = types.InlineKeyboardMarkup(row_width=2)
        qs = ["240", "360", "480", "720", "1080"]
        btns = [types.InlineKeyboardButton(f"🎬 {q}p", callback_data=f"q_{q}") for q in qs]
        markup.add(*btns)
        markup.add(types.InlineKeyboardButton("🎵 MP3 Audio", callback_data="q_mp3"))
        bot.edit_message_text("🎥 Select YouTube Quality:", message.chat.id, status_msg.message_id, reply_markup=markup)
    else:
        status_msg = bot.send_message(message.chat.id, "⏳ Downloading...")
        download_logic(message.chat.id, url, "best", status_msg.message_id)

# --- 4. Quality Selection Handler ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("q_"))
def handle_quality(call):
    url = user_links.get(call.message.chat.id)
    q = call.data.replace("q_", "")
    if not url: return
    bot.edit_message_text(f"⏳ Downloading {q}...", call.message.chat.id, call.message.message_id)
    fmt = "bestaudio/best" if q=="mp3" else f"bestvideo[height<={q}]+bestaudio/best"
    download_logic(call.message.chat.id, url, fmt, call.message.message_id, is_mp3=(q=="mp3"))

# --- 5. Core Download Logic ---
def download_logic(chat_id, url, fmt, status_msg_id, is_mp3=False):
    ext = "mp3" if is_mp3 else "mp4"
    file_name = f"dl_{int(time.time())}.{ext}"
    ydl_opts = {'format': fmt, 'outtmpl': file_name, 'quiet': True}
    if is_mp3:
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open(file_name, 'rb') as f:
            if is_mp3: bot.send_audio(chat_id, f)
            else: bot.send_video(chat_id, f)
        os.remove(file_name)
        bot.delete_message(chat_id, status_msg_id)
    except:
        bot.send_message(chat_id, "❌ Error: Unsupported or private link.")
        if os.path.exists(file_name): os.remove(file_name)

# --- Start/Verify ---
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
    else:
        bot.send_message(message.chat.id, "👋 Send a video link or search YouTube using @!")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("✅ Verified! Send a link.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Please join first!", show_alert=True)

print("✅ Full Bot is Active!")
bot.polling(none_stop=True)
