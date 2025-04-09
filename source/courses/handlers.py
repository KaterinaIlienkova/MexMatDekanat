from source.courses.db_queries import get_student_courses, get_teacher_courses, get_course_students

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from source.database import SessionLocal

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

async def course_callback_handler(update: Update, context: CallbackContext):
    """Обробляє натискання на інлайн-кнопку з курсом."""
    query = update.callback_query
    await query.answer()  # Відповідаємо на колбек-запит

    # Отримуємо ID курсу з callback_data
    course_id = int(query.data.split('_')[1])

    try:
        # Використовуємо контекст для сесії SQLAlchemy
        with SessionLocal() as db:
            # Отримуємо інформацію про курс
            course_info = None
            courses = get_teacher_courses(query.from_user.username, db)
            for course in courses:
                if course["course_id"] == course_id:
                    course_info = course
                    break

            if not course_info:
                await query.edit_message_text("Курс не знайдений.")
                return

            # Отримуємо список студентів
            students = get_course_students(course_id, db)

            if not students:
                await query.edit_message_text(f"На курсі '{course_info['course_name']}' немає студентів.")
                return

            # Формуємо список студентів
            student_info = "\n\n".join(
                [f"👤 *{student['student_name']}*\n📱 Телефон: {student['student_phone']}\n💬 Telegram: @{student['telegram_tag']}"
                 for student in students]
            )

            # Додаємо кнопку "Назад"
            keyboard = [[InlineKeyboardButton("⬅️ Назад до списку курсів", callback_data="back_teachercourses")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"📋 *Список студентів на курсі '{course_info['course_name']}'*:\n\n{student_info}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    except Exception as e:
        await query.edit_message_text(f"Сталася помилка при отриманні студентів: {str(e)}")

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