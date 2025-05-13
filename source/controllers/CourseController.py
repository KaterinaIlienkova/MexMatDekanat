from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.ext import CallbackContext, CallbackQueryHandler, Application

from source.services.CourseService import CourseService




class CourseController:
    WAITING_FOR_COURSE_NAME = "waiting_for_course_name"
    WAITING_FOR_PLATFORM = "waiting_for_platform"
    WAITING_FOR_LINK = "waiting_for_link"
    """Контролер для управління курсами через Telegram."""

    def __init__(self, application: Application, course_service: CourseService):
        """
        Ініціалізує CourseController.

        Args:
            application: Об'єкт Telegram Application
            course_service: Сервіс для роботи з курсами
        """
        self.application = application
        self.course_service = course_service

    def register_handlers(self):
        """Реєструє обробники для кнопок та команд, пов'язаних з курсами."""

        return [
            # Обробники для студентів
            CallbackQueryHandler(
                self.view_course_details,
                pattern="^studentcourse_\\d+$"
            ),

            # Обробники для викладачів
            CallbackQueryHandler(
                self.view_course_students,
                pattern="^teachercourse_\\d+$"
            ),
            CallbackQueryHandler(
                self.back_to_courses_list,
                pattern="^back_to_courses$"
            ),
            # Додаємо нові обробники для функціоналу "Мої курси"
            CallbackQueryHandler(
                self.view_teacher_course_options,
                pattern="^viewteachercourses$"
            ),

            CallbackQueryHandler(
                self.start_create_course,
                pattern="^create_course$"
            ),

            CallbackQueryHandler(
                self.show_archive_options,
                pattern="^archive_course$"
            ),

            CallbackQueryHandler(
                self.archive_selected_course,
                pattern="^archive_\\d+$"
            ),
            # Нові обробники для додавання студентів
            CallbackQueryHandler(
                self.start_add_student,
                pattern="^add_student_\\d+$"
            ),
            CallbackQueryHandler(
                self.select_group_for_add,
                pattern="^select_group_\\d+_\\d+$"
            ),
            CallbackQueryHandler(
                self.add_student_to_course,
                pattern="^add_student_to_course_\\d+_\\d+$"
            ),

            # Нові обробники для видалення студентів
            CallbackQueryHandler(
                self.start_remove_student,
                pattern="^remove_student_\\d+$"
            ),
            CallbackQueryHandler(
                self.remove_student_from_course,
                pattern="^remove_student_from_course_\\d+_\\d+$"
            ),
        ]

    async def view_student_courses(self, update: Update, context: CallbackContext):
        """
        Показує список курсів студента у вигляді повідомлення.
        """
        try:
            user = update.effective_user
            telegram_tag = user.username

            # Логування для діагностики
            print(f"view_student_courses викликано для користувача: {telegram_tag}")

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
        except Exception as e:
            print(f"Помилка у view_student_courses: {e}")
            await update.message.reply_text("Сталася помилка при отриманні списку курсів.")

    async def view_course_details(self, update: Update, context: CallbackContext):
        """
        Показує детальну інформацію про курс для студента.
        """
        query = update.callback_query
        await query.answer()

        # Отримуємо ID курсу з callback_data
        # Перевіряємо формат callback_data
        callback_parts = query.data.split("_")
        if len(callback_parts) < 2 or not callback_parts[1].isdigit():
            await query.edit_message_text("Помилка при отриманні інформації про курс.")
            return

        course_id = int(callback_parts[1])

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


    async def view_students(self, update: Update, context: CallbackContext):
        """
        Показує викладачу список його активних курсів у вигляді кнопок.
        При натисканні на курс викладач зможе побачити список студентів.
        """
        try:
            # Отримуємо користувача
            user = update.effective_user
            # Визначаємо, звідки прийшов запит - з повідомлення чи з callback
            message_obj = update.message or update.callback_query.message

            # Логування для діагностики
            print(f"view_students викликано для користувача: {user.username}")

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
        except Exception as e:
            print(f"Помилка у view_students: {e}")
            await update.message.reply_text("Сталася помилка при отриманні списку студентів.")

    async def view_course_students(self, update: Update, context: CallbackContext):
        """
        Показує список студентів на конкретному курсі та додає кнопки для управління списком.
        """
        query = update.callback_query
        await query.answer()

        # Безпечне отримання ID курсу з callback_data
        try:
            callback_parts = query.data.split("_")
            if callback_parts[0] == "teachercourse" and len(callback_parts) > 1 and callback_parts[1].isdigit():
                course_id = int(callback_parts[1])
            else:
                # Якщо прийшли з іншого місця, спробуємо взяти ID з контексту
                course_id = context.user_data.get("current_course_id")
                if course_id is None:
                    await query.edit_message_text("Не вдалося визначити курс.")
                    return
        except (IndexError, ValueError) as e:
            print(f"Помилка при обробці callback_data у view_course_students: {e}, data: {query.data}")
            await query.edit_message_text("Сталася помилка при обробці запиту.")
            return

        # Зберігаємо ID курсу в контексті, щоб використовувати його в інших методах
        context.user_data["current_course_id"] = course_id

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
                # Додаємо ID студента в дужках для ідентифікації при видаленні
                student_id = self.course_service.get_student_id_by_telegram(student['telegram_tag'])
                message += f"{i}. <b>{student['student_name']}</b>\n"
                message += f"   Telegram: @{student['telegram_tag']}\n"
                if student['student_phone'] != "Не вказано":
                    message += f"   Телефон: {student['student_phone']}\n"
                # Додаємо кнопку для видалення цього студента
                student_id_for_removal = student_id if student_id else i  # Захист від None
                message += f"   [ID: {student_id_for_removal}]\n"
                message += "\n"

        # Додаємо кнопки для управління списком студентів
        keyboard = [
            [InlineKeyboardButton("➕ Додати студента", callback_data=f"add_student_{course_id}")],
            [InlineKeyboardButton("❌ Видалити студента", callback_data=f"remove_student_{course_id}")],
            [InlineKeyboardButton("↩️ Назад до списку курсів", callback_data="back_to_courses")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

    async def start_add_student(self, update: Update, context: CallbackContext):
        """
        Починає процес додавання студента до курсу - показує список груп.
        """
        query = update.callback_query
        await query.answer()

        # Безпечне отримання ID курсу
        try:
            callback_parts = query.data.split("_")
            if len(callback_parts) >= 3 and callback_parts[2].isdigit():
                course_id = int(callback_parts[2])
            else:
                course_id = context.user_data.get("current_course_id")
                if course_id is None:
                    await query.edit_message_text("Не вдалося визначити курс.")
                    return
        except (IndexError, ValueError) as e:
            print(f"Помилка при обробці callback_data у start_add_student: {e}, data: {query.data}")
            await query.edit_message_text("Сталася помилка при обробці запиту.")
            return

        context.user_data["current_course_id"] = course_id

        # Отримуємо всі групи
        groups = self.course_service.get_all_student_groups()

        if not groups:
            await query.edit_message_text(
                "Немає доступних груп студентів.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("↩️ Назад", callback_data=f"teachercourse_{course_id}")
                ]])
            )
            return

        # Створюємо клавіатуру з групами
        keyboard = []
        for group in groups:
            keyboard.append([
                InlineKeyboardButton(
                    group["group_name"],
                    callback_data=f"select_group_{group['group_id']}_{course_id}"
                )
            ])

        # Додаємо кнопку "Назад"
        keyboard.append([
            InlineKeyboardButton("↩️ Назад", callback_data=f"teachercourse_{course_id}")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Оберіть групу студента для додавання до курсу:",
            reply_markup=reply_markup
        )

    async def select_group_for_add(self, update: Update, context: CallbackContext):
        """
        Обробляє вибір групи та відображає список ВСІХ студентів з цієї групи.
        """
        query = update.callback_query
        await query.answer()

        # Безпечне отримання ID групи та курсу з callback_data
        try:
            parts = query.data.split("_")
            if len(parts) >= 4 and parts[2].isdigit() and parts[3].isdigit():
                group_id = int(parts[2])
                course_id = int(parts[3])
            else:
                await query.edit_message_text("Помилка при обробці запиту.")
                return
        except (IndexError, ValueError) as e:
            print(f"Помилка при обробці callback_data у select_group_for_add: {e}, data: {query.data}")
            await query.edit_message_text("Сталася помилка при обробці запиту.")
            return

        context.user_data["selected_group_id"] = group_id
        context.user_data["current_course_id"] = course_id

        # Отримуємо всіх студентів групи незалежно від зарахування
        students = self.course_service.get_all_students_by_group(group_id)

        if not students:
            await query.edit_message_text(
                "У цій групі немає студентів.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("↩️ Назад", callback_data=f"add_student_{course_id}")
                ]])
            )
            return

        # Створюємо клавіатуру зі студентами
        keyboard = []
        for student in students:
            keyboard.append([
                InlineKeyboardButton(
                    student["student_name"],
                    callback_data=f"add_student_to_course_{student['student_id']}_{course_id}"
                )
            ])

        # Додаємо кнопку "Назад"
        keyboard.append([
            InlineKeyboardButton("↩️ Назад", callback_data=f"add_student_{course_id}")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Оберіть студента для додавання до курсу:",
            reply_markup=reply_markup
        )

    async def add_student_to_course(self, update: Update, context: CallbackContext):
        """
        Додає обраного студента до курсу. Якщо студент вже зарахований,
        показує повідомлення про це.
        """
        query = update.callback_query
        await query.answer()

        # Безпечне отримання ID студента та курсу з callback_data
        try:
            parts = query.data.split("_")
            if len(parts) >= 6 and parts[4].isdigit() and parts[5].isdigit():
                student_id = int(parts[4])
                course_id = int(parts[5])

            else:
                await query.answer("Помилка при обробці запиту.", show_alert=True)
                return
        except (IndexError, ValueError) as e:
            print(f"Помилка при обробці callback_data у add_student_to_course: {e}, data: {query.data}")
            await query.answer("Сталася помилка при обробці запиту.", show_alert=True)
            return

        # Додаємо студента до курсу
        success = self.course_service.add_student_to_course(student_id, course_id)

        if success:
            await query.answer("Студента успішно додано до курсу!", show_alert=True)
        else:
            await query.answer("Помилка при додаванні студента до курсу.", show_alert=True)

        # Повертаємось до списку студентів курсу
        context.user_data["current_course_id"] = course_id
        await self.view_course_students(update, context)

    async def start_remove_student(self, update: Update, context: CallbackContext):
        """
        Починає процес видалення студента з курсу.
        Показує список студентів курсу з кнопками для видалення.
        """
        query = update.callback_query
        await query.answer()

        # Безпечне отримання ID курсу
        try:
            callback_parts = query.data.split("_")
            if len(callback_parts) >= 3 and callback_parts[2].isdigit():
                course_id = int(callback_parts[2])
            else:
                course_id = context.user_data.get("current_course_id")
                if course_id is None:
                    await query.edit_message_text("Не вдалося визначити курс.")
                    return
        except (IndexError, ValueError) as e:
            print(f"Помилка при обробці callback_data у start_remove_student: {e}, data: {query.data}")
            await query.edit_message_text("Сталася помилка при обробці запиту.")
            return

        context.user_data["current_course_id"] = course_id

        # Отримуємо список студентів на курсі
        students = self.course_service.get_course_students(course_id)

        if not students:
            await query.edit_message_text(
                "На цьому курсі немає студентів для видалення.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("↩️ Назад", callback_data=f"teachercourse_{course_id}")
                ]])
            )
            return

        # Створюємо клавіатуру зі студентами та кнопками для видалення
        keyboard = []
        for i, student in enumerate(students):
            # Отримуємо ID студента
            student_id = self.course_service.get_student_id_by_telegram(student['telegram_tag'])
            if student_id:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{i+1}. {student['student_name']} (@{student['telegram_tag']})",
                        callback_data=f"remove_student_from_course_{student_id}_{course_id}"
                    )
                ])

        # Додаємо кнопку "Назад"
        keyboard.append([
            InlineKeyboardButton("↩️ Назад", callback_data=f"teachercourse_{course_id}")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Оберіть студента для видалення з курсу:",
            reply_markup=reply_markup
        )

    async def remove_student_from_course(self, update: Update, context: CallbackContext):
        """
        Видаляє студента з курсу. Перевіряє, чи студент дійсно зарахований на курс.
        """
        query = update.callback_query
        await query.answer()

        # Безпечне отримання ID студента та курсу з callback_data
        try:
            parts = query.data.split("_")
            if len(parts) >= 6 and parts[4].isdigit() and parts[5].isdigit():
                student_id = int(parts[4])
                course_id = int(parts[5])
            else:
                await query.answer("Помилка при обробці запиту.", show_alert=True)
                return
        except (IndexError, ValueError) as e:
            print(f"Помилка при обробці callback_data у remove_student_from_course: {e}, data: {query.data}")
            await query.answer("Сталася помилка при обробці запиту.", show_alert=True)
            return

        # Видаляємо студента з курсу
        success = self.course_service.remove_student_from_course(student_id, course_id)

        if success:
            await query.answer("Студента успішно видалено з курсу!", show_alert=True)
        else:
            await query.answer("Помилка при видаленні студента з курсу.", show_alert=True)

        # Повертаємось до списку студентів курсу
        context.user_data["current_course_id"] = course_id
        await self.view_course_students(update, context)


    async def view_teacher_courses(self, update: Update, context: CallbackContext):
        """
        Показує викладачу список його курсів та опції для управління ними.
        """
        try:
            user = update.effective_user
            # Визначаємо, звідки прийшов запит - з повідомлення чи з callback
            message_obj = update.message or update.callback_query.message

            # Логування для діагностики
            print(f"view_teacher_courses викликано для користувача: {user.username}")

            # Перевіряємо, чи є користувач викладачем
            if not self.course_service.is_teacher(user.username):
                await message_obj.reply_text("Ви не зареєстровані як викладач.")
                return

            # Отримуємо курси викладача
            courses = self.course_service.get_teacher_courses(user.username, active_only=True)

            # Формуємо повідомлення з інформацією про курси
            if not courses:
                course_info = "У вас немає активних курсів."
            else:
                course_info = "📚 <b>Ваші активні курси:</b>\n\n"
                for i, course in enumerate(courses, 1):
                    course_info += f"<b>{i}. {course['course_name']}</b>\n"
                    course_info += f"   📝 Платформа: {course['study_platform']}\n"
                    if course['meeting_link'] != "Не вказано":
                        course_info += f"   🔗 Посилання: {course['meeting_link']}\n"
                    course_info += "\n"

            # Створюємо кнопки для створення нового курсу або архівації існуючого
            keyboard = [
                [InlineKeyboardButton("Створити новий курс", callback_data="create_course")],
                [InlineKeyboardButton("Архівувати курс", callback_data="archive_course")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Визначаємо, чи це відповідь на callback або на повідомлення
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    course_info,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await message_obj.reply_text(
                    course_info,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Помилка у view_teacher_courses: {e}")
            error_message = "Сталася помилка при отриманні інформації про курси."
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def view_teacher_course_options(self, update: Update, context: CallbackContext):
        """
        Показує опції для управління курсами (повертає до основного вікна курсів).
        """
        await self.view_teacher_courses(update, context)

    async def start_create_course(self, update: Update, context: CallbackContext):
        """
        Починає процес створення нового курсу.
        """
        query = update.callback_query
        await query.answer()

        # Встановлюємо стан для очікування назви курсу
        context.user_data['state'] = self.WAITING_FOR_COURSE_NAME

        await query.edit_message_text(
            "📝 <b>Створення нового курсу</b>\n\n"
            "Будь ласка, введіть назву курсу:",
            parse_mode="HTML"
        )

    async def handle_course_creation_input(self, update: Update, context: CallbackContext):
        """
        Обробляє введені дані при створенні курсу.
        """
        # Перевіряємо, чи знаходимося в стані створення курсу
        state = context.user_data.get('state')
        if not state or not state.startswith('waiting_for_'):
            return False  # Повертаємо False, якщо це не наше введення

        text = update.message.text

        if state == self.WAITING_FOR_COURSE_NAME:
            # Зберігаємо назву курсу
            context.user_data['course_name'] = text
            context.user_data['state'] = self.WAITING_FOR_PLATFORM

            await update.message.reply_text(
                "Введіть платформу для навчання (наприклад, Zoom, Google Meet, тощо).\n"
                "Якщо не використовуєте специфічну платформу, введіть '-':"
            )
            return True

        elif state == self.WAITING_FOR_PLATFORM:
            # Зберігаємо платформу
            context.user_data['platform'] = None if text == '-' else text
            context.user_data['state'] = self.WAITING_FOR_LINK

            await update.message.reply_text(
                "Введіть посилання на зустрічі для курсу.\n"
                "Якщо посилання немає, введіть '-':"
            )
            return True

        elif state == self.WAITING_FOR_LINK:
            # Зберігаємо посилання і створюємо курс
            link = None if text == '-' else text

            # Отримуємо збережені дані
            course_name = context.user_data.get('course_name')
            platform = context.user_data.get('platform')

            # Створюємо новий курс
            success = self.course_service.create_course(
                update.effective_user.username,
                course_name,
                platform,
                link
            )

            # Очищуємо дані стану
            context.user_data.pop('state', None)
            context.user_data.pop('course_name', None)
            context.user_data.pop('platform', None)

            if success:
                await update.message.reply_text(
                    f"✅ Курс '{course_name}' успішно створено!"
                )
                # Показуємо оновлений список курсів
                await self.view_teacher_courses(update, context)
            else:
                await update.message.reply_text(
                    "❌ Не вдалося створити курс. Будь ласка, спробуйте ще раз або зверніться до адміністратора."
                )
            return True

        return False  # На випадок, якщо це не наше введення

    async def show_archive_options(self, update: Update, context: CallbackContext):
        """
        Показує список курсів для архівації.
        """
        query = update.callback_query
        await query.answer()

        # Отримуємо активні курси викладача
        courses = self.course_service.get_teacher_courses(query.from_user.username, active_only=True)

        if not courses:
            await query.edit_message_text("У вас немає активних курсів для архівації.")
            return

        # Створюємо кнопки для вибору курсу для архівації
        keyboard = []
        for course in courses:
            keyboard.append([InlineKeyboardButton(
                course["course_name"],
                callback_data=f"archive_{course['course_id']}"
            )])

        # Додаємо кнопку повернення
        keyboard.append([InlineKeyboardButton("Назад", callback_data="viewteachercourses")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Оберіть курс для архівації:",
            reply_markup=reply_markup
        )

    async def archive_selected_course(self, update: Update, context: CallbackContext):
        """
        Архівує вибраний курс.
        """
        query = update.callback_query
        await query.answer()

        # Отримуємо ID курсу з callback_data
        course_id = int(query.data.split("_")[1])

        # Отримуємо всі курси викладача для пошуку назви
        courses = self.course_service.get_teacher_courses(query.from_user.username)
        course = next((c for c in courses if c["course_id"] == course_id), None)

        if not course:
            await query.edit_message_text("Курс не знайдено.")
            return

        # Архівуємо курс
        success = self.course_service.archive_course(course_id)

        if success:
            await query.edit_message_text(
                f"✅ Курс '{course['course_name']}' успішно архівовано."
            )
            # Показуємо оновлений список курсів
            await self.view_teacher_courses(update, context)
        else:
            await query.edit_message_text(
                f"❌ Не вдалося архівувати курс '{course['course_name']}'. Спробуйте ще раз."
            )