"""
Guruch Bozori — Telegram Bot
"""

import telebot
from telebot import types
import json, os

BOT_TOKEN        = "8357406972:AAHJ0lH0SJuFbwnvRMKNrBd6O0S9Y3kzGTQ"
CHANNEL_USERNAME = "@guruch_savdo_n1"
MINI_APP_URL     = "https://amirbekataxanov-commits.github.io/Guruch-savdo/"
ADMIN_ID         = 837423714

bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE   = "users.json"
ALLOWED_FILE = "allowed.json"

def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():    return load_json(USERS_FILE, {})
def save_users(d):   save_json(USERS_FILE, d)
def load_allowed():  return load_json(ALLOWED_FILE, [ADMIN_ID])
def save_allowed(d): save_json(ALLOWED_FILE, d)

def is_subscribed(uid):
    try:
        m = bot.get_chat_member(CHANNEL_USERNAME, uid)
        return m.status in ("member", "administrator", "creator")
    except:
        return False

def is_registered(uid):
    return str(uid) in load_users()

def ask_phone(chat_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    bot.send_message(chat_id, "📱 Telefon raqamingizni yuboring:", reply_markup=kb)

def ask_name(chat_id):
    bot.send_message(chat_id,
        "👤 Ism va familiyangizni kiriting:\n_Masalan: Abdulla Yusupov_",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove())

def open_app(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "🌾 Guruch Bozorini ochish",
        web_app=types.WebAppInfo(url=MINI_APP_URL)
    ))
    bot.send_message(chat_id,
        "✅ *Muvaffaqiyatli ro'yxatdan o'tdingiz!*\n\nGuruch bozorini ochish uchun 👇",
        parse_mode="Markdown",
        reply_markup=kb)

@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    if not is_subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "📢 Kanalga obuna bo'lish",
            url="https://t.me/guruch_savdo_n1"
        ))
        kb.add(types.InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_sub"))
        bot.send_message(uid,
            "🌾 *Guruch Bozori*ga xush kelibsiz!\n\n"
            "Davom etish uchun avval kanalga obuna bo'ling 👇",
            parse_mode="Markdown", reply_markup=kb)
        return
    if is_registered(uid):
        open_app(uid)
    else:
        ask_phone(uid)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if is_subscribed(uid):
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        if is_registered(uid):
            open_app(uid)
        else:
            ask_phone(uid)
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmagansiz!", show_alert=True)

@bot.message_handler(content_types=["contact"])
def get_contact(msg):
    uid = msg.from_user.id
    users = load_users()
    users[str(uid)] = {
        "phone": msg.contact.phone_number,
        "name": None,
        "username": msg.from_user.username,
        "step": "waiting_name"
    }
    save_users(users)
    ask_name(msg.chat.id)

@bot.message_handler(content_types=["web_app_data"])
def web_app_data(msg):
    try:
        d = json.loads(msg.web_app_data.data)
        if d.get("action") == "new_product":
            p = d
            users = load_users()
            u = users.get(str(msg.from_user.id), {})
            bot.send_message(ADMIN_ID,
                "🌾 *Yangi e'lon!*\n\n"
                "🏷 Nav: *" + str(p.get("name","")) + "*\n"
                "⚖️ " + str(p.get("amount","")) + " tonna\n"
                "💰 " + str(p.get("price","")) + " so'm/kg\n"
                "📍 " + str(p.get("address","")) + "\n"
                "👤 " + str(p.get("seller","")) + " — " + str(p.get("phone","")) + "\n\n"
                "E'lon bergan: " + str(u.get("name", "Noma'lum")),
                parse_mode="Markdown")
    except Exception as e:
        print("WebApp error:", e)

@bot.message_handler(commands=["allow"])
def allow_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id,
            "Foydalanish:\n`/allow 123456789`\n`/allow @username`",
            parse_mode="Markdown")
        return
    target = parts[1].lstrip("@")
    allowed = load_allowed()
    if target.isdigit():
        uid = int(target)
        if uid not in allowed:
            allowed.append(uid)
            save_allowed(allowed)
        try:
            bot.send_message(uid,
                "✅ Sizga e'lon berish ruxsati berildi! 🌾",
                parse_mode="Markdown")
        except:
            pass
        bot.send_message(msg.chat.id, "✅ Ruxsat berildi: " + str(uid))
    else:
        users = load_users()
        found = next((u for u, v in users.items() if v.get("username") == target), None)
        if found:
            uid = int(found)
            if uid not in allowed:
                allowed.append(uid)
                save_allowed(allowed)
            try:
                bot.send_message(uid, "✅ Sizga e'lon berish ruxsati berildi! 🌾")
            except:
                pass
            bot.send_message(msg.chat.id, "✅ @" + target + " ruxsat ro'yxatiga qo'shildi.")
        else:
            bot.send_message(msg.chat.id,
                "❌ @" + target + " topilmadi. Avval /start bossin yoki ID bilan yuboring.")

@bot.message_handler(commands=["deny"])
def deny_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.send_message(msg.chat.id, "Foydalanish: `/deny 123456789`", parse_mode="Markdown")
        return
    uid = int(parts[1])
    allowed = load_allowed()
    if uid in allowed:
        allowed.remove(uid)
        save_allowed(allowed)
        bot.send_message(msg.chat.id, "🚫 Ruxsat olib qo'yildi: " + str(uid))
    else:
        bot.send_message(msg.chat.id, "Bu foydalanuvchi ro'yxatda yo'q edi.")

@bot.message_handler(commands=["allowed"])
def list_allowed(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    allowed = load_allowed()
    text = "📋 Ruxsat berilganlar:\n\n"
    for uid in allowed:
        text += "• " + str(uid) + "\n"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(commands=["users"])
def show_users(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    users = load_users()
    reg = [u for u in users.values() if u.get("step") == "registered"]
    bot.send_message(msg.chat.id,
        "📊 Statistika\n\n"
        "👥 Jami: " + str(len(users)) + "\n"
        "✅ Royxatdan otgan: " + str(len(reg)) + "\n"
        "🔓 Ruxsat berilgan: " + str(len(load_allowed())))

@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    uid = msg.from_user.id
    users = load_users()
    u = users.get(str(uid))
    if u and u.get("step") == "waiting_name":
        name = msg.text.strip()
        if len(name) < 3:
            bot.send_message(msg.chat.id, "⚠️ Toʻliq ism-familiyangizni kiriting.")
            return
        u["name"] = name
        u["step"] = "registered"
        save_users(users)
        try:
            bot.send_message(ADMIN_ID,
                "🆕 Yangi foydalanuvchi!\n"
                "👤 " + name + "\n"
                "📱 " + str(u.get("phone","")) + "\n"
                "🔗 @" + str(u.get("username","yoq")) + "\n"
                "🆔 " + str(uid))
        except:
            pass
        open_app(msg.chat.id)
        return
    if not is_registered(uid):
        bot.send_message(msg.chat.id, "Iltimos, /start bosing.")

if __name__ == "__main__":
    print("🌾 Guruch Bozori boti ishga tushdi!")
    bot.infinity_polling()
