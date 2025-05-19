from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, MessageHandler, CommandHandler, filters, CallbackQueryHandler

from source.controllers.BaseController import BaseController
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters

class DocumentController(BaseController):
    def __init__(self, application, document_service):
        super().__init__(application)  # Викликаємо конструктор базового класу
        self.document_service = document_service
        self.WAITING_FOR_SCAN_LINK = 1

    def register_handlers(self):
        """Повертає список обробників для реєстрації."""
        return [
            CallbackQueryHandler(self.select_document, pattern="^doc_select_"),
            CallbackQueryHandler(self.confirm_document_request, pattern="^doc_confirm_"),
            CallbackQueryHandler(self.cancel_document_request, pattern="^cancel_doc$"),
            CallbackQueryHandler(self.handle_document_request, pattern="^handle_request_"),
            CallbackQueryHandler(self.process_document_request, pattern="^process_doc_"),
            CallbackQueryHandler(self.reject_document_request, pattern="^reject_doc_")
        ]
    async def request_document(self, update: Update, context: CallbackContext):
        """Ініціює процес замовлення документу."""
        can_request, result = self.document_service.can_request_document(update.effective_chat.id)

        if not can_request:
            await update.message.reply_text(result)
            return

        student = result

        document_types, error_message = self.document_service.get_available_document_types()

        if error_message:
            await update.message.reply_text(error_message)
            return

        keyboard = [[InlineKeyboardButton(doc.TypeName, callback_data=f"doc_select_{doc.TypeID}")] for doc in document_types]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Оберіть тип документа, який бажаєте замовити:",
            reply_markup=reply_markup
        )

    async def select_document(self, update: Update, context: CallbackContext):
        """Обробляє вибір типу документу."""
        query = update.callback_query
        await query.answer()

        document_type_id = int(query.data.split('_')[2])

        can_request, result = self.document_service.can_request_document(update.effective_chat.id)

        if not can_request:
            await query.edit_message_text(result)
            return

        student = result
        document_type = self.document_service.document_type_repo.get_document_type_by_id(document_type_id)

        if not document_type:
            await query.edit_message_text("Помилка: обраний тип документа не знайдено.")
            return

        keyboard = [
            [InlineKeyboardButton("Підтвердити", callback_data=f"doc_confirm_{document_type_id}_{student.StudentID}")],
            [InlineKeyboardButton("Скасувати", callback_data="cancel_doc")]
        ]

        await query.edit_message_text(
            f"Ви обрали: {document_type.TypeName}\n\nБажаєте підтвердити замовлення?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def confirm_document_request(self, update: Update, context: CallbackContext):
        """Підтверджує замовлення документа."""
        query = update.callback_query
        await query.answer()

        try:
            parts = query.data.split('_')
            if len(parts) != 4:
                raise ValueError(f"Невірний формат callback_data: {query.data}")

            _, _, document_type_id_str, student_id_str = parts
            document_type_id = int(document_type_id_str)
            student_id = int(student_id_str)

            new_request, document_type = self.document_service.create_document_request(document_type_id, student_id)

            if new_request:
                await query.edit_message_text(
                    f"✅ Ваша заявка на документ **'{document_type.TypeName}'** успішно створена!\n"
                    f"📄 Номер заявки: {new_request.RequestID}\n"
                    f"⏳ Статус: В обробці"
                )
            else:
                await query.edit_message_text(document_type)

        except Exception as e:
            print(f"❌ Помилка при створенні заявки: {e}")
            await query.edit_message_text(
                "❌ Сталася помилка при створенні заявки. Спробуйте пізніше або зверніться до деканату."
            )

    async def cancel_document_request(self, update: Update, context: CallbackContext):
        """Скасовує замовлення документа."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Замовлення документа скасовано.")

    async def view_pending_requests(self, update: Update, context: CallbackContext):
        """Показує список заявок на документи для опрацювання."""
        request_details, error_message = self.document_service.get_pending_document_requests()

        if error_message:
            await update.message.reply_text(error_message)
            return

        message = "📄 Список заявок:\n\n"
        keyboard = []

        for detail in request_details:
            req = detail['request']
            user = detail['user']
            doc_type = detail['document_type']

            message += f"№ {req.RequestID}: {doc_type.TypeName}, Студент: {user.UserName}\n"
            keyboard.append([InlineKeyboardButton(f"Обрати №{req.RequestID}", callback_data=f"handle_request_{req.RequestID}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

    async def handle_document_request(self, update: Update, context: CallbackContext):
        """Обробляє вибір заявки для опрацювання."""
        query = update.callback_query
        await query.answer()

        request_id = int(query.data.split('_')[2])

        keyboard = [
            [InlineKeyboardButton("✅ Опрацювати", callback_data=f"process_doc_{request_id}")],
            [InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_doc_{request_id}")]
        ]

        await query.edit_message_text(
            f"Заявка №{request_id}: Оберіть дію:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def reject_document_request(self, update: Update, context: CallbackContext):
        """Відхиляє заявку на документ."""
        query = update.callback_query
        await query.answer()

        request_id = int(query.data.split('_')[2])

        success, chat_id, message = self.document_service.process_document_request(request_id, approve=False)

        if success:
            await context.bot.send_message(chat_id=chat_id, text=message)
            await query.edit_message_text(f"Заявка №{request_id} була відхилена.")
        else:
            await query.edit_message_text("Помилка при опрацюванні заявки.")

    async def process_document_request(self, update: Update, context: CallbackContext):
        """Опрацьовує заявку на документ."""
        query = update.callback_query
        await query.answer()

        request_id = int(query.data.split('_')[2])

        context.user_data["processing_request_id"] = request_id
        context.user_data["state"] = self.WAITING_FOR_SCAN_LINK

        await query.edit_message_text("Введіть посилання на скан документу:")

    async def receive_scan_link(self, update: Update, context: CallbackContext):
        """Обробляє отримане посилання на скан документу."""
        if context.user_data.get("state") != self.WAITING_FOR_SCAN_LINK:
            return

        request_id = context.user_data.get("processing_request_id")
        if not request_id:
            await update.message.reply_text("Виникла помилка. Спробуйте знову.")
            return

        scan_link = update.message.text.strip()

        success, chat_id, message = self.document_service.process_document_request_with_scan(
            request_id, scan_link, approve=True
        )

        if success:
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=message)
            await update.message.reply_text(f"Заявка №{request_id} була опрацьована.")
        else:
            await update.message.reply_text("Помилка при обробці заявки.")

        context.user_data.pop("state", None)
        context.user_data.pop("processing_request_id", None)

