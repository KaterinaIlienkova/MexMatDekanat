from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AnnouncementController:
    def __init__(self, application, announcement_service):
        self.application = application
        self.announcement_service = announcement_service

        # Стани розмови
        self.WAITING_FOR_RECIPIENT_TYPE = 1
        self.WAITING_FOR_TARGET_SELECTION = 2
        self.WAITING_FOR_SPECIFIC_RECIPIENTS = 3
        self.WAITING_FOR_ANNOUNCEMENT_TEXT = 4
        self.WAITING_FOR_ANNOUNCEMENT_CONFIRMATION = 5

    def register_handlers(self):
        """Реєстрація обробників для функціоналу оголошень."""
        return [
            ConversationHandler(
                entry_points=[
                    CommandHandler("start_announcement", self.start_announcement),
                    MessageHandler(filters.Regex('^Оголошення$'), self.start_announcement),
                ],
                states={
                    self.WAITING_FOR_RECIPIENT_TYPE: [
                        CallbackQueryHandler(self.select_recipient_type, pattern="^recipient_")
                    ],
                    self.WAITING_FOR_TARGET_SELECTION: [
                        CallbackQueryHandler(self.select_target, pattern="^target_")
                    ],
                    self.WAITING_FOR_SPECIFIC_RECIPIENTS: [
                        CallbackQueryHandler(self.select_specific_recipient, pattern="^select_"),
                        CallbackQueryHandler(self.finish_recipient_selection, pattern="^finish_selection$")
                    ],
                    self.WAITING_FOR_ANNOUNCEMENT_TEXT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_announcement_text)
                    ],
                    self.WAITING_FOR_ANNOUNCEMENT_CONFIRMATION: [
                        CallbackQueryHandler(self.send_announcement, pattern="^confirm_send$"),
                        CallbackQueryHandler(self.cancel_announcement, pattern="^cancel_send$")
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel_announcement_creation)]

            )
        ]

    async def start_announcement(self, update: Update, context: CallbackContext) -> int:
        """Розпочинає процес створення оголошення."""
        # Перевірка прав доступу (тільки для працівників деканату)
        user_id = update.effective_user.id
        # Реалізуйте перевірку прав тут

        keyboard = [
            [InlineKeyboardButton("Всім викладачам", callback_data="recipient_all_teachers")],
            [InlineKeyboardButton("Викладачам кафедри", callback_data="recipient_department_teachers")],
            [InlineKeyboardButton("Окремим викладачам", callback_data="recipient_specific_teachers")],
            [InlineKeyboardButton("Всім студентам", callback_data="recipient_all_students")],
            [InlineKeyboardButton("Студентам групи", callback_data="recipient_group_students")],
            [InlineKeyboardButton("Студентам спеціальності", callback_data="recipient_specialty_students")],
            [InlineKeyboardButton("Студентам курсу", callback_data="recipient_course_year_students")],
            [InlineKeyboardButton("Студентам, що вивчають предмет", callback_data="recipient_course_enrollment_students")],
            [InlineKeyboardButton("Окремим студентам", callback_data="recipient_specific_students")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await update.effective_message.reply_text(
            "Кому бажаєте надіслати оголошення?",
            reply_markup=reply_markup
        )

        # Зберігаємо ID повідомлення для можливого оновлення
        if not context.user_data.get('announcement_data'):
            context.user_data['announcement_data'] = {}

        context.user_data['announcement_data']['message_id'] = message.message_id
        return self.WAITING_FOR_RECIPIENT_TYPE

    async def select_recipient_type(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір типу отримувачів."""
        query = update.callback_query
        await query.answer()

        recipient_type = query.data.split('_', 1)[1]

        # Зберігаємо обраний тип отримувачів
        context.user_data['announcement_data']['recipient_type'] = recipient_type

        # Залежно від типу отримувачів переходимо до наступного кроку
        if recipient_type == "all_teachers" or recipient_type == "all_students":
            # Для випадків, коли не потрібно додаткового вибору
            recipients_count = self.announcement_service.get_recipients_count(recipient_type)

            context.user_data['announcement_data']['recipients_count'] = recipients_count

            await query.edit_message_text(
                f"Обрано: {self._get_recipient_type_name(recipient_type)}\n"
                f"Кількість отримувачів: {recipients_count}\n\n"
                "Введіть текст оголошення:"
            )
            return self.WAITING_FOR_ANNOUNCEMENT_TEXT

        elif recipient_type == "department_teachers":
            # Отримуємо список кафедр
            departments = self.announcement_service.get_departments_list()
            keyboard = [
                [InlineKeyboardButton(dept['name'], callback_data=f"target_{dept['department_id']}")]
                for dept in departments
            ]

        elif recipient_type == "group_students":
            # Отримуємо список груп
            groups = self.announcement_service.get_student_groups_list()
            keyboard = [
                [InlineKeyboardButton(group['group_name'], callback_data=f"target_{group['group_id']}")]
                for group in groups
            ]

        elif recipient_type == "specialty_students":
            # Отримуємо список спеціальностей
            specialties = self.announcement_service.get_specialties_list()
            keyboard = [
                [InlineKeyboardButton(spec['name'], callback_data=f"target_{spec['specialty_id']}")]
                for spec in specialties
            ]

        elif recipient_type == "course_year_students":
            # Отримуємо список курсів
            course_years = self.announcement_service.get_course_years_list()
            keyboard = [
                [InlineKeyboardButton(course['name'], callback_data=f"target_{course['course_year']}")]
                for course in course_years
            ]

        elif recipient_type == "course_enrollment_students":
            # Отримуємо список курсів (предметів)
            courses = self.announcement_service.get_courses_list()
            keyboard = [
                [InlineKeyboardButton(f"{course['name']} ({course['teacher']})", callback_data=f"target_{course['course_id']}")]
                for course in courses
            ]

        elif recipient_type == "specific_teachers":
            # Отримуємо список викладачів для індивідуального вибору
            teachers = self.announcement_service.get_teachers_list()
            context.user_data['announcement_data']['available_recipients'] = teachers
            context.user_data['announcement_data']['selected_recipients'] = []

            # Відображаємо перших 10 викладачів
            keyboard = self._get_specific_recipients_keyboard(teachers[:10], "teacher", 0)

        elif recipient_type == "specific_students":
            # Отримуємо список студентів для індивідуального вибору
            students = self.announcement_service.get_students_list()
            context.user_data['announcement_data']['available_recipients'] = students
            context.user_data['announcement_data']['selected_recipients'] = []

            # Відображаємо перших 10 студентів
            keyboard = self._get_specific_recipients_keyboard(students[:10], "student", 0)

        # Додаємо кнопку скасування
        keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        if recipient_type in ["specific_teachers", "specific_students"]:
            await query.edit_message_text(
                f"Оберіть {self._get_recipient_type_name(recipient_type)}:",
                reply_markup=reply_markup
            )
            return self.WAITING_FOR_SPECIFIC_RECIPIENTS
        else:
            await query.edit_message_text(
                f"Оберіть групу для {self._get_recipient_type_name(recipient_type)}:",
                reply_markup=reply_markup
            )
            return self.WAITING_FOR_TARGET_SELECTION

    def _get_specific_recipients_keyboard(self, recipients: List[Dict[str, Any]], recipient_type: str, page: int) -> List[List[InlineKeyboardButton]]:
        """Створює клавіатуру для вибору конкретних отримувачів."""
        keyboard = []

        # Створюємо кнопки для кожного отримувача
        for recipient in recipients:
            if recipient_type == "teacher":
                name = f"{recipient['name']} ({recipient['department'] or 'без кафедри'})"
                recipient_id = recipient['teacher_id']
            else:  # студент
                name = f"{recipient['name']} ({recipient['group']})"
                recipient_id = recipient['student_id']

            keyboard.append([InlineKeyboardButton(name, callback_data=f"select_{recipient_type}_{recipient_id}")])

        # Додаємо навігаційні кнопки та кнопку завершення вибору
        nav_buttons = []

        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"page_{recipient_type}_{page-1}"))

        if len(recipients) == 10:  # Припускаємо, що на сторінці показуємо 10 елементів
            nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"page_{recipient_type}_{page+1}"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("✅ Завершити вибір", callback_data="finish_selection")])

        return keyboard

    async def select_target(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір конкретної цільової групи."""
        query = update.callback_query
        await query.answer()

        target_id = int(query.data.split('_')[1])
        recipient_type = context.user_data['announcement_data']['recipient_type']

        # Зберігаємо ID цільової групи
        context.user_data['announcement_data']['target_id'] = target_id

        # Отримуємо кількість отримувачів
        recipients_count = self.announcement_service.get_recipients_count(recipient_type, target_id=target_id)
        context.user_data['announcement_data']['recipients_count'] = recipients_count

        # Отримуємо назву цільової групи
        target_name = self._get_target_name(recipient_type, target_id)
        context.user_data['announcement_data']['target_name'] = target_name

        await query.edit_message_text(
            f"Обрано: {self._get_recipient_type_name(recipient_type)} - {target_name}\n"
            f"Кількість отримувачів: {recipients_count}\n\n"
            "Введіть текст оголошення:"
        )

        return self.WAITING_FOR_ANNOUNCEMENT_TEXT

    def _get_target_name(self, recipient_type: str, target_id: int) -> str:
        """Отримує назву цільової групи за типом і ID."""
        if recipient_type == "department_teachers":
            departments = self.announcement_service.get_departments_list()
            for dept in departments:
                if dept['department_id'] == target_id:
                    return dept['name']

        elif recipient_type == "group_students":
            groups = self.announcement_service.get_student_groups_list()
            for group in groups:
                if group['group_id'] == target_id:
                    return group['group_name']

        elif recipient_type == "specialty_students":
            specialties = self.announcement_service.get_specialties_list()
            for spec in specialties:
                if spec['specialty_id'] == target_id:
                    return spec['name']

        elif recipient_type == "course_year_students":
            return f"{target_id} курс"

        elif recipient_type == "course_enrollment_students":
            courses = self.announcement_service.get_courses_list()
            for course in courses:
                if course['course_id'] == target_id:
                    return course['name']

        return "Невідома група"

    async def select_specific_recipient(self, update: Update, context: CallbackContext) -> int:
        """Обробляє вибір конкретного отримувача."""
        query = update.callback_query
        await query.answer()

        parts = query.data.split('_')

        # Перевіряємо, чи це запит на перегортання сторінки
        if parts[0] == "page":
            recipient_type = parts[1]  # "teacher" або "student"
            page = int(parts[2])

            available_recipients = context.user_data['announcement_data']['available_recipients']
            start_idx = page * 10
            end_idx = start_idx + 10

            # Відображаємо наступну сторінку отримувачів
            keyboard = self._get_specific_recipients_keyboard(
                available_recipients[start_idx:end_idx],
                recipient_type,
                page
            )

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"Оберіть отримувачів (сторінка {page + 1}):",
                reply_markup=reply_markup
            )
            return self.WAITING_FOR_SPECIFIC_RECIPIENTS

        # Обробка вибору конкретного отримувача
        recipient_type = parts[1]  # "teacher" або "student"
        recipient_id = int(parts[2])

        # Додаємо до вибраних отримувачів
        if 'selected_recipients' not in context.user_data['announcement_data']:
            context.user_data['announcement_data']['selected_recipients'] = []

        selected_recipients = context.user_data['announcement_data']['selected_recipients']

        # Перевіряємо, чи вже вибрано цього отримувача
        if recipient_id not in [r['id'] for r in selected_recipients]:
            # Знаходимо інформацію про отримувача
            available_recipients = context.user_data['announcement_data']['available_recipients']

            for recipient in available_recipients:
                if recipient_type == "teacher" and recipient['teacher_id'] == recipient_id:
                    selected_recipients.append({
                        'id': recipient_id,
                        'name': recipient['name'],
                        'type': 'teacher'
                    })
                    break
                elif recipient_type == "student" and recipient['student_id'] == recipient_id:
                    selected_recipients.append({
                        'id': recipient_id,
                        'name': recipient['name'],
                        'type': 'student'
                    })
                    break

        # Оновлюємо повідомлення з вибраними отримувачами
        selected_text = "Вибрані отримувачі:\n"
        for idx, recipient in enumerate(selected_recipients, 1):
            selected_text += f"{idx}. {recipient['name']}\n"

        if not selected_recipients:
            selected_text = "Отримувачі не вибрані"

        # Відображаємо поточну сторінку отримувачів
        current_page = 0  # За замовчуванням показуємо першу сторінку
        if parts[0] == "page":
            current_page = int(parts[2])

        available_recipients = context.user_data['announcement_data']['available_recipients']
        start_idx = current_page * 10
        end_idx = start_idx + 10

        keyboard = self._get_specific_recipients_keyboard(
            available_recipients[start_idx:end_idx],
            recipient_type,
            current_page
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"{selected_text}\n\nОберіть отримувачів:",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_SPECIFIC_RECIPIENTS

    async def finish_recipient_selection(self, update: Update, context: CallbackContext) -> int:
        """Завершує вибір конкретних отримувачів."""
        query = update.callback_query
        await query.answer()

        selected_recipients = context.user_data['announcement_data'].get('selected_recipients', [])

        if not selected_recipients:
            await query.edit_message_text(
                "Ви не вибрали жодного отримувача. Спробуйте знову або скасуйте операцію."
            )
            return self.WAITING_FOR_SPECIFIC_RECIPIENTS

        # Розділяємо ID відповідно до типу отримувачів
        teacher_ids = [r['id'] for r in selected_recipients if r['type'] == 'teacher']
        student_ids = [r['id'] for r in selected_recipients if r['type'] == 'student']

        recipient_type = context.user_data['announcement_data']['recipient_type']

        # Зберігаємо ID отримувачів
        if recipient_type == "specific_teachers":
            context.user_data['announcement_data']['teacher_ids'] = teacher_ids
            recipients_count = self.announcement_service.get_recipients_count(
                recipient_type, ids_list=teacher_ids
            )
        else:  # specific_students
            context.user_data['announcement_data']['student_ids'] = student_ids
            recipients_count = self.announcement_service.get_recipients_count(
                recipient_type, ids_list=student_ids
            )

        context.user_data['announcement_data']['recipients_count'] = recipients_count

        # Формуємо список імен вибраних отримувачів
        selected_names = [r['name'] for r in selected_recipients]

        await query.edit_message_text(
            f"Вибрано {recipients_count} отримувачів:\n"
            f"{', '.join(selected_names[:5])}"
            f"{' та інші' if len(selected_names) > 5 else ''}\n\n"
            "Введіть текст оголошення:"
        )

        return self.WAITING_FOR_ANNOUNCEMENT_TEXT

    async def process_announcement_text(self, update: Update, context: CallbackContext) -> int:
        """Обробляє введений текст оголошення."""
        announcement_text = update.message.text.strip()

        if not announcement_text:
            await update.message.reply_text("Текст оголошення не може бути порожнім. Спробуйте ще раз:")
            return self.WAITING_FOR_ANNOUNCEMENT_TEXT

        # Зберігаємо текст оголошення
        context.user_data['announcement_data']['text'] = announcement_text

        # Формуємо повідомлення про підтвердження
        recipient_type = context.user_data['announcement_data']['recipient_type']
        recipients_count = context.user_data['announcement_data']['recipients_count']

        confirmation_message = "Підтвердіть відправку оголошення:\n\n"
        confirmation_message += f"Отримувачі: {self._get_recipient_type_name(recipient_type)}"

        if 'target_name' in context.user_data['announcement_data']:
            confirmation_message += f" - {context.user_data['announcement_data']['target_name']}"

        confirmation_message += f"\nКількість отримувачів: {recipients_count}\n\n"
        confirmation_message += f"Текст оголошення:\n{announcement_text}"

        keyboard = [
            [InlineKeyboardButton("✅ Підтвердити і надіслати", callback_data="confirm_send")],
            [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_send")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            confirmation_message,
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_ANNOUNCEMENT_CONFIRMATION

    async def send_announcement(self, update: Update, context: CallbackContext) -> int:
        """Відправляє оголошення вибраним отримувачам."""
        query = update.callback_query
        await query.answer()

        data = context.user_data['announcement_data']
        recipient_type = data['recipient_type']
        message_text = data['text']
        bot = context.bot

        # Відправляємо повідомлення залежно від типу отримувачів
        try:
            if recipient_type == "all_teachers":
                success_count, fail_count = await self.announcement_service.send_to_all_teachers(message_text, bot)

            elif recipient_type == "department_teachers":
                success_count, fail_count = await self.announcement_service.send_to_department_teachers(
                    data['target_id'], message_text, bot
                )

            elif recipient_type == "specific_teachers":
                success_count, fail_count = await self.announcement_service.send_to_specific_teachers(
                    data['teacher_ids'], message_text, bot
                )

            elif recipient_type == "all_students":
                success_count, fail_count = await self.announcement_service.send_to_all_students(message_text, bot)

            elif recipient_type == "group_students":
                success_count, fail_count = await self.announcement_service.send_to_group_students(
                    data['target_id'], message_text, bot
                )

            elif recipient_type == "specialty_students":
                success_count, fail_count = await self.announcement_service.send_to_specialty_students(
                    data['target_id'], message_text, bot
                )

            elif recipient_type == "course_year_students":
                success_count, fail_count = await self.announcement_service.send_to_course_year_students(
                    data['target_id'], message_text, bot
                )

            elif recipient_type == "course_enrollment_students":
                success_count, fail_count = await self.announcement_service.send_to_course_enrollment_students(
                    data['target_id'], message_text, bot
                )

            elif recipient_type == "specific_students":
                success_count, fail_count = await self.announcement_service.send_to_specific_students(
                    data['student_ids'], message_text, bot
                )

            result_message = (
                f"✅ Оголошення надіслано успішно!\n"
                f"Успішно доставлено: {success_count}\n"
                f"Помилок доставки: {fail_count}"
            )

        except Exception as e:
            logger.error(f"Помилка при відправці оголошення: {e}")
            result_message = f"❌ Сталася помилка при відправці оголошення: {str(e)}"

        # Очищаємо дані
        context.user_data.pop('announcement_data', None)

        await query.edit_message_text(result_message)
        return ConversationHandler.END


    async def cancel_announcement(self, update: Update, context: CallbackContext) -> int:
        """Скасовує відправку оголошення."""
        query = update.callback_query
        await query.answer()

        # Очищаємо дані
        context.user_data.pop('announcement_data', None)

        await query.edit_message_text("Відправка оголошення скасована.")
        return ConversationHandler.END

    async def cancel_announcement_creation(self, update: Update, context: CallbackContext) -> int:
        """Скасовує створення оголошення за командою /cancel."""
        await update.message.reply_text("Створення оголошення скасовано.")

        # Очищаємо дані
        context.user_data.pop('announcement_data', None)

        return ConversationHandler.END

    def _get_recipient_type_name(self, recipient_type: str) -> str:
        """Повертає людинозрозумілу назву типу отримувачів."""
        types = {
            "all_teachers": "Всі викладачі",
            "department_teachers": "Викладачі кафедри",
            "specific_teachers": "Окремі викладачі",
            "all_students": "Всі студенти",
            "group_students": "Студенти групи",
            "specialty_students": "Студенти спеціальності",
            "course_year_students": "Студенти курсу",
            "course_enrollment_students": "Студенти, що вивчають предмет",
            "specific_students": "Окремі студенти"
        }
        return types.get(recipient_type, recipient_type)