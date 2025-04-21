from source.courses.db_queries import get_student_courses, get_teacher_courses, get_course_students, \
    get_teacher_id_by_username, add_new_course
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, \
    filters, ContextTypes
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from source.database import SessionLocal

# Стани для конверсаційного обробника додавання курсу
ADD_COURSE_NAME, ADD_COURSE_PLATFORM, ADD_COURSE_LINK = range(3)
# Стани для конверсаційного обробника деактивації курсу
DEACTIVATE_COURSE = range(1)

async def view_courses_by_student(update: Update, context: CallbackContext):
    """
    Обробник команди для відображення курсів студента
    """
    user = update.effective_user
    telegram_tag = user.username

    # Отримуємо сесію бази даних
    with SessionLocal() as db:
        try:
            # За замовчуванням отримуємо тільки активні курси
            courses = get_student_courses(telegram_tag, db, active_only=True)

            if not courses:
                await update.message.reply_text("У вас немає активних курсів або ви не зареєстровані як студент.")
                return

            # Формуємо повідомлення з курсами
            message = "📚 *Ваші поточні курси:*\n\n"

            for course in courses:
                message += f"*{course['course_name']}*\n"
                message += f"👨‍🏫 Викладач: {course['teacher']['name']}\n"
                message += f"📧 Email: {course['teacher']['email']}\n"

                if course['teacher']['phone'] != "Не вказано":
                    message += f"📞 Телефон: {course['teacher']['phone']}\n"

                message += f"📝 Платформа: {course['study_platform']}\n"

                if course['meeting_link'] != "Не вказано":
                    message += f"🔗 Посилання на зустріч: {course['meeting_link']}\n"

                message += "\n"

            await update.message.reply_text(message, parse_mode="Markdown")

        except Exception as e:
            await update.message.reply_text(f"Сталася помилка: {str(e)}")

async def view_students(update: Update, context: CallbackContext):
    """Показує викладачу список його активних курсів у вигляді кнопок."""

    # Отримуємо Telegram тег викладача
    telegram_tag = update.message.from_user.username

    try:
        # Використовуємо контекст для сесії SQLAlchemy
        with SessionLocal() as db:
            courses = get_teacher_courses(telegram_tag, db)

            if not courses:
                await update.message.reply_text("Ви не ведете жодного курсу.")
                return

            # Створюємо інлайн-кнопки з курсами
            keyboard = []
            for course in courses:
                keyboard.append([InlineKeyboardButton(
                    course["course_name"],
                    callback_data=f"teachercourse_{course['course_id']}"
                )])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "Ваші активні курси. Оберіть курс, щоб побачити список студентів:",
                reply_markup=reply_markup
            )

    except Exception as e:
        await update.message.reply_text(f"Сталася помилка при отриманні курсів: {str(e)}")


async def back_to_courses_handler(update: Update, context: CallbackContext):
    """Обробляє натискання на кнопку 'Назад до списку курсів'."""
    query = update.callback_query
    await query.answer()

    # Викликаємо функцію для показу списку курсів, але через edit_message
    telegram_tag = query.from_user.username

    try:
        with SessionLocal() as db:
            courses = get_teacher_courses(telegram_tag, db)

            if not courses:
                await query.edit_message_text("Ви не ведете жодного курсу.")
                return

            # Створюємо інлайн-кнопки з курсами
            keyboard = []
            for course in courses:
                keyboard.append([InlineKeyboardButton(
                    course["course_name"],
                    callback_data=f"teachercourse_{course['course_id']}"
                )])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "Ваші активні курси. Оберіть курс, щоб побачити список студентів:",
                reply_markup=reply_markup
            )

    except Exception as e:
        await query.edit_message_text(f"Сталася помилка при отриманні курсів: {str(e)}")
