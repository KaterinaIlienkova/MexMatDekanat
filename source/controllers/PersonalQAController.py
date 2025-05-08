from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, CallbackContext, filters
)
from typing import List, Dict, Any, Optional

class PersonalQAController:
    def __init__(self, application, personal_qa_service,auth_service):
        self.application = application
        self.personal_qa_service = personal_qa_service
        self.auth_service =auth_service


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
                    CommandHandler("view_student_questions", self.view_student_questions),
                    MessageHandler(filters.Regex('^Питання студентів$'), self.view_student_questions),
                ],
                states={
                    self.VIEWING_QUESTIONS_LIST: [
                        CallbackQueryHandler(self.select_question_to_answer, pattern="^answer_question_"),
                        CallbackQueryHandler(self.back_to_menu, pattern="^back_to_menu$"),
                    ],
                    self.WAITING_FOR_ANSWER_TEXT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_answer_text)
                    ],
                    self.WAITING_FOR_ANSWER_CONFIRMATION: [
                        CallbackQueryHandler(self.confirm_answer, pattern="^confirm_answer$"),
                        CallbackQueryHandler(self.edit_answer, pattern="^edit_answer$"),
                        CallbackQueryHandler(self.cancel_answer, pattern="^cancel_answer$")
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel_answer_process)]
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

    # Функції для перегляду своїх запитань (студент)
    async def view_my_questions(self, update: Update, context: CallbackContext):
        """Показує список запитань студента."""
        user_id = update.effective_user.id

        # Отримуємо запитання користувача
        result = self.personal_qa_service.get_student_questions(user_id)

        if not result['success']:
            await update.effective_message.reply_text(
                f"❌ Не вдалося отримати список запитань: {result['message']}"
            )
            return

        if result['total_count'] == 0:
            await update.effective_message.reply_text(
                "У вас поки немає запитань. Використайте команду /ask_question, щоб створити нове запитання."
            )
            return

        # Показуємо спочатку невідповідені запитання
        text = "📋 <b>Ваші запитання:</b>\n\n"

        if result['pending_questions']:
            text += "<b>⏳ Очікують відповіді:</b>\n"
            for i, q in enumerate(result['pending_questions'], 1):
                formatted_date = q['timestamp'].strftime('%d.%m.%Y %H:%M')
                text += f"{i}. <i>{formatted_date}</i> - {q['question'][:50]}...\n"
                # Додаємо кнопку для перегляду деталей
                keyboard = [
                    [InlineKeyboardButton("👁️ Переглянути", callback_data=f"view_question_{q['question_id']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
                text = ""  # Очищаємо текст для наступного повідомлення

        if result['answered_questions']:
            text += "<b>✅ Отримали відповідь:</b>\n"
            for i, q in enumerate(result['answered_questions'], 1):
                formatted_date = q['timestamp'].strftime('%d.%m.%Y %H:%M')
                text += f"{i}. <i>{formatted_date}</i> - {q['question'][:50]}...\n"
                # Додаємо кнопку для перегляду деталей
                keyboard = [
                    [InlineKeyboardButton("👁️ Переглянути", callback_data=f"view_question_{q['question_id']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
                text = ""  # Очищаємо текст для наступного повідомлення

    async def view_question_details(self, update: Update, context: CallbackContext):
        """Показує деталі вибраного запитання."""
        query = update.callback_query
        await query.answer()

        # Витягуємо ID запитання з callback_data
        question_id = int(query.data.split('_')[-1])

        # Отримуємо деталі запитання
        result = self.personal_qa_service.get_question_with_context(question_id)

        if not result['success']:
            await query.edit_message_text(
                f"❌ Не вдалося отримати деталі запитання: {result['message']}"
            )
            return

        question = result['question']
        context_data = result['context']

        # Формуємо текст для відображення
        text = f"<b>📝 Запитання від {context_data['formatted_date']}:</b>\n\n"
        text += f"{question['question']}\n\n"

        if question['status'] == 'pending':
            text += f"<b>⏳ Статус:</b> Очікує відповіді\n"
            text += f"<b>⏱️ Час очікування:</b> {context_data['waiting_time']}"
        else:
            text += f"<b>✅ Статус:</b> Відповідь отримано\n"
            text += f"<b>👤 Відповів:</b> {question['answered_by_name']}\n\n"
            text += f"<b>📝 Відповідь:</b>\n{question['answer']}"

        # Додаємо кнопку для повернення до списку запитань
        keyboard = [
            [InlineKeyboardButton("🔙 Назад до списку запитань", callback_data="back_to_questions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def view_student_questions(self, update: Update, context: CallbackContext) -> int:
        """Показує список запитань від студентів для працівників деканату."""
        user_id = update.effective_user.id

        # Показуємо список запитань
        await self.show_questions_list(update, context)

        return self.VIEWING_QUESTIONS_LIST

    async def show_questions_list(self, update: Update, context: CallbackContext):
        """Функція для відображення списку запитань без пагінації."""

        # Отримуємо всі невідповідені запитання
        result = self.personal_qa_service.get_all_unanswered_questions()

        if not result['success']:
            await update.effective_message.reply_text(
                f"❌ Не вдалося отримати список запитань: {result['message']}"
            )
            return

        questions = result['questions']

        if not questions:
            text = "🎉 Наразі немає невідповідених запитань від студентів."
            keyboard = [
                [InlineKeyboardButton("🔄 Оновити", callback_data="refresh_questions")],
                [InlineKeyboardButton("🔙 Повернутися до меню", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if isinstance(update.callback_query, object):
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await update.effective_message.reply_text(text, reply_markup=reply_markup)
            return

        # Формуємо текст повідомлення
        text = "📋 <b>Невідповідені запитання</b>:\n\n"

        # Додаємо кнопки для кожного запитання
        keyboard = []
        for q in questions:
            text += f"👤 <b>{q['student_name']}</b> ({q['formatted_date']}):\n{q['short_question']}\n\n"

            # Кнопка для відповіді на запитання
            keyboard.append([InlineKeyboardButton(
                f"✍️ Відповісти {q['student_name']}",
                callback_data=f"answer_question_{q['question_id']}"
            )])

        # Кнопки навігації
        keyboard.append([InlineKeyboardButton("🔄 Оновити", callback_data="refresh_questions")])
        keyboard.append([InlineKeyboardButton("🔙 Повернутися до меню", callback_data="back_to_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        if isinstance(update.callback_query, object):
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def refresh_questions(self, update: Update, context: CallbackContext) -> int:
        """Оновлює список запитань."""
        query = update.callback_query
        await query.answer()

        # Показуємо актуальний список запитань
        await self.show_questions_list(update, context)

        return self.VIEWING_QUESTIONS_LIST

    async def select_question_to_answer(self, update: Update, context: CallbackContext) -> int:
            """Вибір запитання для відповіді."""
            query = update.callback_query
            await query.answer()

            # Витягуємо ID запитання з callback_data
            question_id = int(query.data.split('_')[-1])
            context.user_data['selected_question_id'] = question_id

            # Отримуємо деталі запитання
            result = self.personal_qa_service.get_question_with_context(question_id)

            if not result['success']:
                await query.edit_message_text(
                    f"❌ Не вдалося отримати деталі запитання: {result['message']}"
                )
                return self.VIEWING_QUESTIONS_LIST

            question = result['question']
            context_data = result['context']

            # Формуємо текст для відображення
            text = f"<b>📝 Запитання від студента {question['student_name']} ({question['student_telegram']}):</b>\n\n"
            text += f"{question['question']}\n\n"

            text += f"<b>📅 Дата створення:</b> {context_data['formatted_date']}\n"
            text += f"<b>⏱️ Час очікування:</b> {context_data['waiting_time']}"

            if context_data['is_urgent']:
                text += " <b>(Термінове!)</b>"

            text += "\n\nБудь ласка, напишіть вашу відповідь на це запитання:"

            await query.edit_message_text(text, parse_mode='HTML')

            return self.WAITING_FOR_ANSWER_TEXT

    async def process_answer_text(self, update: Update, context: CallbackContext) -> int:
        """Обробляє текст відповіді від працівника деканату."""
        answer_text = update.message.text

        # Зберігаємо текст відповіді
        context.user_data['answer_text'] = answer_text

        # Створюємо клавіатуру для підтвердження
        keyboard = [
            [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_answer")],
            [InlineKeyboardButton("✏️ Редагувати", callback_data="edit_answer")],
            [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_answer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_message.reply_text(
            f"Ваша відповідь:\n\n{answer_text}\n\n"
            f"Все правильно? Підтвердіть надсилання або відредагуйте текст.",
            reply_markup=reply_markup
        )

        return self.WAITING_FOR_ANSWER_CONFIRMATION

    async def confirm_answer(self, update: Update, context: CallbackContext) -> int:
        """Підтверджує та зберігає відповідь."""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        question_id = context.user_data['selected_question_id']
        answer_text = context.user_data['answer_text']

        # Зберігаємо відповідь в базі даних
        result = self.personal_qa_service.provide_answer(question_id, user_id, answer_text)

        if result['success']:
            await query.edit_message_text(
                f"✅ Ваша відповідь успішно збережена!\n\n"
                f"Студент отримає повідомлення про вашу відповідь."
            )

            # Надсилаємо повідомлення студенту про нову відповідь
            if 'student_notification' in result:
                notification = result['student_notification']
                try:
                    await self.application.bot.send_message(
                        chat_id=notification['chat_id'],
                        text=notification['message'],
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Failed to send notification to student: {str(e)}")
        else:
            await query.edit_message_text(
                f"❌ Не вдалося зберегти відповідь: {result['message']}\n\n"
                f"Спробуйте ще раз пізніше."
            )

        # Очищаємо дані
        for key in ['selected_question_id', 'answer_text']:
            context.user_data.pop(key, None)

        return ConversationHandler.END

    async def edit_answer(self, update: Update, context: CallbackContext) -> int:
        """Дозволяє відредагувати текст відповіді."""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "Будь ласка, напишіть вашу відповідь ще раз."
        )

        return self.WAITING_FOR_ANSWER_TEXT

    async def cancel_answer(self, update: Update, context: CallbackContext) -> int:
        """Скасовує процес відповіді."""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "❌ Надсилання відповіді скасовано."
        )

        # Очищаємо дані
        for key in ['selected_question_id', 'answer_text']:
            context.user_data.pop(key, None)

        return ConversationHandler.END

    async def cancel_answer_process(self, update: Update, context: CallbackContext) -> int:
        """Обробник команди /cancel для скасування процесу відповіді."""
        await update.effective_message.reply_text(
            "❌ Надсилання відповіді скасовано."
        )

        # Очищаємо дані
        for key in ['selected_question_id', 'answer_text']:
            context.user_data.pop(key, None)

        return ConversationHandler.END

    async def back_to_menu(self, update: Update, context: CallbackContext) -> int:
        """Повертає до головного меню."""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "Ви повернулись до головного меню. Виберіть потрібну опцію з меню нижче."
        )

        return ConversationHandler.END

