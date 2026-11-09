import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "9027384359:AAGM2ny7SD8PxTGurVTnjFoawTDO0ue9jDo"
ADMIN_CHAT_ID = 9146749832

conn = sqlite3.connect('patients.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        name TEXT,
        username TEXT,
        issue TEXT,
        age TEXT,
        gender TEXT,
        heredity TEXT,
        stress TEXT,
        smoke TEXT,
        alcohol TEXT,
        photo_id TEXT,
        package TEXT,
        full_name TEXT,
        last_name TEXT,
        address TEXT,
        phone TEXT,
        receipt_id TEXT,
        date TEXT,
        history TEXT
    )
''')
conn.commit()

# ========== ذخیره تاریخچه چت ==========
def add_history(chat_id, text):
    cursor.execute("SELECT history FROM patients WHERE chat_id = ? ORDER BY id DESC LIMIT 1", (chat_id,))
    row = cursor.fetchone()
    if row:
        new_hist = (row[0] or '') + text + "\n"
        cursor.execute("UPDATE patients SET history = ? WHERE chat_id = ?", (new_hist, chat_id))
    else:
        cursor.execute("INSERT INTO patients (chat_id, history, date) VALUES (?, ?, ?)",
                       (chat_id, text + "\n", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

def get_history(chat_id):
    cursor.execute("SELECT history FROM patients WHERE chat_id = ? ORDER BY id DESC LIMIT 1", (chat_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else "تاریخچه‌ای موجود نیست."

# ========== شروع ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("🔹 ریزش مو", callback_data='issue_hair')],
        [InlineKeyboardButton("🔹 عدم رویش ریش و سیبیل", callback_data='issue_beard')],
    ]
    await update.message.reply_text(
        "سلام و عرض ادب به کلینیک رویش سنتر خوش آمدید\n\n"
        "لطفاً مشکل خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    add_history(update.message.from_user.id, "کاربر /start زد.")

# ========== انتخاب مشکل ==========
async def issue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        return
    ud = context.user_data
    if query.data == 'issue_hair':
        ud['issue'] = 'hair'
        await query.edit_message_text("سن خود را وارد کنید (فقط عدد):")
    elif query.data == 'issue_beard':
        ud['issue'] = 'beard'
        await query.edit_message_text("سن خود را وارد کنید (فقط عدد):")
    add_history(update.effective_user.id, f"مشکل انتخاب شد: {'ریزش مو' if ud['issue'] == 'hair' else 'ریش و سیبیل'}")

# ========== دریافت سن ==========
async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud['age'] = update.message.text
    add_history(update.message.from_user.id, f"سن: {update.message.text}")
    await update.message.reply_text("جنسیت خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("مرد", callback_data='gender_male')],
        [InlineKeyboardButton("زن", callback_data='gender_female')],
    ]))

# ========== دکمه‌های پرسش‌نامه ==========
async def questionnaire_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        return
    data = query.data
    ud = context.user_data
    uid = update.effective_user.id

    if data.startswith('gender_'):
        ud['gender'] = 'مرد' if data == 'gender_male' else 'زن'
        add_history(uid, f"جنسیت: {ud['gender']}")
        await query.edit_message_text("آیا سابقه ارثی (در خانواده) دارید؟", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله", callback_data='heredity_yes')],
            [InlineKeyboardButton("خیر", callback_data='heredity_no')],
        ]))
    elif data.startswith('heredity_'):
        ud['heredity'] = 'بله' if data == 'heredity_yes' else 'خیر'
        add_history(uid, f"سابقه ارثی: {ud['heredity']}")
        await query.edit_message_text("وضعیت استرس و اضطراب شما:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("کم", callback_data='stress_low')],
            [InlineKeyboardButton("متوسط", callback_data='stress_mid')],
            [InlineKeyboardButton("زیاد", callback_data='stress_high')],
        ]))
    elif data.startswith('stress_'):
        ud['stress'] = {'stress_low': 'کم', 'stress_mid': 'متوسط', 'stress_high': 'زیاد'}[data]
        add_history(uid, f"استرس: {ud['stress']}")
        await query.edit_message_text("آیا از دخانیات استفاده می‌کنید؟", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله", callback_data='smoke_yes')],
            [InlineKeyboardButton("خیر", callback_data='smoke_no')],
        ]))
    elif data.startswith('smoke_'):
        ud['smoke'] = 'بله' if data == 'smoke_yes' else 'خیر'
        add_history(uid, f"دخانیات: {ud['smoke']}")
        await query.edit_message_text("آیا از مشروبات الکلی استفاده می‌کنید؟", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله", callback_data='alcohol_yes')],
            [InlineKeyboardButton("خیر", callback_data='alcohol_no')],
        ]))
    elif data.startswith('alcohol_'):
        ud['alcohol'] = 'بله' if data == 'alcohol_yes' else 'خیر'
        add_history(uid, f"مشروبات: {ud['alcohol']}")
        await query.edit_message_text("لطفاً یک عکس واضح از ناحیه مورد نظر ارسال کنید.")

# ========== دریافت عکس (مشاوره یا فیش) ==========
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1]
    ud = context.user_data

    # ۱. اگر منتظر فیش واریزی هستیم:
    if ud.get('awaiting_receipt'):
        ud['awaiting_receipt'] = False
        add_history(user.id, "فیش واریزی ارسال شد.")
        
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo.file_id,
            caption=(
                f"🧾 فیش واریزی جدید ثبت شد!\n\n"
                f"👤 نام درمانجو: {user.first_name} {user.last_name or ''}\n"
                f"🆔 یوزرنیم: @{user.username or 'ندارد'} | Chat ID: {user.id}\n\n"
                f"📦 پکیج انتخابی: {ud.get('package', 'نامشخص')}\n"
                f"📝 نام گیرنده: {ud.get('full_name', '-')} {ud.get('last_name', '-')}\n"
                f"📍 آدرس: {ud.get('address', '-')}\n"
                f"📞 شماره تماس: {ud.get('phone', '-')}"
            )
        )

        history = get_history(user.id)
        filename = f"history_{user.id}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"تاریخچه چت درمانجو: {user.first_name} (@{user.username or 'ندارد'}) | chat_id: {user.id}\n")
            f.write("=" * 40 + "\n")
            f.write(history)
        with open(filename, 'rb') as f:
            await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=f, filename=filename)

        await update.message.reply_text(
            "✅ سفارش شما ثبت شد.\n"
            "منتظر تأییدیه و تماس پشتیبانی باشید؛ تا دقایقی دیگر با شما تماس گرفته می‌شود."
        )
        return

    # ۲. اگر منتظر عکس مشاوره هستیم:
    caption = update.message.caption or ""
    if 'age' not in ud or 'alcohol' not in ud:
        await update.message.reply_text("لطفاً ابتدا /start بزنید و مراحل را طی کنید.")
        return

    cursor.execute(
        "INSERT INTO patients (chat_id, name, username, issue, age, gender, heredity, stress, smoke, alcohol, photo_id, date, history) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user.id, f"{user.first_name} {user.last_name or ''}", user.username or '',
         ud.get('issue'), ud.get('age'), ud.get('gender'), ud.get('heredity'),
         ud.get('stress'), ud.get('smoke'), ud.get('alcohol'), photo.file_id,
         datetime.now().strftime("%Y-%m-%d %H:%M"), "")
    )
    conn.commit()
    add_history(user.id, "عکس ناحیه (مشاوره) ارسال شد.")

    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo.file_id,
        caption=(
            f"📥 عکس جدید از درمانجو\n"
            f"👤 {user.first_name} {user.last_name or ''}\n"
            f"🆔 @{user.username or 'ندارد'} | {user.id}\n"
            f"🔹 مشکل: {'ریزش مو' if ud.get('issue') == 'hair' else 'ریش و سیبیل'}\n"
            f"🎂 سن: {ud.get('age')}\n"
            f"👫 جنسیت: {ud.get('gender')}\n"
            f"🧬 ارثی: {ud.get('heredity')}\n"
            f"😰 استرس: {ud.get('stress')}\n"
            f"🚬 دخانیات: {ud.get('smoke')}\n"
            f"🍷 مشروبات: {ud.get('alcohol')}\n"
            f"📝 توضیح: {caption}\n\n"
            f"💡 برای ارسال مشاوره، روی همین پیام ریپلای کنید و ویس بفرستید.\n"
            f"⚠️ وقتی مشاوره تمام شد، در چت با ربات دستور /done را بزنید."
        )
    )

    await update.message.reply_text(
        "✅ اطلاعات شما دریافت شد.\n"
        "مشاوره توسط پزشک به زودی همین‌جا برای شما ارسال می‌شود.\n"
        "لطفاً منتظر بمانید."
    )

# ========== ریپلای ادمین (فقط ارسال ویس/متن بدون پرسیدن سوال) ==========
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    replied = msg.reply_to_message
    text = replied.caption or replied.text or ""
    target_chat_id = None
    for line in text.split("\n"):
        if "|" in line and line.strip().startswith("🆔"):
            try:
                target_chat_id = int(line.split("|")[1].split("Chat ID:")[-1].strip())
            except Exception:
                pass

    if not target_chat_id:
        await msg.reply_text("⚠️ chat_id پیدا نشد. مطمئن شو روی پیام فورواردشده ریپلای کردی.")
        return

    try:
        if msg.voice:
            await context.bot.send_voice(chat_id=target_chat_id, voice=msg.voice.file_id)
        elif msg.photo:
            await context.bot.send_photo(chat_id=target_chat_id, photo=msg.photo[-1].file_id, caption=msg.caption or "")
        elif msg.text:
            await context.bot.send_message(chat_id=target_chat_id, text=msg.text)
        
        add_history(target_chat_id, "پاسخ/ویس پزشک ارسال شد.")
        
        # ذخیره آخرین درمانجو برای دستور done
        context.user_data['last_patient_id'] = target_chat_id
        
        await msg.reply_text("✅ ارسال شد. (برای اتمام مشاوره و پرسیدن سوال، دستور /done را بزنید)")
    except Exception as e:
        await msg.reply_text(f"⚠️ خطا: {e}")

# ========== دستور /done برای اتمام مشاوره ==========
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_CHAT_ID:
        return
    
    target_chat_id = context.user_data.get('last_patient_id')
    if not target_chat_id:
        await update.message.reply_text("⚠️ هنوز به کسی پیامی ارسال نکردی که بخوای مشاوره‌ش رو تموم کنی. اول روی پیام درمانجو ریپلای کن و ویس بفرست.")
        return
        
    try:
        await context.bot.send_message(
            chat_id=target_chat_id,
            text="آیا سوال دیگری دارید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("بله", callback_data='has_question_yes')],
                [InlineKeyboardButton("خیر", callback_data='has_question_no')],
            ])
        )
        await update.message.reply_text("✅ سوال برای درمانجو ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال به درمانجو: {e}")

# ========== سوال دارد یا نه ==========
async def question_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        return
    ud = context.user_data
    data = query.data

    if data == 'has_question_yes':
        await query.edit_message_text("لطفاً سوال خود را بنویسید:")
        ud['awaiting_question'] = True
    elif data == 'has_question_no':
        await query.edit_message_text("در حال ارسال تعرفه پکیج‌ها...")
        await send_packages(update, context)

# ========== دریافت سوال درمانجو ==========
async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    ud = context.user_data
    if ud.get('awaiting_question'):
        ud['awaiting_question'] = False
        text = update.message.text
        add_history(user.id, f"سوال: {text}")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"❓ سوال جدید از درمانجو\n"
                f"👤 {user.first_name} {user.last_name or ''}\n"
                f"🆔 @{user.username or 'ندارد'} | {user.id}\n"
                f"📝 سوال: {text}\n\n"
                f"💡 برای پاسخ، روی همین پیام ریپلای کنید."
            )
        )
        await update.message.reply_text("✅ سوال شما دریافت شد. پزشک به زودی پاسخ می‌دهد.")
        return True
    return False

# ========== ارسال تعرفه پکیج‌ها ==========
async def send_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    issue = ud.get('issue', 'hair')
    uid = update.effective_user.id

    if issue == 'beard':
        text = (
            "🧔 تعرفه پکیج‌های تخصصی مراقبت و تقویت ریش و سبیل\n\n"
            "✨ پکیج پایه | BASIC — ۱,۸۵۷,۰۰۰ تومان\n"
            "✅ کمک به تقویت ریشه و فولیکول‌ها\n✅ بهبود ضخامت تارهای ریش\n✅ مراقبت و آبرسانی پوست\n\n"
            "⭐ پکیج پیشرفته | ADVANCED — ۲,۹۵۴,۰۰۰ تومان\n"
            "✅ مراقبت چندمنظوره\n✅ تقویت فولیکول‌ها\n✅ تعادل چربی و PH پوست\n✅ نرم‌تر شدن تارهای زبر\n\n"
            "💎 پکیج رویال VIP | ROYAL — ۳,۴۶۷,۰۰۰ تومان\n"
            "✅ برنامه جامع مراقبتی\n✅ تقویت فولیکول و سلامت پوست\n✅ پشتیبانی ویژه\n\n"
            "لطفاً پکیج مورد نظر خود را انتخاب کنید:"
        )
        kb = [
            [InlineKeyboardButton("پایه | BASIC", callback_data='pkg_beard_basic')],
            [InlineKeyboardButton("پیشرفته | ADVANCED", callback_data='pkg_beard_advanced')],
            [InlineKeyboardButton("رویال VIP | ROYAL", callback_data='pkg_beard_royal')],
        ]
    else:
        text = (
            "💇 تعرفه پکیج‌های تخصصی مراقبت و تقویت مو\n\n"
            "✨ پکیج پایه | BASIC — ۳,۸۰۰,۰۰۰ تومان\n"
            "✅ کنترل ریزش و تقویت ریشه\n✅ بهبود فولیکول‌های ضعیف\n✅ افزایش ضخامت تارها\n\n"
            "⭐ پکیج پیشرفته | ADVANCED — ۵,۴۰۰,۰۰۰ تومان\n"
            "✅ ترکیب کامل‌تر محصولات\n✅ تقویت فولیکول و سلامت ریشه\n✅ برنامه منظم و هدفمند\n\n"
            "💎 پکیج رویال VIP | ROYAL — ۸,۴۰۰,۰۰۰ تومان\n"
            "✅ برنامه جامع و چندمنظوره\n✅ حجم بیشتر و ارزش اقتصادی\n✅ پشتیبانی اختصاصی\n\n"
            "لطفاً پکیج مورد نظر خود را انتخاب کنید:"
        )
        kb = [
            [InlineKeyboardButton("پایه | BASIC", callback_data='pkg_hair_basic')],
            [InlineKeyboardButton("پیشرفته | ADVANCED", callback_data='pkg_hair_advanced')],
            [InlineKeyboardButton("رویال VIP | ROYAL", callback_data='pkg_hair_royal')],
        ]

    add_history(uid, "تعرفه پکیج‌ها ارسال شد.")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

# ========== انتخاب پکیج ==========
async def package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        return
    ud = context.user_data
    data = query.data
    pkg_names = {
        'pkg_beard_basic': 'ریش - پایه BASIC', 'pkg_beard_advanced': 'ریش - پیشرفته ADVANCED', 'pkg_beard_royal': 'ریش - رویال ROYAL',
        'pkg_hair_basic': 'مو - پایه BASIC', 'pkg_hair_advanced': 'مو - پیشرفته ADVANCED', 'pkg_hair_royal': 'مو - رویال ROYAL',
    }
    ud['package'] = pkg_names.get(data, data)
    ud['form_step'] = 'full_name'
    add_history(update.effective_user.id, f"پکیج انتخاب شد: {ud['package']}")
    
    user = update.effective_user
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            f"📦 انتخاب پکیج جدید:\n"
            f"👤 {user.first_name} {user.last_name or ''} (@{user.username or 'ندارد'})\n"
            f"🆔 Chat ID: {user.id}\n"
            f"✅ پکیج: {ud['package']}\n\n"
            f"درمانجو در حال تکمیل فرم اطلاعات است..."
        )
    )

    await query.edit_message_text(
        "خرید پایان همه چیز نیست، شروع یک اعتماد است\n\n"
        "لطفاً اطلاعات ثبت سفارش را وارد کنید:\n\n"
        "نام:"
    )

# ========== فرم اطلاعات ==========
async def form_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    step = ud.get('form_step')
    if not step:
        return False
    text = update.message.text
    uid = update.message.from_user.id

    if step == 'full_name':
        ud['full_name'] = text
        ud['form_step'] = 'last_name'
        add_history(uid, f"نام: {text}")
        await update.message.reply_text("نام خانوادگی:")
    elif step == 'last_name':
        ud['last_name'] = text
        ud['form_step'] = 'address'
        add_history(uid, f"نام خانوادگی: {text}")
        await update.message.reply_text("آدرس دقیق:")
    elif step == 'address':
        ud['address'] = text
        ud['form_step'] = 'phone'
        add_history(uid, f"آدرس: {text}")
        await update.message.reply_text("شماره تماس:")
    elif step == 'phone':
        ud['phone'] = text
        ud['form_step'] = None
        add_history(uid, f"شماره تماس: {text}")
        cursor.execute(
            "UPDATE patients SET package=?, full_name=?, last_name=?, address=?, phone=? WHERE chat_id=?",
            (ud.get('package'), ud.get('full_name'), ud.get('last_name'), ud.get('address'), ud.get('phone'), uid)
        )
        conn.commit()

        user = update.message.from_user
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📝 فرم اطلاعات تکمیل شد:\n"
                f"👤 درمانجو: {user.first_name} {user.last_name or ''} (@{user.username or 'ندارد'})\n"
                f"🆔 Chat ID: {user.id}\n"
                f"📦 پکیج: {ud.get('package')}\n"
                f"نام: {ud.get('full_name')} {ud.get('last_name')}\n"
                f"📍 آدرس: {ud.get('address')}\n"
                f"📞 تماس: {ud.get('phone')}\n\n"
                f"درمانجو در حال واریز و ارسال فیش است..."
            )
        )

        await update.message.reply_text(
            "✅ اطلاعات ثبت شد.\n\n"
            "💳 لطفاً مبلغ پکیج را به شماره کارت زیر واریز کنید:\n\n"
            "6219-8614-8063-1307\n"
            "به نام: آقای آریا عابدینی\n\n"
            "🙏 لطفاً پس از واریز، عکس فیش واریزی را ارسال کنید.\n"
            "🔴 با تشکر از حسن انتخاب و خرید شما"
        )
        ud['awaiting_receipt'] = True
    return True

# ========== پنل ادمین ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    cursor.execute("SELECT chat_id, name, username, issue, package, phone, date FROM patients ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("هنوز درمانجویی ثبت نشده.")
        return
    text = "📋 آخرین ۱۰ درمانجو:\n\n"
    for row in rows:
        text += (
            f"👤 {row[1]} (@{row[2] or 'ندارد'})\n"
            f"🆔 {row[0]}\n"
            f"🔹 {row[3] or '-'}\n"
            f"📦 {row[4] or '-'}\n"
            f"📞 {row[5] or '-'}\n"
            f"📅 {row[6]}\n\n"
        )
    await update.message.reply_text(text)

# ========== هندلر متن عمومی ==========
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await form_handler(update, context):
        return
    if await handle_question(update, context):
        return
    
    ud = context.user_data
    if 'issue' in ud and 'age' not in ud:
        await ask_age(update, context)
        return

    await update.message.reply_text("لطفاً از منوی /start استفاده کنید.")

# ========== اجرا ==========
def main():
    print("بات در حال روشن شدن...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("done", done_command)) # دستور جدید برای اتمام مشاوره
    
    app.add_handler(CallbackQueryHandler(issue_handler, pattern='^issue_'))
    app.add_handler(CallbackQueryHandler(question_callback, pattern='^has_question_'))
    app.add_handler(CallbackQueryHandler(package_callback, pattern='^pkg_'))
    app.add_handler(CallbackQueryHandler(questionnaire_callback))
    
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler((filters.VOICE | filters.TEXT) & filters.REPLY & filters.User(ADMIN_CHAT_ID), admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    
    print("بات روشن شد!")
    app.run_polling(poll_interval=1.0, timeout=30)

if __name__ == '__main__':
    main()
