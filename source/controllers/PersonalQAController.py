from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, CallbackContext, filters
)

class PersonalQAController:
    def __init__(self, application, personal_qa_service, auth_service):
        self.application = application
        self.personal_qa_service = personal_qa_service
        self.auth_service = auth_service

        # Стани розмови для студента
        self.WAITING_FOR_QUESTION_TEXT = 1
        self.WAITING_FOR_QUESTION_CONFIRMATION = 2

        # Стани розмови для працівника деканату
        self.VIEWING_QUESTIONS_LIST = 3
        self.WAITING_FOR_ANSWER_TEXT = 4
        self.WAITING_FOR_ANSWER_CONFIRMATION = 5

    def register_handlers(self):
        """Реєстрація обробників для функціоналу персональних запитань."""
        return [
            # Обробник для студентів
            ConversationHandler(
                entry_points=[
                    CommandHandler("ask_question", self.start_question_creation),
                    MessageHandler(filters.Regex('^Поставити питання$'), self.start_question_creation),
                ],
                states={
                    self.WAITING_FOR_QUESTION_TEXT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_question_text)
                    ],
                    self.WAITING_FOR_QUESTION_CONFIRMATION: [
                        CallbackQueryHandler(self.confirm_question, pattern="^confirm_question$"),
                        CallbackQueryHandler(self.cancel_question, pattern="^cancel_question$")
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel_question_creation)]
            ),

            # Обробник для працівників деканату
            ConversationHandler(
                entry_points=[
                    CommandHandler("view_questions", self.view_student_questions),
                    MessageHandler(filters.Regex('^Персональні питання студентів$'), self.view_student_questions),
                ],
                states={
                    self.VIEWING_QUESTIONS_LIST: [
                        CallbackQueryHandler(self.show_question_details, pattern="^question_(\d+)$")
                    ],
                    self.WAITING_FOR_ANSWER_TEXT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_answer_text)
                    ],
                    self.WAITING_FOR_ANSWER_CONFIRMATION: [
                        CallbackQueryHandler(self.confirm_answer, pattern="^confirm_answer$"),
                        CallbackQueryHandler(self.cancel_answer, pattern="^cancel_answer$")
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel_answer_creation)]
            ),
        ]

    # Функції для створення запитання (студент)
    async def start_question_creation(self, update: Update, context: CallbackContext) -> int:
        """Розпочинає процес створення персонального запитання."""
        await update.effective_message.reply_text(
            "Будь ласка, напишіть ваше запитання до деканату. "
            "Будьте конкретними та надайте всю необхідну інформацію для отримання точної відповіді."
        )

        # Ініціалізуємо дані користувача
        if not context.user_data.get('question_data'):
            context.user_data['question_data'] = {}

        return self.WAITING_FOR_QUESTION_TEXT

    async def process_question_text(self, update: Update, context: CallbackContext) -> int:
        """Обробляє текст запитання від студента."""
        question_text = update.message.text

        # Зберігаємо текст запитання
        context.user_data['question_data']['text'] = question_text

        # Створюємо клавіатуру для підтвердження
        keyboard = [
            [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_question")],
            [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_question")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_message.reply_text(
            f"Ваше запитання:\n\n{question_text}\n\n"
            f"Все правильно? Підтвердіть надсилання.",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_QUESTION_CONFIRMATION

    async def confirm_question(self, update: Update, context: CallbackContext) -> int:
        """Підтверджує та зберігає запитання."""
        query = update.callback_query
        await query.answer()

        chat_id = update.effective_user.id
        question_text = context.user_data['question_data']['text']

        user = await self.auth_service.get_user_by_chat_id(chat_id)
        user_id = user.UserID
        # Зберігаємо запитання в базі даних
        result = self.personal_qa_service.submit_question(user_id, question_text)

        if result['success']:
            await query.edit_message_text(
                f"✅ Ваше запитання успішно відправлено до деканату!\n\n"
                f"Ви отримаєте повідомлення, коли на ваше запитання буде надано відповідь."
            )
        else:
            await query.edit_message_text(
                f"❌ Не вдалося відправити запитання: {result['message']}\n\n"
                f"Спробуйте ще раз пізніше."
            )

        # Очищаємо дані
        context.user_data.pop('question_data', None)

        return ConversationHandler.END

    async def cancel_question(self, update: Update, context: CallbackContext) -> int:
        """Скасовує створення запитання."""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "❌ Створення запитання скасовано."
        )

        # Очищаємо дані
        context.user_data.pop('question_data', None)

        return ConversationHandler.END

    async def cancel_question_creation(self, update: Update, context: CallbackContext) -> int:
        """Обробник команди /cancel для скасування створення запитання."""
        await update.effective_message.reply_text(
            "❌ Створення запитання скасовано."
        )

        # Очищаємо дані
        context.user_data.pop('question_data', None)

        return ConversationHandler.END

    # Функції для відповіді на запитання (працівник деканату)
    async def view_student_questions(self, update: Update, context: CallbackContext) -> int:
        """Показує список невідповідених запитань студентів."""
        # Перевіряємо, чи має користувач роль dean_office
        chat_id = update.effective_user.id
        user = await self.auth_service.get_user_by_chat_id(chat_id)

        if not user or user.Role != 'dean_office':
            await update.effective_message.reply_text(
                "❌ У вас немає доступу до цієї функції."
            )
            return ConversationHandler.END

        # Отримуємо список запитань
        questions = self.personal_qa_service.get_pending_questions()

        if not questions:
            await update.effective_message.reply_text(
                "На даний момент немає невідповідених запитань від студентів."
            )
            return ConversationHandler.END

        # Створюємо кнопки для кожного запитання
        keyboard = []
        for question in questions:
            button_text = f"{question['short_text']}"

            # Створюємо кнопку
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"question_{question['id']}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_message.reply_text(
            "📝 Список невідповідених запитань від студентів:\n"
            "Виберіть запитання, щоб надати відповідь:",
            reply_markup=reply_markup
        )

        return self.VIEWING_QUESTIONS_LIST

    async def show_question_details(self, update: Update, context: CallbackContext) -> int:
        """Показує детальну інформацію про вибране запитання."""
        query = update.callback_query
        await query.answer()

        # Отримуємо ID запитання з callback_data
        question_id = int(query.data.split('_')[1])

        # Зберігаємо ID запитання для подальшого використання
        context.user_data['answer_data'] = {'question_id': question_id}

        # Отримуємо детальну інформацію про запитання
        question_details = self.personal_qa_service.get_question_details(question_id)

        if not question_details:
            await query.edit_message_text(
                "❌ Не вдалося отримати інформацію про запитання. Спробуйте ще раз."
            )
            return ConversationHandler.END

        # Формуємо повідомлення з детальною інформацією
        message = (
            f"📝 <b>Запитання №{question_details['id']}</b>\n\n"
            f"<b>Студент:</b> {question_details['user_name']} (@{question_details['telegram_tag']})\n"
        )

        # Додаємо інформацію про групу, якщо доступна
        if 'group' in question_details:
            message += f"<b>Група:</b> {question_details['group']}\n"

        message += (
            f"<b>Час створення:</b> {question_details['timestamp']}\n\n"
            f"<b>Текст запитання:</b>\n{question_details['question_text']}\n\n"
            f"📝 Будь ласка, напишіть вашу відповідь на це запитання."
        )

        await query.edit_message_text(
            message,
            parse_mode="HTML"
        )

        return self.WAITING_FOR_ANSWER_TEXT

    async def process_answer_text(self, update: Update, context: CallbackContext) -> int:
        """Обробляє текст відповіді від працівника деканату."""
        answer_text = update.message.text

        # Зберігаємо текст відповіді
        context.user_data['answer_data']['text'] = answer_text

        # Створюємо клавіатуру для підтвердження
        keyboard = [
            [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_answer")],
            [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_answer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_message.reply_text(
            f"Ваша відповідь:\n\n{answer_text}\n\n"
            f"Все правильно? Підтвердіть надсилання.",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_ANSWER_CONFIRMATION

    async def confirm_answer(self, update: Update, context: CallbackContext) -> int:
        """Підтверджує та зберігає відповідь."""
        query = update.callback_query
        await query.answer()

        chat_id = update.effective_user.id
        question_id = context.user_data['answer_data']['question_id']
        answer_text = context.user_data['answer_data']['text']

        # Отримуємо ID користувача
        user = await self.auth_service.get_user_by_chat_id(chat_id)

        if not user:
            await query.edit_message_text(
                "❌ Помилка автентифікації. Спробуйте ще раз."
            )
            return ConversationHandler.END

        # Зберігаємо відповідь в базі даних
        result = self.personal_qa_service.answer_question(question_id, answer_text, user.UserID)

        if result['success']:
            await query.edit_message_text(
                "✅ Відповідь успішно збережена та відправлена студенту!"
            )

            # Якщо є chat_id студента, відправляємо йому повідомлення про відповідь
            if result.get('student_chat_id'):
                try:
                    # Отримуємо деталі запитання, щоб включити його в повідомлення
                    question_details = self.personal_qa_service.get_question_details(question_id)

                    if question_details:
                        student_message = (
                            f"📬 <b>Відповідь на ваше запитання</b>\n\n"
                            f"<b>Ваше запитання:</b>\n{question_details['question_text']}\n\n"
                            f"<b>Відповідь від деканату:</b>\n{answer_text}"
                        )

                        await context.bot.send_message(
                            chat_id=result['student_chat_id'],
                            text=student_message,
                            parse_mode="HTML"
                        )
                except Exception as e:
                    # Логуємо помилку, але не повідомляємо користувача
                    print(f"Помилка при відправці повідомлення студенту: {str(e)}")
        else:
            await query.edit_message_text(
                f"❌ Не вдалося зберегти відповідь: {result['message']}\n\n"
                f"Спробуйте ще раз пізніше."
            )

        # Очищаємо дані
        context.user_data.pop('answer_data', None)

        return ConversationHandler.END

    async def cancel_answer(self, update: Update, context: CallbackContext) -> int:
        """Скасовує створення відповіді."""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "❌ Надсилання відповіді скасовано."
        )

        # Очищаємо дані
        context.user_data.pop('answer_data', None)

        return ConversationHandler.END

    async def cancel_answer_creation(self, update: Update, context: CallbackContext) -> int:
        """Обробник команди /cancel для скасування створення відповіді."""
        await update.effective_message.reply_text(
            "❌ Надсилання відповіді скасовано."
        )

        # Очищаємо дані
        context.user_data.pop('answer_data', None)

        return ConversationHandler.END