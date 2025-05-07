from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.ext import CallbackContext, CallbackQueryHandler, Application

from source.services.CourseService import CourseService

# Стани для конверсаційного обробника додавання курсу
ADD_COURSE_NAME, ADD_COURSE_PLATFORM, ADD_COURSE_LINK = range(3)

# Стани для конверсаційного обробника деактивації курсу
DEACTIVATE_COURSE = range(1)

class CourseController:
    """Контролер для управління курсами через Telegram."""

    def __init__(self, application: Application, course_service:CourseService):
        """
        Ініціалізує CourseController.

        Args:
            application: Об'єкт Telegram Application
            course_service: Сервіс для роботи з курсами
        """
        self.application = application
        self.course_service = course_service
        self.register_handlers()

    def register_handlers(self):
        """Реєструє обробники для кнопок та команд, пов'язаних з курсами."""

        # Обробники для студентів
        self.application.add_handler(CallbackQueryHandler(
            self.view_course_details,
            pattern="^studentcourse_\\d+$"
        ))

        # Обробники для викладачів
        self.application.add_handler(CallbackQueryHandler(
            self.view_course_students,
            pattern="^teachercourse_\\d+$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.back_to_courses_list,
            pattern="^back_to_courses$"
        ))

    async def view_student_courses(self, update: Update, context: CallbackContext):
        """
        Показує список курсів студента у вигляді повідомлення.
        """
        user = update.effective_user
        telegram_tag = user.username

        # Отримуємо курси студента
        courses = self.course_service.get_student_courses(telegram_tag, active_only=True)

        if not courses:
            await update.message.reply_text("У вас немає активних курсів або ви не зареєстровані як студент.")
            return

        # Створюємо клавіатуру з курсами
        keyboard = []
        for course in courses:
            keyboard.append([InlineKeyboardButton(
                course["course_name"],
                callback_data=f"studentcourse_{course['course_id']}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Відправляємо повідомлення з кнопками
        await update.message.reply_text(
            "📚 Ваші поточні курси. Натисніть на курс для детальної інформації:",
            reply_markup=reply_markup
        )

    async def view_course_details(self, update: Update, context: CallbackContext):
        """
        Показує детальну інформацію про курс для студента.
        """
        query = update.callback_query
        await query.answer()

        # Отримуємо ID курсу з callback_data
        course_id = int(query.data.split("_")[1])

        # Отримуємо всі курси студента
        courses = self.course_service.get_student_courses(query.from_user.username, active_only=True)

        # Знаходимо потрібний курс за ID
        course = next((c for c in courses if c["course_id"] == course_id), None)

        if not course:
            await query.edit_message_text("Інформація про курс не знайдена.")
            return

        # Формуємо повідомлення з деталями курсу
        message = f"📚 *{course['course_name']}*\n\n"
        message += f"👨‍🏫 Викладач: {course['teacher']['name']}\n"
        message += f"📧 Email: {course['teacher']['email']}\n"

        if course['teacher']['phone'] != "Не вказано":
            message += f"📞 Телефон: {course['teacher']['phone']}\n"

        message += f"📝 Платформа: {course['study_platform']}\n"

        if course['meeting_link'] != "Не вказано":
            message += f"🔗 Посилання на зустріч: {course['meeting_link']}\n"

        # Додаємо кнопку "Назад"
        keyboard = [[InlineKeyboardButton("Назад до списку курсів", callback_data="back_to_courses")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

    async def back_to_courses_list(self, update: Update, context: CallbackContext):
        """
        Повертає студента до списку його курсів.
        """
        query = update.callback_query
        await query.answer()

        # Отримуємо курси студента
        courses = self.course_service.get_student_courses(query.from_user.username, active_only=True)

        if not courses:
            await query.edit_message_text("У вас немає активних курсів.")
            return

        # Створюємо клавіатуру з курсами
        keyboard = []
        for course in courses:
            keyboard.append([InlineKeyboardButton(
                course["course_name"],
                callback_data=f"studentcourse_{course['course_id']}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📚 Ваші поточні курси. Натисніть на курс для детальної інформації:",
            reply_markup=reply_markup
        )

    async def view_teacher_courses(self, update: Update, context: CallbackContext):
        """
        Показує список курсів викладача з опціями управління.
        """
        user = update.effective_user
        message_obj = update.message or update.callback_query.message

        # Отримуємо курси викладача
        courses_list = self.course_service.get_teacher_courses(user.username, active_only=True)

        if not courses_list:
            if not self.course_service.is_teacher(user.username):
                await message_obj.reply_text("Ви не зареєстровані як викладач.")
                return
            else:
                message = "У вас немає активних курсів."
        else:
            message = "📚 <b>Ваші активні курси:</b>\n\n"
            for course in courses_list:
                students = self.course_service.get_course_students(course["course_id"])
                student_count = len(students)

                message += f"<b>{course['course_name']}</b>\n"
                message += f"Платформа: {course['study_platform']}\n"
                message += f"Посилання: {course['meeting_link']}\n"
                message += f"Кількість студентів: {student_count}\n\n"

        # Додаємо кнопки для управління курсами
        keyboard = [
            [InlineKeyboardButton("👥 Переглянути списки студентів", callback_data="view_students")],
            [InlineKeyboardButton("➕ Додати новий курс", callback_data="add_course")],
            [InlineKeyboardButton("❌ Деактивувати курс", callback_data="deactivate_course")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Відправляємо повідомлення
        await message_obj.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def view_course_students(self, update: Update, context: CallbackContext):
        """
        Показує список студентів на конкретному курсі.
        """
        query = update.callback_query
        await query.answer()

        # Отримуємо ID курсу з callback_data
        course_id = int(query.data.split("_")[1])

        # Отримуємо список студентів на курсі
        students = self.course_service.get_course_students(course_id)

        # Отримуємо інформацію про курс
        courses = self.course_service.get_teacher_courses(query.from_user.username)
        course = next((c for c in courses if c["course_id"] == course_id), None)

        if not course:
            await query.edit_message_text("Інформація про курс не знайдена.")
            return

        # Формуємо повідомлення зі списком студентів
        if not students:
            message = f"На курсі <b>{course['course_name']}</b> немає студентів."
        else:
            message = f"📚 <b>Студенти курсу: {course['course_name']}</b>\n\n"
            for i, student in enumerate(students, 1):
                message += f"{i}. <b>{student['student_name']}</b>\n"
                message += f"   Telegram: @{student['telegram_tag']}\n"
                if student['student_phone'] != "Не вказано":
                    message += f"   Телефон: {student['student_phone']}\n"
                message += "\n"

        # Додаємо кнопку "Назад"
        keyboard = [[InlineKeyboardButton("Назад до списку курсів", callback_data="back_to_courses")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")


    async def view_students(self, update: Update, context: CallbackContext):
        """
        Показує викладачу список його активних курсів у вигляді кнопок.
        При натисканні на курс викладач зможе побачити список студентів.
        """
        # Отримуємо користувача (через message або callback_query)
        user = update.effective_user
        message_obj = update.message or update.callback_query.message

        # Перевіряємо, чи є користувач викладачем
        if not self.course_service.is_teacher(user.username):
            await message_obj.reply_text("Ви не зареєстровані як викладач.")
            return

        # Отримуємо активні курси викладача через service
        courses = self.course_service.get_teacher_courses(user.username, active_only=True)

        if not courses:
            await message_obj.reply_text("У вас немає активних курсів.")
            return

        # Створюємо інлайн-кнопки з курсами
        keyboard = []
        for course in courses:
            keyboard.append([InlineKeyboardButton(
                course["course_name"],
                callback_data=f"teachercourse_{course['course_id']}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await message_obj.reply_text(
            "Ваші активні курси. Оберіть курс, щоб побачити список студентів:",
            reply_markup=reply_markup
        )