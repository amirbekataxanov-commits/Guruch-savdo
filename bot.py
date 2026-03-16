"""
Guruch Bozori — Telegram Bot
==============================
O'rnatish:  pip install pyTelegramBotAPI
Ishlatish:  python bot.py
"""

import telebot
from telebot import types
import json, os

# ============================================================
# SOZLAMALAR — Railway Variables dan avtomatik o'qiladi
# ============================================================
BOT_TOKEN        = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@your_channel")
MINI_APP_URL     = os.getenv("MINI_APP_URL", "https://YOUR_USERNAME.github.io/guruch-bozori/")
ADMIN_ID         = int(os.getenv("ADMIN_ID", "123456789"))
# ============================================================

bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE   = "users.json"
ALLOWED_FILE = "allowed.json"

# ── helpers ────────────────────────────────────────────────
def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():    return load_json(USERS_FILE,   {})
def save_users(d):   save_json(USERS_FILE,   d)
def load_allowed():  return load_json(ALLOWED_FILE, [ADMIN_ID])
def save_allowed(d): save_json(ALLOWED_FILE, d)

def is_subscribed(uid):
    try:
        m = bot.get_chat_member(CHANNEL_USERNAME, uid)
        return m.status in ("member","administrator","creator")
    except: return False

def is_registered(uid):
    return str(uid) in load_users()

# ── /start ─────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id

    if not is_subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Kanalga obuna bo'lish",
               url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"))
        kb.add(types.InlineKeyboardButton("✅ Obuna bo'ldim",
               callback_data="check_sub"))
        bot.send_message(uid,
            "🌾 *Guruch Bozori*ga xush kelibsiz!\n\n"
            "Davom etish uchun avval kanalga obuna bo'ling 👇",
            parse_mode="Markdown", reply_markup=kb)
        return

    if is_registered(uid): return open_app(uid)
    ask_phone(uid)

# ── Obuna callback ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if is_subscribed(uid):
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        if is_registered(uid): open_app(uid)
        else: ask_phone(uid)
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmagansiz!", show_alert=True)

# ── Ro'yxatdan o'tish ──────────────────────────────────────
def ask_phone(chat_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    bot.send_message(chat_id, "📱 Telefon raqamingizni yuboring:", reply_markup=kb)

def ask_name(chat_id):
    bot.send_message(chat_id, "👤 Ism va familiyangizni kiriting:\n_Masalan: Abdulla Yusupov_",
                     parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

def open_app(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🌾 Guruch Bozorini ochish",
           web_app=types.WebAppInfo(url=MINI_APP_URL)))
    bot.send_message(chat_id,
        "✅ *Muvaffaqiyatli ro'yxatdan o'tdingiz!*\n\nGuruch bozorini ochish uchun 👇",
        parse_mode="Markdown", reply_markup=kb)

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

# ── WebApp ma'lumot ─────────────────────────────────────────
@bot.message_handler(content_types=["web_app_data"])
def web_app_data(msg):
    try:
        d = json.loads(msg.web_app_data.data)
        if d.get("action") == "new_product":
            p = d
            users = load_users()
            u = users.get(str(msg.from_user.id), {})
            bot.send_message(ADMIN_ID,
                f"🌾 *Yangi e'lon!*\n\n"
                f"🏷 Nav: *{p['name']}*\n"
                f"⚖️ {p['amount']} tonna\n"
                f"💰 {int(p['price']):,} so'm/kg\n"
                f"📍 {p['address']}\n"
                f"👤 {p['seller']} — {p['phone']}\n\n"
                f"E'lon bergan: {u.get('name','Noma\\'lum')}",
                parse_mode="Markdown")
    except Exception as e:
        print("WebApp error:", e)

# ── ADMIN: /allow va /deny ──────────────────────────────────
@bot.message_handler(commands=["allow"])
def allow_user(msg):
    """
    Foydalanish:
      /allow 123456789
      /allow @username  (username bo'yicha qidiradi)
    """
    if msg.from_user.id != ADMIN_ID:
        return

    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id,
            "ℹ️ Foydalanish:\n`/allow 123456789`\n`/allow @username`",
            parse_mode="Markdown")
        return

    target = parts[1].lstrip("@")
    allowed = load_allowed()

    # ID bo'yicha
    if target.isdigit():
        uid = int(target)
        if uid not in allowed:
            allowed.append(uid)
            save_allowed(allowed)
        # Foydalanuvchiga xabar
        try:
            bot.send_message(uid,
                "✅ *Tabriklaymiz!*\n\nSizga e'lon berish ruxsati berildi.\n"
                "Endi Guruch Bozorida o'z mahsulotingizni joylashtira olasiz! 🌾",
                parse_mode="Markdown")
        except: pass
        bot.send_message(msg.chat.id, f"✅ `{uid}` ruxsat ro'yxatiga qo'shildi.", parse_mode="Markdown")

    # Username bo'yicha — foydalanuvchi avval botga yozgan bo'lishi kerak
    else:
        users = load_users()
        found = next((uid for uid, u in users.items() if u.get("username") == target), None)
        if found:
            uid = int(found)
            if uid not in allowed:
                allowed.append(uid)
                save_allowed(allowed)
            try:
                bot.send_message(uid,
                    "✅ *Tabriklaymiz!*\n\nSizga e'lon berish ruxsati berildi. 🌾",
                    parse_mode="Markdown")
            except: pass
            bot.send_message(msg.chat.id, f"✅ @{target} ruxsat ro'yxatiga qo'shildi.")
        else:
            bot.send_message(msg.chat.id,
                f"❌ @{target} topilmadi.\nFoydalanuvchi avval botga /start bosishi kerak.\n"
                f"Yoki to'g'ridan ID bilan yuboring: `/allow 123456789`",
                parse_mode="Markdown")


