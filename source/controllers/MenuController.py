from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters

from source.controllers.BaseController import BaseController
import logging

logger = logging.getLogger(__name__)

class MenuController(BaseController):
    def __init__(self, application,document_controller,faq_controller,course_controller,auth_controller,announcement_controller, pqa_controller ):
        super().__init__(application)
        self.button_handlers = {}
        self.document_controller = document_controller
        self.faq_controller = faq_controller
        self.course_controller = course_controller
        self.auth_controller = auth_controller
        self.announcement_controller = announcement_controller
        self.pqa_controller = pqa_controller

    def register_handlers(self):
        self.button_handlers = {
            "Додати користувача": self.auth_controller.add_user,
            "Видалити користувача": self.auth_controller.delete_user,
            "Q&A": self.faq_controller.send_qa,
            "Поставити питання": self.pqa_controller.start_question_creation,
            "Персональні питання студентів": self.pqa_controller.view_student_questions,
            "Редагувати Q&A": self.faq_controller.show_edit_qa_options,
            "Оголошення": self.announcement_controller.start_announcement,
            "Підтвердити реєстрацію": self.auth_controller.view_registration_requests,
            "Мої поточні курси": self.course_controller.view_student_courses,
            "Списки студентів": self.course_controller.view_students,
            "Замовити документ": self.document_controller.request_document,
            "Заявки на документи": self.document_controller.view_pending_requests,
            "Мої курси": self.course_controller.view_teacher_courses
        }

        self.application.add_handler(CommandHandler("start", self.start))
        # Register document controller handlers first
        self.document_controller.register_handlers()

        # Register announcement controller handlers
        for handler in self.announcement_controller.register_handlers():
            self.application.add_handler(handler)

        for handler in self.pqa_controller.register_handlers():
            self.application.add_handler(handler)

        for handler in self.auth_controller.register_handlers():
            self.application.add_handler(handler)

        course_handlers = self.course_controller.register_handlers()
        for handler in course_handlers:
            self.application.add_handler(handler)


        # Then register menu handlers

        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def start(self, update: Update, context: CallbackContext):
        role = await self.auth_controller.check_registration(update, context)
        if role is None:
            return

        keyboard = self.get_keyboard(role)

        if keyboard:
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            await update.message.reply_text(
                f"Вітаю, {update.message.from_user.username}! Ви зареєстровані як {role}.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"Вітаю, {update.message.from_user.username}! Ви зареєстровані як {role}."
            )

    def get_keyboard(self, role):
        keyboards = {
            "dean_office": [
                [KeyboardButton("Додати користувача"), KeyboardButton("Видалити користувача")],
                [KeyboardButton("Редагувати Q&A"), KeyboardButton("Оголошення")],
                [KeyboardButton("Підтвердити реєстрацію"), KeyboardButton("Заявки на документи")],
                [KeyboardButton("Персональні питання студентів")]
            ],
            "student": [
                [KeyboardButton("Q&A"),KeyboardButton("Поставити питання")],
                [KeyboardButton("Мої поточні курси")],
                [KeyboardButton("Замовити документ")]
            ],
            "teacher": [
                [KeyboardButton("Списки студентів")],
                [KeyboardButton("Мої курси"), KeyboardButton("Оголошення")]
            ],
        }
        return keyboards.get(role, [])


    async def handle_message(self, update: Update, context: CallbackContext):
        # Handle FAQ text inputs
        if await self.faq_controller.handle_faq_text_input(update, context):
            return

        # Handle document controller scan links
        if context.user_data.get("state") == self.document_controller.WAITING_FOR_SCAN_LINK:
            await self.document_controller.receive_scan_link(update, context)
            return

            # Перевіряємо, чи обробляємо зараз створення курсу
        if context.user_data.get("state", "").startswith("waiting_for_"):
            # Делегуємо обробку CourseController, якщо в процесі створення курсу
            await self.course_controller.handle_course_creation_input(update, context)
            return

        # Handle menu button commands
        text = update.message.text
        handler = self.button_handlers.get(text)

        if handler:
            await handler(update, context)
        else:
            await update.message.reply_text("Невідома команда.")

