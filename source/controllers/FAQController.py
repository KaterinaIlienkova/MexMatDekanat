from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, Application
from source.services import FAQService
import logging

from source.repositories.FAQRepository import FAQRepository

logger = logging.getLogger(__name__)

# Константи для стану розмови
WAITING_FOR_QUESTION = 'waiting_for_question'
WAITING_FOR_ANSWER = 'waiting_for_answer'
WAITING_FOR_EDIT_ANSWER = 'waiting_for_edit_answer'

class FAQController:
    """Контролер для роботи з FAQ в телеграм боті."""

    def __init__(self, application: Application, faq_service: FAQService):
        """
        Ініціалізує FAQController.

        Args:
            application: Об'єкт додатку telegram.
            faq_service: Сервіс для роботи з FAQ.
        """
        self.application = application
        self.faq_service = faq_service

        # Реєстрація обробників
        self.register_handlers()

    def register_handlers(self):
        """Реєструє всі обробники FAQ в додатку"""
        self.application.add_handler(CallbackQueryHandler(self.edit_qa_handler, pattern="^edit_question$|^add_question$|^delete_question$"))
        self.application.add_handler(CallbackQueryHandler(self.delete_faq_handler, pattern="^delete_faq_|^cancel_delete$"))
        self.application.add_handler(CallbackQueryHandler(self.edit_faq_callback_handler, pattern="^edit_faq_|^cancel_edit$"))
        self.application.add_handler(CallbackQueryHandler(self.faq_response, pattern="^faq_"))

    async def show_edit_qa_options(self, update: Update, context: CallbackContext):
        """Показує опції редагування Q&A."""
        keyboard = [
            [InlineKeyboardButton("Додати питання", callback_data="add_question")],
            [InlineKeyboardButton("Видалити питання", callback_data="delete_question")],
            [InlineKeyboardButton("Редагувати питання", callback_data="edit_question")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Виберіть дію для редагування Q&A:", reply_markup=reply_markup)

    async def edit_qa_handler(self, update: Update, context: CallbackContext):
        """Обробляє вибір дії редагування FAQ."""
        query = update.callback_query
        await query.answer()

        if query.data == "delete_question":
            await self.show_questions_to_delete(update, context)
        elif query.data == "add_question":
            await self.prompt_new_question(update, context)
        elif query.data == "edit_question":
            await self.show_questions_to_edit(update, context)

    async def show_questions_to_edit(self, update: Update, context: CallbackContext):
        """Відображає список питань для редагування їх відповідей."""
        query = update.callback_query

        try:
            # Отримуємо всі FAQ записи з ID
            faqs = self.faq_service.get_all_faqs_with_id()

            if not faqs:
                await query.edit_message_text("Немає доступних питань для редагування.")
                return

            # Створюємо кнопки для кожного питання
            keyboard = []
            for faq_id, question, _ in faqs:
                # Обмежуємо довжину питання для кнопки
                short_question = question[:50] + "..." if len(question) > 50 else question
                keyboard.append([InlineKeyboardButton(
                    short_question,
                    callback_data=f"edit_faq_{faq_id}"
                )])

            # Додаємо кнопку "Скасувати"
            keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_edit")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Виберіть питання, відповідь на яке ви хочете відредагувати:",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.exception(f"Помилка при відображенні питань для редагування: {e}")
            await query.edit_message_text("Сталася помилка при завантаженні питань. Спробуйте пізніше.")

    async def prompt_new_question(self, update: Update, context: CallbackContext):
        """Запитує користувача про нове питання для FAQ."""
        query = update.callback_query

        # Встановлюємо стан розмови
        context.user_data["state"] = WAITING_FOR_QUESTION

        await query.edit_message_text("Будь ласка, надішліть текст питання, яке ви хочете додати до FAQ:")

    async def show_questions_to_delete(self, update: Update, context: CallbackContext):
        """Відображає список питань для видалення з бази даних."""
        query = update.callback_query

        try:
            # Отримуємо всі FAQ записи з ID
            faqs = self.faq_service.get_all_faqs_with_id()

            if not faqs:
                await query.edit_message_text("Немає доступних питань для видалення.")
                return

            # Створюємо кнопки для кожного питання
            keyboard = []
            for faq_id, question, _ in faqs:
                # Обмежуємо довжину питання для кнопки
                short_question = question[:50] + "..." if len(question) > 50 else question
                keyboard.append([InlineKeyboardButton(
                    short_question,
                    callback_data=f"delete_faq_{faq_id}"
                )])

            # Додаємо кнопку "Скасувати"
            keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_delete")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Виберіть питання, яке ви хочете видалити:",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.exception(f"Помилка при відображенні питань для видалення: {e}")
            await query.edit_message_text("Сталася помилка при завантаженні питань. Спробуйте пізніше.")

    async def delete_faq_handler(self, update: Update, context: CallbackContext):
        """Обробляє видалення обраного FAQ."""
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == "cancel_delete":
            await query.edit_message_text("Видалення скасовано.")
            return

        # Отримуємо ID питання з callback_data
        try:
            faq_id = int(callback_data.split("_")[-1])

            # Видаляємо FAQ з бази даних
            success = self.faq_service.remove_faq(faq_id)

            if success:
                await query.edit_message_text("Питання успішно видалено.")
            else:
                await query.edit_message_text("Не вдалося видалити питання. Спробуйте пізніше.")
        except ValueError:
            await query.edit_message_text("Некоректний формат ідентифікатора питання.")
        except Exception as e:
            logger.exception(f"Помилка при видаленні FAQ: {e}")
            await query.edit_message_text("Сталася помилка при видаленні питання.")

    async def edit_faq_callback_handler(self, update: Update, context: CallbackContext):
        """Обробляє вибір питання для редагування."""
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == "cancel_edit":
            await query.edit_message_text("Редагування скасовано.")
            return

        # Отримуємо ID питання з callback_data
        try:
            faq_id = int(callback_data.split("_")[-1])

            # Зберігаємо ID питання в контексті користувача
            context.user_data["edit_faq_id"] = faq_id

            # Отримуємо текст питання та відповідь
            faqs = self.faq_service.get_all_faqs_with_id()
            selected_faq = next((faq for faq in faqs if faq[0] == faq_id), None)

            if selected_faq:
                question_text = selected_faq[1]
                answer_text = selected_faq[2]

                # Зберігаємо питання для подальшого використання
                context.user_data["edit_question_text"] = question_text

                # Встановлюємо стан розмови
                context.user_data["state"] = WAITING_FOR_EDIT_ANSWER

                # Показуємо поточну відповідь та запитуємо нову
                await query.edit_message_text(
                    f"Питання: {question_text}\n\n"
                    f"Поточна відповідь: {answer_text}\n\n"
                    "Будь ласка, надішліть нову відповідь на це питання. "
                    "Або напишіть /cancel щоб скасувати редагування."
                )
            else:
                await query.edit_message_text("Питання не знайдено у базі даних.")
        except ValueError:
            await query.edit_message_text("Некоректний формат ідентифікатора питання.")
        except Exception as e:
            logger.exception(f"Помилка при підготовці до редагування FAQ: {e}")
            await query.edit_message_text("Сталася помилка при підготовці до редагування.")

    async def send_qa(self, update: Update, context: CallbackContext):
        """Надсилає список частих запитань студенту."""
        faqs = self.faq_service.get_all_faqs()

        if not faqs:
            await update.message.reply_text("Наразі немає доступних запитань.")
            return

        # Зберігаємо список FAQ у контексті користувача
        context.user_data["faqs"] = faqs
        logger.debug("Збережено запитання: %s", faqs)  # Логування для перевірки

        # Створюємо кнопки для кожного питання
        keyboard = [
            [InlineKeyboardButton(question, callback_data=f"faq_{i}")]
            for i, (question, _) in enumerate(faqs)
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Оберіть питання:", reply_markup=reply_markup)

    async def faq_response(self, update: Update, context: CallbackContext):
        """Надсилає відповідь на вибране студентом запитання."""
        query = update.callback_query

        # Перевіряємо наявність callback-запиту
        if not query:
            return

        # Показуємо індикатор завантаження
        await query.answer()

        # Перевіряємо, чи це запит FAQ
        if not query.data or not query.data.startswith("faq_"):
            return

        # Отримуємо дані з бази
        faqs = self.faq_service.get_all_faqs()

        if not faqs:
            await query.message.reply_text("Наразі немає доступних запитань.")
            return

        try:
            # Отримуємо індекс вибраного запитання
            index = int(query.data.split("_")[1])

            if 0 <= index < len(faqs):
                question, answer = faqs[index]

                # Відправляємо відповідь
                await query.message.reply_text(
                    f"*{question}*\n\n{answer}",
                    parse_mode="Markdown"
                )
            else:
                await query.message.reply_text("Невірний індекс запитання.")
        except Exception as e:
            await query.message.reply_text("Помилка при обробці запиту.")

    async def handle_faq_text_input(self, update: Update, context: CallbackContext):
        """Обробляє текстові повідомлення для додавання або редагування FAQ"""
        state = context.user_data.get("state")

        if state == WAITING_FOR_QUESTION:
            # Зберігаємо питання і просимо відповідь
            context.user_data["new_question"] = update.message.text
            context.user_data["state"] = WAITING_FOR_ANSWER
            await update.message.reply_text(f"Питання збережено. Тепер надішліть відповідь на це питання:")
            return True

        elif state == WAITING_FOR_ANSWER:
            # Додаємо нове питання та відповідь
            question = context.user_data.get("new_question", "")
            answer = update.message.text

            success = self.faq_service.add_new_faq(question, answer)

            if success:
                await update.message.reply_text("✅ Питання успішно додано до FAQ!")
            else:
                await update.message.reply_text("❌ Помилка при додаванні питання.")

            # Очищаємо стан
            context.user_data.pop("state", None)
            context.user_data.pop("new_question", None)
            return True

        elif state == WAITING_FOR_EDIT_ANSWER:
            # Оновлюємо відповідь на існуюче питання
            faq_id = context.user_data.get("edit_faq_id")
            new_answer = update.message.text

            if not faq_id:
                await update.message.reply_text("Помилка: ідентифікатор питання не знайдено.")
                context.user_data.pop("state", None)
                return True

            success = self.faq_service.update_faq_answer(faq_id, new_answer)

            if success:
                await update.message.reply_text("✅ Відповідь успішно оновлено!")
            else:
                await update.message.reply_text("❌ Помилка при оновленні відповіді.")

            # Очищаємо стан
            context.user_data.pop("state", None)
            context.user_data.pop("edit_faq_id", None)
            context.user_data.pop("edit_question_text", None)
            return True

        # Якщо немає активного стану FAQ, повертаємо False
        return False


