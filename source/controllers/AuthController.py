import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, \
    filters
from telegram.ext import ContextTypes

from source.controllers.BaseController import BaseController
from source.services import AuthService

logger = logging.getLogger(__name__)


class AuthController(BaseController):

    WAITING_FOR_USER_DETAILS = "WAITING_FOR_USER_DETAILS"
    # Стани для ConversationHandler
    WAITING_FOR_USER_ROLE = 1
    WAITING_FOR_USERNAME = 2
    WAITING_FOR_TELEGRAM_TAG = 3
    WAITING_FOR_PHONE = 4

    # Стани для студента
    WAITING_FOR_GROUP = 5
    WAITING_FOR_SPECIALTY = 6
    WAITING_FOR_ADMISSION_YEAR = 7

    # Стани для викладача
    WAITING_FOR_EMAIL = 8
    WAITING_FOR_DEPARTMENT = 9

    WAITING_FOR_CONFIRMATION = 10
    # Додаємо нові стани для обробки заявок
    WAITING_FOR_REGISTRATION_ACTION = 11
    WAITING_FOR_USER_SELECTION = 12
    WAITING_FOR_APPROVAL_ACTION = 13

    # Для редагування
    WAITING_FOR_EDIT_FIELD = 14
    WAITING_FOR_NEW_USERNAME = 15
    WAITING_FOR_NEW_TELEGRAM_TAG = 16
    WAITING_FOR_NEW_PHONE = 17
    WAITING_FOR_NEW_GROUP = 18
    WAITING_FOR_NEW_ADMISSION_YEAR = 19

    # Нові стани для видалення користувача
    WAITING_FOR_DELETE_ROLE = 20
    WAITING_FOR_DELETE_DEPARTMENT = 21
    WAITING_FOR_DELETE_COURSE = 22
    WAITING_FOR_DELETE_GROUP = 23
    WAITING_FOR_DELETE_USER = 24
    WAITING_FOR_DELETE_CONFIRMATION = 25

    def __init__(self, application, auth_service: AuthService):
        super().__init__(application)
        self.auth_service = auth_service

    def register_handlers(self):
        """Returns handlers for Telegram bot."""
        # Don't register CommandHandler for add_user here since we're calling it from MenuController
        return [
            ConversationHandler(
                entry_points=[
                    # Add entry point for handling button click
                    MessageHandler(filters.Regex('^Додати користувача$'), self.add_user),
                    MessageHandler(filters.Regex('^Підтвердити реєстрацію$'), self.view_registration_requests),
                    MessageHandler(filters.Regex('^Видалити користувача$'), self.delete_user),
                    CommandHandler("add_user", self.add_user),
                    CommandHandler("approve_registrations", self.view_registration_requests),
                    CommandHandler("delete_user", self.delete_user)
                ],
                states={
                    self.WAITING_FOR_USER_ROLE: [
                        # Add CallbackQueryHandler to handle button click
                        CallbackQueryHandler(self.process_role),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_role)
                    ],
                    # Rest of your states
                    self.WAITING_FOR_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_username)],
                    self.WAITING_FOR_TELEGRAM_TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_telegram_tag)],
                    self.WAITING_FOR_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_phone)],

                    # Для студента
                    self.WAITING_FOR_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_group)],
                    self.WAITING_FOR_SPECIALTY: [
                        CallbackQueryHandler(self.process_specialty_choice),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_specialty)
                    ],
                    self.WAITING_FOR_ADMISSION_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_admission_year)],

                    # Для викладача
                    self.WAITING_FOR_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_email)],
                    self.WAITING_FOR_DEPARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_department)],
                    # Для підтвердження
                    self.WAITING_FOR_CONFIRMATION: [CallbackQueryHandler(self.process_confirmation)],

                    # Нові стани для обробки заявок на реєстрацію
                    self.WAITING_FOR_USER_SELECTION: [CallbackQueryHandler(self.select_student)],
                    self.WAITING_FOR_APPROVAL_ACTION: [CallbackQueryHandler(self.process_student_action)],
                    self.WAITING_FOR_EDIT_FIELD: [CallbackQueryHandler(self.select_edit_field)],
                    self.WAITING_FOR_NEW_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_new_username)],
                    self.WAITING_FOR_NEW_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_new_phone)],
                    self.WAITING_FOR_NEW_GROUP: [CallbackQueryHandler(self.process_new_group)],
                    self.WAITING_FOR_NEW_ADMISSION_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_new_admission_year)],

                    # Нові стани для видалення користувача
                    self.WAITING_FOR_DELETE_ROLE: [CallbackQueryHandler(self.process_delete_role)],
                    self.WAITING_FOR_DELETE_DEPARTMENT: [CallbackQueryHandler(self.process_delete_department)],
                    self.WAITING_FOR_DELETE_COURSE: [CallbackQueryHandler(self.process_delete_course)],
                    self.WAITING_FOR_DELETE_GROUP: [CallbackQueryHandler(self.process_delete_group)],
                    self.WAITING_FOR_DELETE_USER: [CallbackQueryHandler(self.process_delete_user)],
                    self.WAITING_FOR_DELETE_CONFIRMATION: [CallbackQueryHandler(self.process_delete_confirmation)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel)]
            )
        ]

    async def delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ініціює процес видалення користувача."""

        # Створення інлайн кнопок для вибору ролі
        keyboard = [
            [InlineKeyboardButton("Студент", callback_data="delete_student")],
            [InlineKeyboardButton("Викладач", callback_data="delete_teacher")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Виберіть роль користувача, якого бажаєте видалити:",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_DELETE_ROLE

    async def process_delete_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            #Обробляє вибір ролі для видалення.
        query = update.callback_query
        await query.answer()

        role = query.data.split('_')[1]  # delete_student або delete_teacher
        context.user_data['delete_role'] = role

        if role == "student":
            # Отримати список курсів для студентів
            courses = await self.auth_service.get_admission_years()

            keyboard = []
            for course in courses:
                keyboard.append([InlineKeyboardButton(f"{course} курс", callback_data=f"delete_course_{course}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Виберіть курс студента:",
                reply_markup=reply_markup
            )

            return self.WAITING_FOR_DELETE_COURSE

        elif role == "teacher":
            # Отримати список кафедр для викладачів
            departments = await self.auth_service.get_departments()

            keyboard = []
            for i, department in enumerate(departments):
                # Використовуємо індекс замість повної назви
                keyboard.append([InlineKeyboardButton(department, callback_data=f"delete_dept_{i}")])
                # Зберігаємо відповідність між індексом та назвою кафедри
                if 'department_map' not in context.user_data:
                    context.user_data['department_map'] = {}
                context.user_data['department_map'][str(i)] = department

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Виберіть кафедру викладача:",
                reply_markup=reply_markup
            )

            return self.WAITING_FOR_DELETE_DEPARTMENT

    async def process_delete_course(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє вибір курсу для видалення студента."""
        query = update.callback_query
        await query.answer()

        course = query.data.split('_')[2]
        context.user_data['delete_course'] = course

        # Отримати список груп для вибраного курсу
        groups = await self.auth_service.get_groups_by_admission_year(course)

        keyboard = []
        for group in groups:
            keyboard.append([InlineKeyboardButton(group, callback_data=f"delete_group_{group}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Виберіть групу студента з {course} курсу:",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_DELETE_GROUP

    async def process_delete_department(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обробляє вибір кафедри для видалення викладача."""
            query = update.callback_query
            await query.answer()

            # Отримуємо індекс кафедри з callback_data
            dept_index = query.data.split('_')[2]

            # Отримуємо реальну назву кафедри з map у контексті
            department = context.user_data['department_map'][dept_index]
            context.user_data['delete_department'] = department

            # Отримати список викладачів кафедри
            teachers = await self.auth_service.get_teachers_by_department(department)

            keyboard = []
            for teacher in teachers:
                # Використовуємо ID користувача замість імені та email
                keyboard.append([InlineKeyboardButton(
                    f"{teacher['name']} ({teacher['email']})",
                    callback_data=f"delete_user_{teacher['user_id']}"
                )])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"Виберіть викладача кафедри {department} для видалення:",
                reply_markup=reply_markup
            )

            return self.WAITING_FOR_DELETE_USER

    async def process_delete_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє вибір групи для видалення студента."""
        query = update.callback_query
        await query.answer()

        group = query.data.split('_')[2]
        context.user_data['delete_group'] = group

        # Отримати список студентів групи
        course = context.user_data.get('delete_course')
        students = await self.auth_service.get_students_by_group_and_course(group, course)

        keyboard = []
        for student in students:
            keyboard.append([InlineKeyboardButton(
                student['name'],
                callback_data=f"delete_user_{student['user_id']}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Виберіть студента групи {group} для видалення:",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_DELETE_USER

    async def process_delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє вибір користувача для видалення."""
        query = update.callback_query
        await query.answer()

        user_id = query.data.split('_')[2]
        context.user_data['delete_user_id'] = user_id

        # Отримати інформацію про користувача
        user_info = await self.auth_service.get_user_info(user_id)

        # Створити клавіатуру підтвердження
        keyboard = [
            [InlineKeyboardButton("Підтвердити видалення", callback_data="confirm_delete")],
            [InlineKeyboardButton("Скасувати", callback_data="cancel_delete")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Відобразити інформацію про користувача та запит на підтвердження
        if context.user_data.get('delete_role') == 'student':
            await query.edit_message_text(
                f"Ви впевнені, що хочете видалити студента:\n"
                f"Ім'я: {user_info['name']}\n"
                f"Група: {user_info['group']}\n"
                f"Курс: {user_info['course']}\n"
                f"Телефон: {user_info.get('phone', 'Не вказано')}\n\n"
                f"Увага! Ця дія видалить усі пов'язані записи студента, включаючи записи на курси та заявки на документи!",
                reply_markup=reply_markup
            )
        else:  # teacher
            await query.edit_message_text(
                f"Ви впевнені, що хочете видалити викладача:\n"
                f"Ім'я: {user_info['name']}\n"
                f"Кафедра: {user_info['department']}\n"
                f"Email: {user_info['email']}\n"
                f"Телефон: {user_info.get('phone', 'Не вказано')}\n\n"
                f"Увага! Ця дія не може бути скасована!",
                reply_markup=reply_markup
            )

        return self.WAITING_FOR_DELETE_CONFIRMATION

    async def process_delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє підтвердження видалення користувача."""
        query = update.callback_query
        await query.answer()

        action = query.data.split('_')[0]

        if action == "confirm":
            user_id = context.user_data.get('delete_user_id')
            # Викликаємо метод сервісу для видалення користувача
            result = self.auth_service.delete_user(user_id)

            if result:
                await query.edit_message_text("Користувача успішно видалено з системи.")
            else:
                await query.edit_message_text("Помилка при видаленні користувача. Спробуйте знову.")

        else:  # cancel
            await query.edit_message_text("Видалення користувача скасовано.")

        # Очищаємо дані
        context.user_data.clear()

        return ConversationHandler.END

    async def check_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
        """Перевіряє реєстрацію користувача при вході в бот."""
        user = update.effective_user
        telegram_tag = user.username
        chat_id = update.effective_chat.id

        if not telegram_tag:
            await update.message.reply_text(
                "❌ У вашому профілі Telegram відсутнє ім'я користувача. "
                "Будь ласка, встановіть його в налаштуваннях Telegram."
            )
            return None

        return await self.auth_service.check_and_register_user(update, context, telegram_tag, chat_id)

    async def add_user(self, update: Update, context: CallbackContext) -> int:
        """Починає процес додавання нового користувача (для працівників деканату)."""
        # Перевіряємо, чи користувач має роль dean_office
        user = update.effective_user
        telegram_tag = user.username

        if not telegram_tag:
            await update.message.reply_text("❌ У вашому профілі Telegram відсутнє ім'я користувача.")
            return ConversationHandler.END

        # Перевіряємо роль користувача через сервіс
        user_data = self.auth_service.auth_repository.get_user_by_telegram_tag(telegram_tag)
        if not user_data or user_data.Role != "dean_office":
            await update.message.reply_text("❌ У вас немає прав для додавання нових користувачів.")
            return ConversationHandler.END

        # Очищаємо попередні дані, якщо є
        context.user_data.clear()

        # Показуємо кнопки вибору ролі
        keyboard = [
            [InlineKeyboardButton("Студент", callback_data="student")],
            [InlineKeyboardButton("Викладач", callback_data="teacher")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Виберіть роль нового користувача:",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_USER_ROLE

    async def process_role(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір ролі користувача."""
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            role = query.data
            await query.edit_message_text(f"Обрана роль: {role}")
        else:
            role = update.message.text.lower()

        if role not in ["student", "teacher"]:
            message = update.message or update.callback_query.message
            await message.reply_text("❌ Невірна роль. Виберіть 'student' або 'teacher'.")
            return self.WAITING_FOR_USER_ROLE

        context.user_data["role"] = role

        message = update.message or update.callback_query.message
        await message.reply_text("Введіть ім'я та прізвище користувача:")
        return self.WAITING_FOR_USERNAME

    async def process_username(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введене ім'я користувача."""
        username = update.message.text.strip()
        context.user_data["username"] = username

        await update.message.reply_text("Введіть Telegram-тег користувача (без @):")
        return self.WAITING_FOR_TELEGRAM_TAG

    async def process_telegram_tag(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введений Telegram-тег."""
        telegram_tag = update.message.text.strip()

        # Видаляємо символ @ якщо він є
        if telegram_tag.startswith('@'):
            telegram_tag = telegram_tag[1:]

        # Перевіряємо чи користувач вже існує
        existing_user = self.auth_service.auth_repository.get_user_by_telegram_tag(telegram_tag)
        if existing_user:
            await update.message.reply_text("❌ Користувач з таким Telegram-тегом вже існує.")
            return self.WAITING_FOR_TELEGRAM_TAG

        context.user_data["telegram_tag"] = telegram_tag

        await update.message.reply_text("Введіть номер телефону користувача:")
        return self.WAITING_FOR_PHONE

    async def process_phone(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введений номер телефону."""
        phone_number = update.message.text.strip()
        context.user_data["phone_number"] = phone_number

        # Різна логіка залежно від ролі
        role = context.user_data.get("role", "")

        if role == "student":
            await update.message.reply_text("Введіть назву групи студента:")
            return self.WAITING_FOR_GROUP
        elif role == "teacher":
            await update.message.reply_text("Введіть email викладача:")
            return self.WAITING_FOR_EMAIL
        else:
            await update.message.reply_text("❌ Невідома роль користувача.")
            return ConversationHandler.END

    async def process_group(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введену групу студента."""
        group_name = update.message.text.strip()
        context.user_data["group_name"] = group_name

        # Перевіряємо чи група існує
        group = self.auth_service.auth_repository.get_student_group_by_name(group_name)

        if group:
            # Група існує, переходимо до року вступу
            context.user_data["group_id"] = group.GroupID
            await update.message.reply_text("Введіть рік вступу студента (наприклад, 2023):")
            return self.WAITING_FOR_ADMISSION_YEAR
        else:
            # Групи немає, потрібно створити - запитуємо спеціальність
            keyboard = [
                [InlineKeyboardButton("Не створювати нову групу", callback_data="cancel_group")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"Група '{group_name}' не знайдена. Введіть назву спеціальності для створення нової групи, або натисніть кнопку:",
                reply_markup=reply_markup
            )
            return self.WAITING_FOR_SPECIALTY

    async def process_specialty_choice(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір зі спеціальністю через кнопки."""
        query = update.callback_query
        await query.answer()

        choice = query.data

        if choice == "cancel_group":
            await query.edit_message_text("❌ Операцію скасовано. Група потрібна для створення студента.")
            return ConversationHandler.END

        return self.WAITING_FOR_SPECIALTY

    async def process_specialty(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введену спеціальність для нової групи."""
        specialty_name = update.message.text.strip()
        context.user_data["specialty_name"] = specialty_name

        await update.message.reply_text("Введіть рік вступу студента (наприклад, 2023):")
        return self.WAITING_FOR_ADMISSION_YEAR

    async def process_admission_year(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введений рік вступу."""
        try:
            admission_year = int(update.message.text.strip())

            # Перевірка на розумні межі року
            current_year = 2025  # Можна отримати поточний рік з datetime.now().year
            if admission_year < 2000 or admission_year > current_year:
                await update.message.reply_text("❌ Введіть коректний рік вступу (між 2000 та поточним роком).")
                return self.WAITING_FOR_ADMISSION_YEAR

            context.user_data["admission_year"] = admission_year

            # Перейти до підтвердження
            return await self.show_confirmation(update, context)

        except ValueError:
            await update.message.reply_text("❌ Введіть рік числом (наприклад, 2023).")
            return self.WAITING_FOR_ADMISSION_YEAR

    async def process_email(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введений email викладача."""
        email = update.message.text.strip()

        # Проста перевірка формату email
        if "@" not in email or "." not in email:
            await update.message.reply_text("❌ Введіть коректний email.")
            return self.WAITING_FOR_EMAIL

        context.user_data["email"] = email

        await update.message.reply_text("Введіть назву кафедри викладача:")
        return self.WAITING_FOR_DEPARTMENT

    async def process_department(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введену кафедру викладача."""
        department_name = update.message.text.strip()
        context.user_data["department_name"] = department_name

        # Перейти до підтвердження
        return await self.show_confirmation(update, context)

    async def show_confirmation(self, update: Update, context: CallbackContext) -> int:
        """Показує дані для підтвердження."""
        data = context.user_data
        role = data.get("role", "")

        confirmation_text = f"Підтвердіть дані нового користувача:\n\n"
        confirmation_text += f"Ім'я: {data.get('username', '')}\n"
        confirmation_text += f"Telegram: @{data.get('telegram_tag', '')}\n"
        confirmation_text += f"Телефон: {data.get('phone_number', '')}\n"

        if role == "student":
            confirmation_text += f"Роль: Студент\n"
            confirmation_text += f"Група: {data.get('group_name', '')}\n"

            # Якщо створюється нова група
            if 'specialty_name' in data:
                confirmation_text += f"Спеціальність: {data.get('specialty_name', '')}\n"

            confirmation_text += f"Рік вступу: {data.get('admission_year', '')}\n"
        elif role == "teacher":
            confirmation_text += f"Роль: Викладач\n"
            confirmation_text += f"Email: {data.get('email', '')}\n"
            confirmation_text += f"Кафедра: {data.get('department_name', '')}\n"

        keyboard = [
            [
                InlineKeyboardButton("✅ Підтвердити", callback_data="confirm"),
                InlineKeyboardButton("❌ Скасувати", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = update.message or update.callback_query.message
        await message.reply_text(confirmation_text, reply_markup=reply_markup)

        return self.WAITING_FOR_CONFIRMATION

    async def process_confirmation(self, update: Update, context: CallbackContext) -> int:
        """Обробляє підтвердження або скасування створення користувача."""
        query = update.callback_query
        await query.answer()

        choice = query.data

        if choice == "cancel":
            await query.edit_message_text("❌ Операцію скасовано.")
            return ConversationHandler.END

        if choice == "confirm":
            try:
                # Створення користувача
                data = context.user_data
                role = data.get("role", "")

                user_data = {
                    "username": data.get("username", ""),
                    "telegram_tag": data.get("telegram_tag", ""),
                    "phone_number": data.get("phone_number", ""),
                    "role": role
                }

                if role == "student":
                    group_name = data.get("group_name", "")
                    group_id = data.get("group_id")

                    # Якщо потрібно створити нову групу
                    if not group_id and "specialty_name" in data:
                        specialty_name = data.get("specialty_name", "")

                        # Створюємо нову групу
                        group_id = self.auth_service.get_or_create_student_group(group_name, specialty_name)
                        if not group_id:
                            await query.edit_message_text("❌ Помилка при створенні групи.")
                            return ConversationHandler.END

                    # Додаткові дані для студента
                    user_data["group_id"] = group_id
                    user_data["group_name"] = group_name
                    user_data["admission_year"] = data.get("admission_year")

                elif role == "teacher":
                    # Додаткові дані для викладача
                    user_data["email"] = data.get("email", "")
                    user_data["department_name"] = data.get("department_name", "")

                if role == "student":
                    result = self.auth_service.create_student(user_data)
                elif role == "teacher":
                    result = self.auth_service.create_teacher(user_data)
                else:
                    result = None

                if result:
                    await query.edit_message_text(f"✅ Користувача успішно створено")
                else:
                    await query.edit_message_text("❌ Помилка при створенні користувача.")

                return ConversationHandler.END

            except Exception as e:
                logger.error(f"Error creating user: {e}")
                await query.edit_message_text(f"❌ Помилка: {str(e)}")
                return ConversationHandler.END

        return self.WAITING_FOR_CONFIRMATION

    async def cancel(self, update: Update, context: CallbackContext) -> int:
        """Скасовує процес додавання користувача."""
        message = update.message or update.callback_query.message
        await message.reply_text("❌ Операцію скасовано.")
        return ConversationHandler.END


    async def view_registration_requests(self, update: Update, context: CallbackContext) -> int:
        """Показує список заявок на реєстрацію."""
        # Перевіряємо, чи користувач має права доступу (role = dean_office)
        user = update.effective_user
        telegram_tag = user.username

        if not telegram_tag:
            await update.message.reply_text("❌ У вашому профілі Telegram відсутнє ім'я користувача.")
            return ConversationHandler.END

        user_data = self.auth_service.auth_repository.get_user_by_telegram_tag(telegram_tag)
        if not user_data or user_data.Role != "dean_office":
            await update.message.reply_text("❌ У вас немає прав для перегляду заявок на реєстрацію.")
            return ConversationHandler.END

        # Отримуємо список непідтверджених студентів
        students = self.auth_service.get_unconfirmed_students()

        if not students:
            await update.message.reply_text("Немає заявок на реєстрацію.")
            return ConversationHandler.END

        # Зберігаємо список студентів в контексті для доступу в інших функціях
        context.user_data["unconfirmed_students"] = students

        # Відправляємо інформацію про кожного студента окремим повідомленням перед відправкою кнопок
        for i, student in enumerate(students):
            student_info = (
                f"👤 {i+1}. {student['username']}\n"
                f"📱 Telegram: @{student['telegram_tag']}\n"
                f"☎️ Телефон: {student['phone_number']}\n"
                f"👥 Група: {student['group_name']}\n"
                f"📅 Рік вступу: {student['admission_year']}"
            )
            await update.message.reply_text(student_info)

        # Створюємо клавіатуру з номерами заявок
        keyboard = []
        for i, student in enumerate(students):
            keyboard.append([InlineKeyboardButton(
                f"{i+1}",
                callback_data=f"select_student_{student['user_id']}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Список заявок на реєстрацію студентів:\n"
            "Виберіть студента для підтвердження, редагування або видалення:",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_USER_SELECTION

    async def select_student(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір студента зі списку."""
        query = update.callback_query
        await query.answer()

        user_id = int(query.data.split("_")[-1])

        # Зберігаємо ID користувача для подальшої обробки
        context.user_data["selected_user_id"] = user_id

        # Знаходимо інформацію про вибраного студента
        students = context.user_data.get("unconfirmed_students", [])
        selected_student = next((s for s in students if s["user_id"] == user_id), None)

        if not selected_student:
            await query.edit_message_text("❌ Студент не знайдений. Спробуйте знову.")
            return ConversationHandler.END

        # Зберігаємо дані вибраного студента
        context.user_data["selected_student"] = selected_student

        # Показуємо детальну інформацію про студента
        student_info = (
            f"📋 Інформація про студента:\n\n"
            f"Ім'я: {selected_student['username']}\n"
            f"Telegram: @{selected_student['telegram_tag']}\n"
            f"Телефон: {selected_student['phone_number']}\n"
            f"Група: {selected_student['group_name']}\n"
            f"Рік вступу: {selected_student['admission_year']}"
        )

        # Створюємо клавіатуру з доступними діями
        keyboard = [
            [
                InlineKeyboardButton("✅ Підтвердити", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Відхилити", callback_data=f"delete_{user_id}")
            ],
            [
                InlineKeyboardButton("✏️ Редагувати", callback_data=f"edit_{user_id}"),
                InlineKeyboardButton("↩️ Назад", callback_data="back_to_list")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(student_info, reply_markup=reply_markup)

        return self.WAITING_FOR_APPROVAL_ACTION

    async def process_student_action(self, update: Update, context: CallbackContext) -> int:
        """Обробляє дію з вибраним студентом (підтвердження, видалення або редагування)."""
        query = update.callback_query
        await query.answer()

        action = query.data.split("_")[0]

        if action == "back":
            # Повертаємося до списку студентів
            return await self.view_registration_requests(update, context)

        user_id = context.user_data.get("selected_user_id")
        if not user_id:
            await query.edit_message_text("❌ Помилка: студент не вибраний.")
            return ConversationHandler.END

        if action == "approve":
            # Підтверджуємо студента
            success = self.auth_service.confirm_user(user_id)
            if success:
                await query.edit_message_text("✅ Студента успішно підтверджено!")
            else:
                await query.edit_message_text("❌ Помилка при підтвердженні студента.")

            # Повертаємося до списку студентів
            return await self.view_registration_requests(update, context)

        elif action == "delete":
            # Підтверджуємо видалення
            keyboard = [
                [
                    InlineKeyboardButton("✅ Так, видалити", callback_data=f"confirm_delete_{user_id}"),
                    InlineKeyboardButton("❌ Ні, скасувати", callback_data=f"cancel_delete")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "❓ Ви впевнені, що хочете видалити цього студента?",
                reply_markup=reply_markup
            )

            return self.WAITING_FOR_APPROVAL_ACTION

        elif action == "confirm":
            if "delete" in query.data:
                # Видаляємо студента
                success = self.auth_service.delete_user(user_id)
                if success:
                    await query.edit_message_text("✅ Студента успішно видалено!")
                else:
                    await query.edit_message_text("❌ Помилка при видаленні студента.")

                # Повертаємося до списку студентів
                return await self.view_registration_requests(update, context)

        elif action == "cancel":
            # Повертаємося до деталей студента
            return await self.select_student(update, context)

        elif action == "edit":
            # Переходимо до редагування студента
            keyboard = [
                [InlineKeyboardButton("Ім'я", callback_data="edit_field_name")],
                [InlineKeyboardButton("Телефон", callback_data="edit_field_phone")],
                [InlineKeyboardButton("Група", callback_data="edit_field_group")],
                [InlineKeyboardButton("Рік вступу", callback_data="edit_field_year")],
                [InlineKeyboardButton("↩️ Назад", callback_data="back_to_student")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "✏️ Виберіть поле для редагування:",
                reply_markup=reply_markup
            )

            return self.WAITING_FOR_EDIT_FIELD

        return self.WAITING_FOR_APPROVAL_ACTION

    async def select_edit_field(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір поля для редагування."""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_student":
            # Повертаємося до деталей студента
            return await self.select_student(update, context)

        field_name = query.data.split("_")[-1]
        context.user_data["edit_field"] = field_name

        field_labels = {
            "name": "ім'я",
            "phone": "номер телефону",
            "group": "групу",
            "year": "рік вступу"
        }

        await query.edit_message_text(f"Введіть нове {field_labels.get(field_name, field_name)}:")

        # Вибираємо наступний стан залежно від поля
        if field_name == "name":
            return self.WAITING_FOR_NEW_USERNAME
        elif field_name == "phone":
            return self.WAITING_FOR_NEW_PHONE
        elif field_name == "group":
            # Якщо редагуємо групу, показуємо список доступних груп
            groups = self.auth_service.get_student_groups()

            keyboard = []
            for group_id, group_name in groups:
                keyboard.append([InlineKeyboardButton(group_name, callback_data=f"group_{group_id}")])

            keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_edit")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "Виберіть нову групу:",
                reply_markup=reply_markup
            )

            return self.WAITING_FOR_NEW_GROUP
        elif field_name == "year":
            return self.WAITING_FOR_NEW_ADMISSION_YEAR

        # За замовчуванням повертаємося до вибору поля
        return self.WAITING_FOR_EDIT_FIELD

    async def process_new_username(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введене нове ім'я."""
        user_id = context.user_data.get("selected_user_id")
        new_username = update.message.text.strip()

        # Оновлюємо ім'я користувача
        success = self.auth_service.update_student_info(user_id, {"username": new_username})

        if success:
            await update.message.reply_text(f"✅ Ім'я успішно змінено на '{new_username}'")
        else:
            await update.message.reply_text("❌ Помилка при оновленні імені.")

        # Повертаємося до списку студентів
        return await self.view_registration_requests(update, context)

    async def process_new_phone(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введений новий номер телефону."""
        user_id = context.user_data.get("selected_user_id")
        new_phone = update.message.text.strip()

        # Оновлюємо номер телефону
        success = self.auth_service.update_student_info(user_id, {"phone_number": new_phone})

        if success:
            await update.message.reply_text(f"✅ Номер телефону успішно змінено на '{new_phone}'")
        else:
            await update.message.reply_text("❌ Помилка при оновленні номера телефону.")

        # Повертаємося до списку студентів
        return await self.view_registration_requests(update, context)

    async def process_new_group(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір нової групи."""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_edit":
            # Повертаємося до вибору поля для редагування
            keyboard = [
                [InlineKeyboardButton("Ім'я", callback_data="edit_field_name")],
                [InlineKeyboardButton("Телефон", callback_data="edit_field_phone")],
                [InlineKeyboardButton("Група", callback_data="edit_field_group")],
                [InlineKeyboardButton("Рік вступу", callback_data="edit_field_year")],
                [InlineKeyboardButton("↩️ Назад", callback_data="back_to_student")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "✏️ Виберіть поле для редагування:",
                reply_markup=reply_markup
            )

            return self.WAITING_FOR_EDIT_FIELD

        user_id = context.user_data.get("selected_user_id")
        group_id = int(query.data.split("_")[1])

        # Оновлюємо групу
        success = self.auth_service.update_student_info(user_id, {"group_id": group_id})

        if success:
            # Знаходимо назву групи
            groups = self.auth_service.get_student_groups()
            group_name = next((name for id, name in groups if id == group_id), "Невідома")

            await query.edit_message_text(f"✅ Групу успішно змінено на '{group_name}'")
        else:
            await query.edit_message_text("❌ Помилка при оновленні групи.")

        # Повертаємося до списку студентів
        return await self.view_registration_requests(update, context)

    async def process_new_admission_year(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введений новий рік вступу."""
        user_id = context.user_data.get("selected_user_id")

        try:
            new_year = int(update.message.text.strip())

            # Перевірка на розумні межі року
            current_year = 2025  # Можна отримати поточний рік з datetime.now().year
            if new_year < 2000 or new_year > current_year:
                await update.message.reply_text("❌ Введіть коректний рік вступу (між 2000 та поточним роком).")
                return self.WAITING_FOR_NEW_ADMISSION_YEAR

            # Оновлюємо рік вступу
            success = self.auth_service.update_student_info(user_id, {"admission_year": new_year})

            if success:
                await update.message.reply_text(f"✅ Рік вступу успішно змінено на '{new_year}'")
            else:
                await update.message.reply_text("❌ Помилка при оновленні року вступу.")

            # Повертаємося до списку студентів
            return await self.view_registration_requests(update, context)

        except ValueError:
            await update.message.reply_text("❌ Введіть рік числом (наприклад, 2023).")
            return self.WAITING_FOR_NEW_ADMISSION_YEAR