"""
Guruch Bozori — Telegram Bot
"""

import telebot
from telebot import types
import json, os, requests, base64

BOT_TOKEN        = "8357406972:AAHJ0lH0SJuFbwnvRMKNrBd6O0S9Y3kzGTQ"
CHANNEL_USERNAME = "@guruch_savdo_n1"
MINI_APP_URL     = "https://amirbekataxanov-commits.github.io/Guruch-savdo/"
ADMIN_ID         = 837423714

# GitHub sozlamalari
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
GITHUB_OWNER = "amirbekataxanov-commits"
GITHUB_REPO  = "Guruch-savdo"
GITHUB_FILE  = "products.json"
GITHUB_API   = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"

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

# ── GitHub funksiyalari ─────────────────────────────────────
def get_products():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(GITHUB_API, headers=headers)
    if res.ok:
        data = res.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    return [], None

def save_product_to_github(product):
    try:
        products, sha = get_products()
        if sha is None:
            return False
        products.insert(0, product)
        content = base64.b64encode(
            json.dumps(products, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("utf-8")
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
        body = {"message": "Yangi e'lon qo'shildi", "content": content, "sha": sha}
        res = requests.put(GITHUB_API, headers=headers, json=body)
        return res.ok
    except Exception as e:
        print(f"GitHub save error: {e}")
        return False

def delete_product_from_github(product_id):
    try:
        products, sha = get_products()
        if sha is None:
            return False
        products = [p for p in products if str(p.get("id")) != str(product_id)]
        content = base64.b64encode(
            json.dumps(products, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("utf-8")
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
        body = {"message": "E'lon o'chirildi", "content": content, "sha": sha}
        res = requests.put(GITHUB_API, headers=headers, json=body)
        return res.ok
    except Exception as e:
        print(f"GitHub delete error: {e}")
        return False

# ── Helpers ─────────────────────────────────────────────────
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

# ── /start ──────────────────────────────────────────────────
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
            "🌾 *Guruch Bozori*ga xush kelibsiz!\n\nDavom etish uchun avval kanalga obuna bo'ling 👇",
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

# ── WebApp ma'lumot ─────────────────────────────────────────
@bot.message_handler(content_types=["web_app_data"])
def web_app_data(msg):
    try:
        d = json.loads(msg.web_app_data.data)
        action = d.get("action")
        users = load_users()
        u = users.get(str(msg.from_user.id), {})

        if action == "new_product":
            product = d.get("product", {})
            ok = save_product_to_github(product)
            if ok:
                bot.send_message(msg.chat.id, "✅ E'lon muvaffaqiyatli saqlandi!")
                bot.send_message(ADMIN_ID,
                    f"🌾 *Yangi e'lon!*\n\n"
                    f"🏷 Nav: *{product.get('name','')}*\n"
                    f"⚖️ {product.get('amount','')} tonna\n"
                    f"💰 {product.get('price','')} so'm/kg\n"
                    f"📍 {product.get('address','')}\n"
                    f"👤 {product.get('seller','')} — {product.get('phone','')}\n\n"
                    f"Yuborgan: {u.get('name', 'Noma\\'lum')}",
                    parse_mode="Markdown")
            else:
                bot.send_message(msg.chat.id, "❌ Saqlashda xato yuz berdi.")

        elif action == "delete_product":
            product_id = d.get("id")
            allowed = load_allowed()
            if msg.from_user.id in allowed:
                ok = delete_product_from_github(product_id)
                if ok:
                    bot.send_message(msg.chat.id, "🗑️ E'lon o'chirildi!")
                else:
                    bot.send_message(msg.chat.id, "❌ O'chirishda xato.")
            else:
                bot.send_message(msg.chat.id, "🔒 Ruxsat yo'q.")

    except Exception as e:
        print(f"WebApp error: {e}")

# ── Admin buyruqlar ─────────────────────────────────────────
@bot.message_handler(commands=["allow"])
def allow_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "Foydalanish: `/allow 123456789`", parse_mode="Markdown")
        return
    target = parts[1].lstrip("@")
    allowed = load_allowed()
    if target.isdigit():
        uid = int(target)
        if uid not in allowed:
            allowed.append(uid)
            save_allowed(allowed)
        try:
            bot.send_message(uid, "✅ Sizga e'lon berish ruxsati berildi! 🌾")
        except:
            pass
        bot.send_message(msg.chat.id, f"✅ {uid} ruxsat ro'yxatiga qo'shildi.")
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
            bot.send_message(msg.chat.id, f"✅ @{target} ruxsat ro'yxatiga qo'shildi.")
        else:
            bot.send_message(msg.chat.id, f"❌ @{target} topilmadi.")

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
        bot.send_message(msg.chat.id, f"🚫 {uid} ruxsatdan chiqarildi.")
    else:
        bot.send_message(msg.chat.id, "Bu foydalanuvchi ro'yxatda yo'q.")

@bot.message_handler(commands=["allowed"])
def list_allowed(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    allowed = load_allowed()
    text = "📋 Ruxsat berilganlar:\n\n" + "\n".join([f"• `{uid}`" for uid in allowed])
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["users"])
def show_users(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    users = load_users()
    reg = [u for u in users.values() if u.get("step") == "registered"]
    bot.send_message(msg.chat.id,
        f"📊 Statistika\n\n"
        f"👥 Jami: {len(users)}\n"
        f"✅ Ro'yxatdan o'tgan: {len(reg)}\n"
        f"🔓 Ruxsat berilgan: {len(load_allowed())}")

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
                f"🆕 Yangi foydalanuvchi!\n"
                f"👤 {name}\n📱 {u.get('phone','')}\n"
                f"🔗 @{u.get('username','yoq')}\n🆔 {uid}")
        except:
            pass
        open_app(msg.chat.id)
        return
    if not is_registered(uid):
        bot.send_message(msg.chat.id, "Iltimos, /start bosing.")

if __name__ == "__main__":
    print("🌾 Guruch Bozori boti ishga tushdi!")
    bot.infinity_polling()