async def courses(update: Update, context: CallbackContext):
    """Відображає список курсів викладача та додаткові опції."""
    user = update.effective_user
    message_obj = update.message or update.callback_query.message

    with SessionLocal() as session:
        courses_list = get_teacher_courses(user.username, session, active_only=True)

        if not courses_list:
            teacher_id = get_teacher_id_by_username(session, user.username)
            if teacher_id is None:
                await message_obj.reply_text("Ви не зареєстровані як викладач.")
                return
            else:
                message = "У вас немає активних курсів."
        else:
            message = "📚 <b>Ваші активні курси:</b>\n\n"
            for course in courses_list:
                students = get_course_students(course["course_id"], session)
                student_count = len(students)

                message += f"<b>{course['course_name']}</b>\n"
                message += f"Платформа: {course['study_platform']}\n"
                message += f"Посилання: {course['meeting_link']}\n"
                message += f"Кількість студентів: {student_count}\n\n"

        keyboard = [
            [InlineKeyboardButton("➕ Додати новий курс", callback_data="add_course")],
            [InlineKeyboardButton("❌ Деактивувати курс", callback_data="deactivate_course")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await message_obj.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')



async def add_course_name(update: Update, context: CallbackContext):
    """Зберігає назву курсу та запитує платформу."""
    context.user_data['course_name'] = update.message.text
    await update.message.reply_text("Тепер введіть назву навчальної платформи (або відправте '-', якщо немає):")
    return ADD_COURSE_PLATFORM

async def add_course_platform(update: Update, context: CallbackContext):
    """Зберігає платформу та запитує посилання на зустріч."""
    platform = update.message.text
    context.user_data['course_platform'] = None if platform == '-' else platform
    await update.message.reply_text("Тепер введіть посилання на зустріч (або відправте '-', якщо немає):")
    return ADD_COURSE_LINK

async def add_course_link(update: Update, context: CallbackContext):
    """Завершує створення курсу та зберігає його в базу даних."""
    link = update.message.text
    context.user_data['course_link'] = None if link == '-' else link

    # Отримуємо дані з контексту
    course_name = context.user_data['course_name']
    course_platform = context.user_data['course_platform']
    course_link = context.user_data['course_link']

    user = update.effective_user

    with SessionLocal() as session:
        # Знаходимо ID викладача
        teacher_id = get_teacher_id_by_username(session, user.username)

        if not teacher_id:
            await update.message.reply_text("Помилка: не вдалося знайти інформацію про викладача.")
            return ConversationHandler.END

        # Додаємо новий курс
        success = add_new_course(session, course_name, course_platform, course_link, teacher_id)

        if success:
            await update.message.reply_text(f"Курс '{course_name}' успішно створено!")
        else:
            await update.message.reply_text("На жаль, сталася помилка при створенні курсу. Спробуйте пізніше.")

    # Очищаємо дані користувача
    context.user_data.clear()

    # Викликаємо функцію курсів безпосередньо
    update.callback_query = None  # Переконаємося, що немає callback_query
    await courses(update, context)

    return ConversationHandler.END

async def course_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # Наприклад: "teachercourse_view_5", "teachercourse_edit_5", "teachercourse_deactivate_5"

    if data.startswith("teachercourse_"):
        parts = data.split("_")  # ['teachercourse', 'view', '5']
        if len(parts) >= 3:
            action = parts[1]
            course_id = parts[2]

            if action == "view":
                await query.edit_message_text(f"🔍 Інформація про курс ID {course_id}")
                # Тут можеш додати витяг з бази даних і вивід деталей курсу

            elif action == "edit":
                context.user_data["editing_course_id"] = course_id
                await query.edit_message_text(f"✏️ Введіть нову назву курсу ID {course_id}")
                # Далі чекаєш на повідомлення від викладача через MessageHandler

            elif action == "deactivate":
                # Тут ставиш у базі is_active = False
                await query.edit_message_text(f"🛑 Курс ID {course_id} було деактивовано.")
                # Можеш надіслати повідомлення назад або оновити список курсів
