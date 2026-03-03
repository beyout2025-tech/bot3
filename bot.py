#bot.py
import os
import logging
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# إعداد logging لتتبع الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تعيين رمز البوت الخاص بك (Bot Token) هنا
BOT_TOKEN = os.getenv("BOT_TOKEN")

# إضافة ID المطور الرئيسي هنا
DEV_ID = 873158772

# اسم ملف قاعدة البيانات
DB_FILE = "db.json"

# تعريف حالات المحادثة للمستخدمين العاديين
(
    GET_NAME,
    GET_GENDER,
    GET_AGE,
    GET_COUNTRY,
    GET_CITY,
    GET_PHONE,
    GET_EMAIL,
) = range(7)

# تعريف حالات المحادثة للمديرين
(
    GET_ACCEPT_MESSAGE,
    GET_REJECT_MESSAGE,
    GET_BROADCAST_MESSAGE,
    GET_ADMIN_ID_TO_ADD,
    GET_ADMIN_ID_TO_REMOVE,
    ADD_COURSE_NAME,
    ADD_COURSE_DESC,
    ADD_COURSE_PRICE,
    ADD_COURSE_CAT,
    EDIT_COURSE_SELECT_COURSE,
    EDIT_COURSE_SELECT_FIELD,
    EDIT_COURSE_NEW_VALUE,
    ADD_CATEGORY_NAME,
    DELETE_CATEGORY_CONFIRM,
    DELETE_COURSE_CONFIRM,
    EDIT_COURSE_CAT,
    MOVE_COURSE_SELECT_COURSE, # حالة جديدة لنقل الدورة
    MOVE_COURSE_SELECT_CAT, # حالة جديدة لاختيار التصنيف الجديد
) = range(7, 25) # تم تعديل مدى الأرقام ليشمل الحالات الجديدة

# دالة لقراءة البيانات من ملف JSON
def load_db():
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # إنشاء بنية فارغة إذا لم يكن الملف موجودًا
        data = {
            "users": [873158772],
            "admins": [873158772],
            "categories": [],
            "courses": [],
            "registrations": []
        }
    
    # ضمان وجود الـ DEV_ID دائمًا في قائمة المديرين
    if DEV_ID not in data["admins"]:
        data["admins"].append(DEV_ID)
        save_db(data)
        
    return data

