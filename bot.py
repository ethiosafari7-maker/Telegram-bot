import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os
import time

# --- Configuration ---
# አዲሱን API Token እዚህ ጋር አስገብቻለሁ
API_TOKEN = '8537226856:AAGi84G9VXn3s_OIu6iZpWnKKSMz7oOimqQ'
CHANNEL_ID = '@MuleTechReact'
ADMIN_ID = 7738656478 
bot = telebot.TeleBot(API_TOKEN)

user_links = {}
USER_FILE = "users.txt"

# --- User Database ---
def save_user(user_id):
    if not os.path.exists(USER_FILE):
        open(USER_FILE, "w").close()
    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(str(user_id) + "\n")

# --- Force Join Check ---
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Subscription Check Error: {e}")
        return True 

def send_force_join(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")
    verify = types.InlineKeyboardButton("🔄 I Have Joined", callback_data="check_sub")
    markup.add(btn)
    markup.add(verify)
    bot.send_message(message.chat.id, f"⚠️ **ይህንን ቦት ለመጠቀም መጀመሪያ የኛን ቻናል መቀላቀል አለብዎት!**\n\nእባክዎ ቻናሉን ይቀላቀሉና 'I Have Joined' የሚለውን ይጫኑ።", 
                     reply_markup=markup, parse_mode="Markdown")

# --- 1. Admin Broadcast Feature ---
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.reply_to(message, "📌 አጠቃቀም: `/broadcast መልዕክት እዚህ ይጻፉ`", parse_mode="Markdown")
        return
    
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            users = f.read().splitlines()
        bot.send_message(ADMIN_ID, f"⏳ ለ {len(users)} ተጠቃሚዎች በመላክ ላይ...")
        count = 0
        for user in users:
            try:
                bot.send_message(user, msg_text)
                count += 1
                time.sleep(0.3) 
            except: pass
        bot.send_message(ADMIN_ID, f"✅ ተጠናቋል! ለ {count} ተጠቃሚዎች ተልኳል።")

# --- 2. Start Command ---
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
    else:
        bot.send_message(message.chat.id, "👋 እንኳን ደህና መጡ! የቪዲዮ ሊንክ (YouTube, TikTok, FB, IG) ይላኩ ወይም በ @ በመጠቀም ቪዲዮ ይፈልጉ።")

# --- 3. Link Handling & Quality Selection ---
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
        return
    save_user(message.from_user.id)
    url = message.text
    user_links[message.chat.id] = url
    
    if "youtube.com" in url or "youtu.be" in url:
        markup = types.InlineKeyboardMarkup(row_width=2)
        qs = ["360", "480", "720", "1080"]
        btns = [types.InlineKeyboardButton(f"🎬 {q}p", callback_data=f"q_{q}") for q in qs]
        markup.add(*btns)
        markup.add(types.InlineKeyboardButton("🎵 MP3 Audio", callback_data="q_mp3"))
        bot.send_message(message.chat.id, "🎥 የቪዲዮ ጥራት ይምረጡ ወይም በኦዲዮ ያውርዱ:", reply_markup=markup)
    else:
        status = bot.send_message(message.chat.id, "⏳ ቪዲዮው እየተዘጋጀ ነው (TikTok/FB/IG)...")
        download_logic(message.chat.id, url, "best", status.message_id)

# --- 4. Callback Handlers ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "check_sub":
        if is_subscribed(call.from_user.id):
            bot.edit_message_text("✅ ተረጋግጧል! አሁን ሊንክ መላክ ይችላሉ።", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ አልተቀላቀሉም! እባክዎ መጀመሪያ ቻናሉን ይቀላቀሉ።", show_alert=True)
            
    elif call.data.startswith("q_"):
        url = user_links.get(call.message.chat.id)
        q = call.data.replace("q_", "")
        if not url: return
        bot.edit_message_text(f"⏳ {q} በጥራት እየተዘጋጀ ነው...", call.message.chat.id, call.message.message_id)
        # 1080p እንዲሰራ ቪዲዮና ኦዲዮ እንዲዋሃድ እናደርጋለን
        fmt = "bestaudio/best" if q == "mp3" else f"bestvideo[height<={q}]+bestaudio/best"
        download_logic(call.message.chat.id, url, fmt, call.message.message_id, is_mp3=(q=="mp3"))

# --- 5. Core Download Logic (Optimized for Docker/Railway) ---
def download_logic(chat_id, url, fmt, status_msg_id, is_mp3=False):
    ext = "mp3" if is_mp3 else "mp4"
    file_name = f"video_{int(time.time())}.{ext}"
    
    ydl_opts = {
        'format': fmt,
        'outtmpl': file_name,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4' if not is_mp3 else None,
    }
    
    if is_mp3:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                if is_mp3:
                    bot.send_audio(chat_id, f, caption=f"🎵 @{bot.get_me().username}")
                else:
                    bot.send_video(chat_id, f, caption=f"✅ @{bot.get_me().username}")
            os.remove(file_name)
            bot.delete_message(chat_id, status_msg_id)
        else:
            bot.send_message(chat_id, "❌ ስህተት፡ ፋይሉ አልተገኘም።")
    except Exception as e:
        bot.send_message(chat_id, "❌ ስህተት ተፈጥሯል። ሊንኩን ወይም የቦቱን አቅም ያረጋግጡ።")
        if os.path.exists(file_name): os.remove(file_name)

# --- Start Polling ---
if __name__ == "__main__":
    print("🚀 ቦቱ በ Railway ላይ ስራ ጀምሯል...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=40)
        except Exception as e:
            print(f"📡 የግንኙነት ስህተት: {e}. ከ5 ሰከንድ በኋላ እንደገና ይሞከራል...")
            time.sleep(5)