@bot.message_handler(commands=["deny"])
def deny_user(msg):
    """Ruxsatni olib qo'yish: /deny 123456789"""
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.send_message(msg.chat.id, "ℹ️ Foydalanish: `/deny 123456789`", parse_mode="Markdown")
        return
    uid = int(parts[1])
    allowed = load_allowed()
    if uid in allowed:
        allowed.remove(uid)
        save_allowed(allowed)
        bot.send_message(msg.chat.id, f"🚫 `{uid}` ruxsat ro'yxatidan o'chirildi.", parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, f"ℹ️ `{uid}` ro'yxatda yo'q edi.", parse_mode="Markdown")


@bot.message_handler(commands=["allowed"])
def list_allowed(msg):
    """Ruxsat berilganlar ro'yxati: /allowed"""
    if msg.from_user.id != ADMIN_ID: return
    allowed = load_allowed()
    text = "📋 *Ruxsat berilgan foydalanuvchilar:*\n\n"
    for uid in allowed:
        text += f"• `{uid}`\n"
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=["users"])
def show_users(msg):
    if msg.from_user.id != ADMIN_ID: return
    users = load_users()
    reg = [u for u in users.values() if u.get("step") == "registered"]
    bot.send_message(msg.chat.id,
        f"📊 *Statistika*\n\n"
        f"👥 Jami: {len(users)}\n"
        f"✅ Ro'yxatdan o'tgan: {len(reg)}\n"
        f"🔓 Ruxsat berilgan: {len(load_allowed())}",
        parse_mode="Markdown")


# ── Matn xabarlar ───────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    uid = msg.from_user.id
    users = load_users()
    u = users.get(str(uid))

    if u and u.get("step") == "waiting_name":
        name = msg.text.strip()
        if len(name) < 3:
            bot.send_message(msg.chat.id, "⚠️ To'liq ism-familiyangizni kiriting.")
            return
        u["name"] = name
        u["step"] = "registered"
        save_users(users)
        try:
            bot.send_message(ADMIN_ID,
                f"🆕 *Yangi foydalanuvchi!*\n👤 {name}\n📱 {u['phone']}\n🔗 @{u.get('username','—')}\n🆔 `{uid}`",
                parse_mode="Markdown")
        except: pass
        open_app(msg.chat.id)
        return

    if not is_registered(uid):
        bot.send_message(msg.chat.id, "Iltimos, /start bosing.")


if __name__ == "__main__":
    print("🌾 Guruch Bozori boti ishga tushdi!")
    print(f"📢 Kanal: {CHANNEL_USERNAME}")
    print(f"🌐 Mini App: {MINI_APP_URL}")
    print("\nAdmin buyruqlar:")
    print("  /allow <id|@username> — ruxsat berish")
    print("  /deny <id>            — ruxsatni olish")
    print("  /allowed              — ro'yxatni ko'rish")
    print("  /users                — statistika")
    bot.infinity_polling()