# دالة لحفظ البيانات في ملف JSON
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# دالة لعرض القائمة الرئيسية
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = load_db()
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton("📚 استعراض التصنيفات", callback_data="show_categories")]
    ]
    if user_id in db["admins"]:
        keyboard.append([InlineKeyboardButton("🔧 لوحة المطور", callback_data="dev_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text="اختر من القائمة الرئيسية:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("اختر من القائمة الرئيسية:", reply_markup=reply_markup)

# دالة أمر /start المحدثة بإشعار دخول مفصل
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    db = load_db()
    
    # إرسال إشعار للمدير عند دخول مستخدم جديد فقط
    is_new_user = user_id not in db["users"]
    if is_new_user:
        db["users"].append(user_id)
        save_db(db)
        
        # تجهيز البيانات للإشعار
        total_users = len(db["users"])
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "لا يوجد"
        
        # القالب الذي طلبته
        message_to_admin = (
            f"تم دخول شخص جديد إلى البوت الخاص بك 👾\n"
            f"            -----------------------\n"
            f"• معلومات العضو الجديد .\n\n"
            f"• الاسم : {user_name}\n"
            f"• معرف : {username}\n"
            f"• الايدي : `{user_id}`\n"
            f"            -----------------------\n"
            f"• عدد الأعضاء الكلي : {total_users}"
        )
        
        # إرسال الإشعار لجميع المديرين المسجلين
        for admin_id in db["admins"]:
            try:
                # التأكد من عدم إرسال إشعار للمدير عن نفسه إذا كان هو من دخل
                if admin_id != user_id:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=message_to_admin,
                        parse_mode='Markdown'
                    )
            except Exception:
                continue
    
    await update.message.reply_text("أهلاً بك في بوت الدورات التدريبية!")
    await show_main_menu(update, context)


# دالة لعرض التصنيفات
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    db = load_db()
    categories = db["categories"]
    
    if not categories:
        await query.edit_message_text(text="لا توجد تصنيفات متاحة حالياً.")
        return

    keyboard = []
    for i in range(0, len(categories), 2):
        row = []
        row.append(InlineKeyboardButton(categories[i], callback_data=f"cat_{categories[i]}"))
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(categories[i+1], callback_data=f"cat_{categories[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="اختر التصنيف الذي تهتم به:", reply_markup=reply_markup)

# دالة لعرض الدورات ضمن تصنيف معين
async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    category_name = query.data.split("_")[1]
    db = load_db()
    
    courses_in_category = [c for c in db["courses"] if c["category"] == category_name and c["active"]]
    
    if not courses_in_category:
        await query.edit_message_text(
            text=f"لا توجد دورات متاحة حالياً في تصنيف '{category_name}'.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="show_categories")]])
        )
        return
        
    keyboard = []
    for i in range(0, len(courses_in_category), 2):
        row = []
        course1 = courses_in_category[i]
        row.append(InlineKeyboardButton(course1["name"], callback_data=f"course_{course1['id']}"))
        
        if i + 1 < len(courses_in_category):
            course2 = courses_in_category[i+1]
            row.append(InlineKeyboardButton(course2["name"], callback_data=f"course_{course2['id']}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="show_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"الدورات المتاحة في تصنيف '{category_name}':", reply_markup=reply_markup)

# دالة لعرض تفاصيل الدورة
async def show_course_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    course_id = int(query.data.split("_")[1])
    db = load_db()
    
    course = next((c for c in db["courses"] if c["id"] == course_id), None)
    
    if not course:
        await query.edit_message_text("عذرًا، لم يتم العثور على الدورة.")
        return

    message_text = (
        f"**{course['name']}**\n\n"
        f"**الوصف:** {course['description']}\n"
        f"**السعر:** {course['price']} دولار\n"
        f"**الحالة:** {'✅ متاحة للتسجيل' if course['active'] else '❌ غير متاحة حالياً'}"
    )
    
    keyboard = []
    if course["active"]:
        keyboard.append([InlineKeyboardButton("📥 التسجيل في الدورة", callback_data=f"register_{course_id}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"cat_{course['category']}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')

# دالة تبدأ عملية التسجيل
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    course_id = int(query.data.split("_")[1])
    context.user_data["registration_data"] = {"course_id": course_id}
    
    await query.edit_message_text("الرجاء إدخال **اسمك الثلاثي** الكامل:")
    return GET_NAME


# دالة للحصول على الاسم
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text
    context.user_data["registration_data"]["name"] = name
    
    keyboard = [
        [
            InlineKeyboardButton("ذكر", callback_data="gender_male"),
            InlineKeyboardButton("أنثى", callback_data="gender_female"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("الرجاء تحديد **الجنس**:", reply_markup=reply_markup)
    return GET_GENDER


# دالة للحصول على الجنس
async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    gender = "ذكر" if query.data == "gender_male" else "أنثى"
    context.user_data["registration_data"]["gender"] = gender
    
    await query.edit_message_text("الرجاء إدخال **عمرك** بالأرقام:")
    return GET_AGE


# دالة للحصول على العمر
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age = update.message.text
    if not age.isdigit():
        await update.message.reply_text("الرجاء إدخال رقم صحيح للعمر.")
        return GET_AGE
    
    context.user_data["registration_data"]["age"] = int(age)
    await update.message.reply_text("الرجاء إدخال **اسم البلد**:")
    return GET_COUNTRY


# دالة للحصول على البلد
async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    country = update.message.text
    context.user_data["registration_data"]["country"] = country
    await update.message.reply_text("الرجاء إدخال **اسم المدينة**:")
    return GET_CITY


# دالة للحصول على المدينة
async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    context.user_data["registration_data"]["city"] = city
    await update.message.reply_text("الرجاء إدخال **رقم هاتفك (للتواصل عبر الواتساب)**:")
    return GET_PHONE


# دالة للحصول على رقم الهاتف
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text
    context.user_data["registration_data"]["phone"] = phone
    await update.message.reply_text("الرجاء إدخال **بريدك الإلكتروني**:")
    return GET_EMAIL


# دالة للحصول على البريد الإلكتروني وإنهاء عملية التسجيل
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    context.user_data["registration_data"]["email"] = email
    
    registration_data = context.user_data.pop("registration_data")
    registration_data["user_id"] = update.effective_user.id
    registration_data["status"] = "pending"
    registration_data["receipt"] = None

    db = load_db()
    db["registrations"].append(registration_data)
    save_db(db)
    
    await update.message.reply_text(
        "✅ تم استلام طلبك بنجاح! سيتم مراجعته من قبل الإدارة وسيتم إرسال إشعار لك فوراً.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    admin_ids = db["admins"]
    if admin_ids:
        course = next((c for c in db["courses"] if c["id"] == registration_data['course_id']), None)
        course_name = course['name'] if course else 'دورة غير معروفة'
        
        message_to_admin = (
            f"**🔔 طلب تسجيل جديد**\n\n"
            f"**الدورة:** {course_name}\n"
            f"**الاسم:** {registration_data['name']}\n"
            f"**الجنس:** {registration_data['gender']}\n"
            f"**العمر:** {registration_data['age']}\n"
            f"**البلد:** {registration_data['country']}\n"
            f"**المدينة:** {registration_data['city']}\n"
            f"**الهاتف:** {registration_data['phone']}\n"
            f"**البريد:** {registration_data['email']}\n"
            f"**معرف المستخدم:** `{registration_data['user_id']}`"
        )
        
        admin_keyboard = [[InlineKeyboardButton("✅ قبول", callback_data=f"accept_{registration_data['user_id']}_{registration_data['course_id']}"),
                           InlineKeyboardButton("❌ رفض", callback_data=f"reject_{registration_data['user_id']}_{registration_data['course_id']}")]]
        
        for admin_id in admin_ids:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message_to_admin,
                reply_markup=InlineKeyboardMarkup(admin_keyboard),
                parse_mode='Markdown'
            )
        
    return ConversationHandler.END


# دالة لعرض لوحة المدير
async def show_dev_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db = load_db()
    user_id = update.effective_user.id
    if user_id not in db["admins"]:
        await query.edit_message_text("عذرًا، أنت لست مديرًا.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات", callback_data="dev_stats")],
        [InlineKeyboardButton("👤 إدارة المستخدمين", callback_data="dev_users")],
        [InlineKeyboardButton("📚 إدارة الدورات", callback_data="dev_courses")],
        [InlineKeyboardButton("🗂️ إدارة التصنيفات", callback_data="dev_categories")],
        [InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data="dev_broadcast")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("مرحباً بك في لوحة المطور! اختر من القائمة:", reply_markup=reply_markup)


# دوال إدارة لوحة المدير
async def show_dev_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db = load_db()
    
    num_users = len(db["users"])
    num_courses = len(db["courses"])
    num_admins = len(db["admins"])
    num_pending = len([r for r in db["registrations"] if r["status"] == "pending"])
    num_accepted = len([r for r in db["registrations"] if r["status"] == "accepted"])
    num_rejected = len([r for r in db["registrations"] if r["status"] == "rejected"])

    stats_text = (
        f"**📊 إحصائيات البوت**\n\n"
        f"عدد المستخدمين: {num_users}\n"
        f"عدد الدورات: {num_courses}\n"
        f"عدد المديرين: {num_admins}\n\n"
        f"**إحصائيات التسجيلات:**\n"
        f"طلبات معلقة: {num_pending}\n"
        f"طلبات مقبولة: {num_accepted}\n"
        f"طلبات مرفوضة: {num_rejected}"
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')


async def show_dev_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف", callback_data="dev_add_admin")],
        [InlineKeyboardButton("➖ إزالة مشرف", callback_data="dev_remove_admin")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر عملية إدارة المستخدمين:", reply_markup=reply_markup)


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("أرسل معرف المستخدم (User ID) الذي تريد إضافته كمشرف:")
    return GET_ADMIN_ID_TO_ADD

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_admin_id = int(update.message.text)
        db = load_db()
        if new_admin_id in db["admins"]:
            await update.message.reply_text("هذا المستخدم هو مشرف بالفعل.")
        else:
            db["admins"].append(new_admin_id)
            save_db(db)
            await update.message.reply_text(f"تم إضافة المستخدم {new_admin_id} كمشرف بنجاح.", reply_markup=ReplyKeyboardRemove())
            
            # إرسال إشعار للمستخدم الجديد أنه أصبح مشرفاً
            await context.bot.send_message(
                chat_id=new_admin_id,
                text="✅ تهانينا! لقد تم إضافتك كمدير في البوت."
            )
            
    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح.")
    return ConversationHandler.END


async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    db = load_db()
    # لا يمكن إزالة المطور الأساسي
    admins_to_remove = [admin for admin in db["admins"] if admin != DEV_ID]
    if not admins_to_remove:
        await query.edit_message_text("لا يوجد مشرفون لإزالتهم.")
        return ConversationHandler.END
        
    admin_list = "\n".join([str(a) for a in admins_to_remove])
    await query.edit_message_text(f"أرسل معرف المستخدم (User ID) الذي تريد إزالته من المشرفين:\n\nالمشرفون الحاليون:\n{admin_list}")
    return GET_ADMIN_ID_TO_REMOVE

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        admin_id_to_remove = int(update.message.text)
        db = load_db()
        if admin_id_to_remove == DEV_ID:
            await update.message.reply_text("لا يمكنك إزالة المطور الأساسي.", reply_markup=ReplyKeyboardRemove())
        elif admin_id_to_remove in db["admins"]:
            db["admins"].remove(admin_id_to_remove)
            save_db(db)
            await update.message.reply_text(f"تم إزالة المستخدم {admin_id_to_remove} من المشرفين.", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("هذا المستخدم ليس مشرفًا.")
    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح.")
    return ConversationHandler.END


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إرسال الرسالة التي تريد إرسالها لجميع المستخدمين:")
    return GET_BROADCAST_MESSAGE
#الرسائل الجماعية
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message_text = update.message.text
    db = load_db()
    users = db.get("users", [])
    
    if not users:
        await update.message.reply_text("⚠️ لا يوجد مستخدمون في قاعدة البيانات لإرسال الرسالة لهم.")
        return ConversationHandler.END

    success_count = 0
    fail_count = 0
    
    # إشعار للمدير ببدء العملية لكي لا يظن أن البوت معلق
    status_msg = await update.message.reply_text("⏳ جاري بدء الإرسال الجماعي... يرجى الانتظار.")
    
    for user_id in users:
        try:
            # التأكد من تحويل المعرف لرقم صحيح (حل مشكلة الـ String)
            await context.bot.send_message(
                chat_id=int(user_id), 
                text=message_text,
                parse_mode='Markdown' # لدعم التنسيق الغامق والمائل في رسالتك
            )
            success_count += 1
        except Exception as e:
            # تسجيل الخطأ وتجاوز المستخدم الذي حظر البوت
            logging.error(f"Error sending to {user_id}: {e}")
            fail_count += 1

    # تحديث الرسالة النهائية بالنتائج
    result_text = (
        f"✅ **اكتملت عملية الإرسال الجماعي**\n"
        f"-----------------------\n"
        f"• تم الإرسال بنجاح: {success_count}\n"
        f"• فشل الإرسال: {fail_count}\n"
        f"-----------------------\n"
        f"إجمالي القائمة: {len(users)}"
    )
    
    await status_msg.edit_text(result_text, parse_mode='Markdown')
    return ConversationHandler.END


# دوال إدارة الدورات
async def show_manage_courses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db = load_db()
    
    courses_list = ""
    if db["courses"]:
        for c in db["courses"]:
            courses_list += f"- {'✅' if c['active'] else '❌'} {c['name']} (ID: {c['id']})\n"
    else:
        courses_list = "لا توجد دورات حالياً."
        
    keyboard = [
        [InlineKeyboardButton("➕ إضافة دورة جديدة", callback_data="dev_add_course")],
        [InlineKeyboardButton("✏️ تعديل دورة", callback_data="dev_edit_course")],
        [InlineKeyboardButton("➡️ نقل دورة", callback_data="dev_move_course")], # زر جديد لنقل الدورة
        [InlineKeyboardButton("🗑️ حذف دورة", callback_data="dev_delete_course")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"**📚 إدارة الدورات**\n\n{courses_list}", reply_markup=reply_markup, parse_mode='Markdown')

async def add_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إدخال **اسم الدورة**:")
    return ADD_COURSE_NAME

async def add_course_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["temp_course_data"] = {"name": update.message.text}
    await update.message.reply_text("الآن، أدخل **وصف الدورة**:")
    return ADD_COURSE_DESC

async def add_course_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["temp_course_data"]["description"] = update.message.text
    await update.message.reply_text("الآن، أدخل **سعر الدورة** بالأرقام:")
    return ADD_COURSE_PRICE

async def add_course_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text)
        context.user_data["temp_course_data"]["price"] = price
        
        db = load_db()
        categories = db["categories"]
        if not categories:
            await update.message.reply_text("لا توجد تصنيفات، الرجاء إضافة تصنيف أولاً.")
            return ConversationHandler.END

        keyboard = [[InlineKeyboardButton(cat, callback_data=f"select_cat_{cat}")] for cat in categories]
        await update.message.reply_text("اختر **تصنيف الدورة**:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_COURSE_CAT
    except ValueError:
        await update.message.reply_text("الرجاء إدخال سعر صحيح (رقم).")
        return ADD_COURSE_PRICE

async def add_course_cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.split("select_cat_")[1]
    context.user_data["temp_course_data"]["category"] = category
    
    db = load_db()
    new_course = context.user_data.pop("temp_course_data")
    new_course["id"] = len(db["courses"]) + 1
    new_course["active"] = True
    db["courses"].append(new_course)
    save_db(db)
    
    await query.edit_message_text("✅ تم إضافة الدورة بنجاح!")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END


async def delete_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    db = load_db()
    if not db["courses"]:
        await query.edit_message_text("لا توجد دورات لحذفها.")
        return ConversationHandler.END
    
    keyboard = []
    for c in db["courses"]:
        keyboard.append([InlineKeyboardButton(f"{c['name']} (ID: {c['id']})", callback_data=f"del_course_confirm_{c['id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر الدورة التي تريد حذفها:", reply_markup=reply_markup)
    return DELETE_COURSE_CONFIRM


async def confirm_delete_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("del_course_confirm_")[1])
    db = load_db()
    
    db["courses"] = [c for c in db["courses"] if c["id"] != course_id]
    save_db(db)
    
    await query.edit_message_text(f"✅ تم حذف الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END


async def edit_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    db = load_db()
    if not db["courses"]:
        await query.edit_message_text("لا توجد دورات لتعديلها.")
        return ConversationHandler.END
    
    keyboard = []
    for c in db["courses"]:
        keyboard.append([InlineKeyboardButton(f"{c['name']} (ID: {c['id']})", callback_data=f"edit_select_{c['id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر الدورة التي تريد تعديلها:", reply_markup=reply_markup)
    return EDIT_COURSE_SELECT_COURSE

async def edit_course_select_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("edit_select_")[1])
    context.user_data["edit_course_id"] = course_id
    
    keyboard = [
        [InlineKeyboardButton("تعديل الاسم", callback_data="edit_field_name")],
        [InlineKeyboardButton("تعديل الوصف", callback_data="edit_field_desc")],
        [InlineKeyboardButton("تعديل السعر", callback_data="edit_field_price")],
        [InlineKeyboardButton("تعديل التصنيف", callback_data="edit_field_cat")],
        [InlineKeyboardButton("تغيير الحالة (متاح/غير متاح)", callback_data=f"toggle_status_{course_id}")],
        [InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر ما تريد تعديله في الدورة:", reply_markup=reply_markup)
    return EDIT_COURSE_SELECT_FIELD

async def edit_course_get_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field = query.data.split("edit_field_")[1]
    context.user_data["edit_field"] = field
    
    if field == "cat":
        db = load_db()
        categories = db["categories"]
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"edit_cat_{cat}")] for cat in categories]
        await query.edit_message_text("اختر التصنيف الجديد:", reply_markup=InlineKeyboardMarkup(keyboard))
        return EDIT_COURSE_CAT
    else:
        await query.edit_message_text(f"الرجاء إرسال القيمة الجديدة لـ {field}:")
        return EDIT_COURSE_NEW_VALUE

async def update_course_with_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = load_db()
    course_id = context.user_data.pop("edit_course_id")
    field = context.user_data.pop("edit_field")
    
    new_value = update.message.text
    if field == "price":
        try:
            new_value = float(new_value)
        except ValueError:
            await update.message.reply_text("الرجاء إدخال قيمة رقمية صحيحة للسعر.")
            return EDIT_COURSE_NEW_VALUE
            
    for c in db["courses"]:
        if c["id"] == course_id:
            c[field] = new_value
            break
            
    save_db(db)
    await update.message.reply_text(f"✅ تم تعديل الدورة بنجاح.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def update_course_with_new_cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    db = load_db()
    course_id = context.user_data.pop("edit_course_id")
    category = query.data.split("edit_cat_")[1]
    
    for c in db["courses"]:
        if c["id"] == course_id:
            c["category"] = category
            break
            
    save_db(db)
    await query.edit_message_text(f"✅ تم تعديل تصنيف الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END


async def toggle_course_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("toggle_status_")[1])
    db = load_db()
    for c in db["courses"]:
        if c["id"] == course_id:
            c["active"] = not c["active"]
            break
    save_db(db)
    await query.edit_message_text("✅ تم تغيير حالة الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END

# دوال جديدة لنقل الدورة
async def move_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    db = load_db()
    if not db["courses"]:
        await query.edit_message_text("لا توجد دورات لنقلها.")
        return ConversationHandler.END
    
    keyboard = []
    for c in db["courses"]:
        keyboard.append([InlineKeyboardButton(f"{c['name']} (ID: {c['id']})", callback_data=f"move_course_{c['id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر الدورة التي تريد نقلها:", reply_markup=reply_markup)
    return MOVE_COURSE_SELECT_COURSE

async def move_course_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("move_course_")[1])
    context.user_data["move_course_id"] = course_id
    
    db = load_db()
    categories = db["categories"]
    
    if not categories:
        await query.edit_message_text("لا توجد تصنيفات لنقل الدورة إليها.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(cat, callback_data=f"move_to_cat_{cat}")] for cat in categories]
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر التصنيف الجديد للدورة:", reply_markup=reply_markup)
    return MOVE_COURSE_SELECT_CAT

async def move_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    new_category = query.data.split("move_to_cat_")[1]
    course_id = context.user_data.pop("move_course_id")
    
    db = load_db()
    for c in db["courses"]:
        if c["id"] == course_id:
            c["category"] = new_category
            break
            
    save_db(db)
    await query.edit_message_text("✅ تم نقل الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END

# دوال إدارة التصنيفات
async def show_manage_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db = load_db()
    
    categories_list = "\n".join([f"- {cat}" for cat in db["categories"]]) if db["categories"] else "لا توجد تصنيفات حالياً."
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة تصنيف جديد", callback_data="dev_add_cat")],
        [InlineKeyboardButton("🗑️ حذف تصنيف", callback_data="dev_delete_cat")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"**🗂️ إدارة التصنيفات**\n\n{categories_list}", reply_markup=reply_markup, parse_mode='Markdown')

async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إدخال **اسم التصنيف** الجديد:")
    return ADD_CATEGORY_NAME

async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category_name = update.message.text
    db = load_db()
    if category_name in db["categories"]:
        await update.message.reply_text("هذا التصنيف موجود بالفعل.")
    else:
        db["categories"].append(category_name)
        save_db(db)
        await update.message.reply_text("✅ تم إضافة التصنيف بنجاح.", reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END


async def delete_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    db = load_db()
    if not db["categories"]:
        await query.edit_message_text("لا توجد تصنيفات لحذفها.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"del_cat_confirm_{cat}")] for cat in db["categories"]]
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر التصنيف الذي تريد حذفه:", reply_markup=reply_markup)
    return DELETE_CATEGORY_CONFIRM

async def confirm_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category_name = query.data.split("del_cat_confirm_")[1]
    
    context.user_data["temp_category_name"] = category_name
    
    keyboard = [
        [InlineKeyboardButton("حذف التصنيف فقط", callback_data="delete_cat_only")],
        [InlineKeyboardButton("حذف التصنيف والدورات التابعة له", callback_data="delete_cat_with_courses")],
        [InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_categories")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"هل تريد حذف التصنيف '{category_name}' فقط أم مع جميع الدورات التابعة له؟", reply_markup=reply_markup)
    return DELETE_CATEGORY_CONFIRM

async def execute_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    category_name = context.user_data.pop("temp_category_name")
    
    db = load_db()
    
    if choice == "delete_cat_with_courses":
        db["courses"] = [c for c in db["courses"] if c["category"] != category_name]
        db["categories"].remove(category_name)
        await query.edit_message_text(f"✅ تم حذف التصنيف '{category_name}' وجميع الدورات التابعة له بنجاح.")
    elif choice == "delete_cat_only":
        db["categories"].remove(category_name)
        await query.edit_message_text(f"✅ تم حذف التصنيف '{category_name}' فقط. الدورات التابعة له أصبحت بلا تصنيف.")
    
    save_db(db)
    await show_manage_categories_menu(update, context)
    return ConversationHandler.END


# دوال معالجة طلبات التسجيل (مدير)
async def accept_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, user_id, course_id = query.data.split('_')
    context.user_data['temp_reg_user_id'] = int(user_id)
    context.user_data['temp_reg_course_id'] = int(course_id)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="الرجاء كتابة رسالة مخصصة للمستخدم لإرسالها مع طلب إيصال الدفع:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_ACCEPT_MESSAGE

async def send_accept_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    accept_message = update.message.text
    user_id = context.user_data.pop('temp_reg_user_id')
    course_id = context.user_data.pop('temp_reg_course_id')
    db = load_db()
    for reg in db["registrations"]:
        if reg["user_id"] == user_id and reg["course_id"] == course_id and reg["status"] == "pending":
            reg["status"] = "accepted"
            break
    save_db(db)
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ تهانينا! تم قبول طلب تسجيلك في الدورة.\n\n"
             f"{accept_message}\n\n"
             f"الآن، الرجاء إرسال إيصال الدفع هنا."
    )
    await update.message.reply_text("تم إرسال رسالة القبول للمستخدم بنجاح.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def reject_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, user_id, course_id = query.data.split('_')
    context.user_data['temp_reg_user_id'] = int(user_id)
    context.user_data['temp_reg_course_id'] = int(course_id)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="الرجاء كتابة رسالة رفض مخصصة للمستخدم:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_REJECT_MESSAGE


async def send_reject_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reject_message = update.message.text
    user_id = context.user_data.pop('temp_reg_user_id')
    course_id = context.user_data.pop('temp_reg_course_id')
    db = load_db()
    for reg in db["registrations"]:
        if reg["user_id"] == user_id and reg["course_id"] == course_id and reg["status"] == "pending":
            reg["status"] = "rejected"
            break
    save_db(db)
    await context.bot.send_message(
        chat_id=user_id,
        text=f"❌ للأسف، تم رفض طلب تسجيلك.\n\n"
             f"{reject_message}"
    )
    await update.message.reply_text("تم إرسال رسالة الرفض للمستخدم بنجاح.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# دالة لمعالجة إيصال الدفع
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    db = load_db()
    registration = next((reg for reg in db["registrations"] if reg["user_id"] == user_id and reg["status"] == "accepted"), None)
    if registration and update.message.photo:
        receipt_file_id = update.message.photo[-1].file_id
        registration["receipt"] = receipt_file_id
        save_db(db)
        
        admin_ids_to_notify = db["admins"]
        if admin_ids_to_notify:
            course = next((c for c in db["courses"] if c["id"] == registration['course_id']), None)
            caption = (
                f"**🔔 تم استلام إيصال دفع جديد**\n\n"
                f"**الدورة:** {course['name'] if course else 'غير معروفة'}\n"
                f"**الاسم:** {registration['name']}\n"
                f"**معرف المستخدم:** `{registration['user_id']}`"
            )
            for admin_id in admin_ids_to_notify:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=receipt_file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            await update.message.reply_text("شكراً لك! تم إرسال إيصالك للمراجعة.")
    else:
        pass


# دالة لمعالجة جميع الأزرار (Callback Queries)
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    if data == "show_categories":
        await show_categories(update, context)
    elif data == "main_menu":
        await show_main_menu(update, context)
    elif data == "dev_panel":
        await show_dev_panel(update, context)
    elif data == "dev_stats":
        await show_dev_stats(update, context)
    elif data == "dev_users":
        await show_dev_users(update, context)
    elif data == "dev_courses":
        await show_manage_courses_menu(update, context)
    elif data == "dev_categories":
        await show_manage_categories_menu(update, context)
    elif data.startswith("cat_"):
        await show_courses(update, context)
    elif data.startswith("course_"):
        await show_course_details(update, context)


# دالة لإلغاء المحادثة
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('تم إلغاء العملية.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# دالة رئيسية لتشغيل البوت
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler لعملية تسجيل المستخدم
    user_reg_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_registration, pattern=r"^register_\d+$")],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_GENDER: [CallbackQueryHandler(get_gender, pattern=r"^gender_")],
            GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GET_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            GET_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لرسائل المدير المخصصة للقبول/الرفض
    admin_msg_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(accept_registration, pattern=r"^accept_\d+_\d+$"),
            CallbackQueryHandler(reject_registration, pattern=r"^reject_\d+_\d+$"),
        ],
        states={
            GET_ACCEPT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_accept_message)],
            GET_REJECT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_reject_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لإدارة المستخدمين
    admin_user_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_admin_start, pattern="^dev_add_admin$"),
            CallbackQueryHandler(remove_admin_start, pattern="^dev_remove_admin$"),
        ],
        states={
            GET_ADMIN_ID_TO_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin)],
            GET_ADMIN_ID_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_admin)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لإرسال رسالة جماعية
    admin_broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="^dev_broadcast$")],
        states={
            GET_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # ConversationHandler لإضافة دورة جديدة
    admin_add_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_course_start, pattern="^dev_add_course$")],
        states={
            ADD_COURSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_name)],
            ADD_COURSE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_desc)],
            ADD_COURSE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_price)],
            ADD_COURSE_CAT: [CallbackQueryHandler(add_course_cat, pattern=r"^select_cat_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لتعديل دورة
    admin_edit_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_course_start, pattern="^dev_edit_course$")],
        states={
            EDIT_COURSE_SELECT_COURSE: [CallbackQueryHandler(edit_course_select_field, pattern=r"^edit_select_\d+$")],
            EDIT_COURSE_SELECT_FIELD: [CallbackQueryHandler(edit_course_get_new_value, pattern=r"^edit_field_"),
                                       CallbackQueryHandler(toggle_course_status, pattern=r"^toggle_status_\d+$")],
            EDIT_COURSE_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_course_with_new_value)],
            EDIT_COURSE_CAT: [CallbackQueryHandler(update_course_with_new_cat, pattern=r"^edit_cat_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # ConversationHandler لحذف دورة
    admin_delete_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_course_start, pattern="^dev_delete_course$")],
        states={
            DELETE_COURSE_CONFIRM: [CallbackQueryHandler(confirm_delete_course, pattern=r"^del_course_confirm_\d+$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لنقل دورة (جديد)
    admin_move_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(move_course_start, pattern="^dev_move_course$")],
        states={
            MOVE_COURSE_SELECT_COURSE: [CallbackQueryHandler(move_course_select_category, pattern=r"^move_course_\d+$")],
            MOVE_COURSE_SELECT_CAT: [CallbackQueryHandler(move_course, pattern=r"^move_to_cat_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # ConversationHandler لإدارة التصنيفات
    admin_category_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_category_start, pattern="^dev_add_cat$"),
            CallbackQueryHandler(delete_category_start, pattern="^dev_delete_cat$")
        ],
        states={
            ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category)],
            DELETE_CATEGORY_CONFIRM: [CallbackQueryHandler(execute_delete_category, pattern=r"^(delete_cat_only|delete_cat_with_courses)$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # إضافة Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(user_reg_handler)
    application.add_handler(admin_msg_handler)
    application.add_handler(admin_user_handler)
    application.add_handler(admin_broadcast_handler)
    application.add_handler(admin_add_course_handler)
    application.add_handler(admin_edit_course_handler)
    application.add_handler(admin_delete_course_handler)
    application.add_handler(admin_move_course_handler) # إضافة الـ Handler الجديد هنا
    application.add_handler(admin_category_handler)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    
    # تشغيل البوت
    print("البوت يعمل...")
    application.run_polling()

if __name__ == "__main__":
    main()


