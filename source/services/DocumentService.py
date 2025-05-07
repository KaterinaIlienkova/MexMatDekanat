from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class DocumentService:
    def __init__(self, auth_repo, document_type_repo, document_request_repo):
        self.auth_repo = auth_repo
        self.document_type_repo = document_type_repo
        self.document_request_repo = document_request_repo

    def can_request_document(self, chat_id):
        user = self.auth_repo.get_user_by_chat_id(chat_id)
        if not user or user.Role != 'student':
            return False, "Замовлення документів доступне тільки для студентів."

        student = self.auth_repo.get_student_by_user_id(user.UserID)
        if not student:
            return False, "Не вдалося знайти дані студента. Зверніться до деканату."

        return True, student

    def get_available_document_types(self):
        document_types = self.document_type_repo.get_all_document_types()
        if not document_types:
            return None, "На даний момент немає доступних типів документів для замовлення."
        return document_types, None

    def create_document_request(self, document_type_id, student_id):
        try:
            document_type = self.document_type_repo.get_document_type_by_id(document_type_id)
            if not document_type:
                return None, "Помилка: обраний тип документа не знайдено."

            new_request = self.document_request_repo.create_request(student_id, document_type_id)
            return new_request, document_type
        except Exception as e:
            print(f"❌ Помилка при створенні заявки: {e}")
            return None, "❌ Сталася помилка при створенні заявки. Спробуйте пізніше або зверніться до деканату."

    def get_pending_document_requests(self):
        requests = self.document_request_repo.get_pending_requests()
        if not requests:
            return None, "Немає заявок на документи для опрацювання."

        request_details = []
        for req in requests:
            # Використовуємо StudentID з запиту для отримання об'єкта студента
            student = self.student_repo.get_student_by_id(req.StudentID)
            if not student:
                continue  # Пропускаємо цей запит, якщо студент не знайдений

            # Отримуємо користувача за UserID студента
            user = self.user_repo.get_user_by_id(student.UserID)
            if not user:
                continue  # Пропускаємо, якщо користувач не знайдений

            doc_type = self.document_type_repo.get_document_type_by_id(req.TypeID)
            if not doc_type:
                continue  # Пропускаємо, якщо тип документа не знайдений

            request_details.append({
                'request': req,
                'student': student,
                'user': user,
                'document_type': doc_type
            })

        if not request_details:
            return None, "Не вдалося отримати деталі для наявних запитів."

        return request_details, None

    # def process_document_request(self, request_id, approve=True):
    #     status = 'processed' if approve else 'rejected'
    #     updated_request = self.document_request_repo.update_request_status(request_id, status)
    #
    #     if updated_request:
    #         # Отримуємо студента за StudentID з запиту
    #         student = self.student_repo.get_student_by_id(updated_request.StudentID)
    #         if not student:
    #             return False, None, "Студент не знайдений"
    #
    #         # Отримуємо користувача за UserID студента
    #         user = self.user_repo.get_user_by_id(student.UserID)
    #         if not user:
    #             return False, None, "Користувач не знайдений"
    #
    #         status_text = "опрацьована" if approve else "відхилена"
    #         message = f"{'✅' if approve else '❌'} Ваша заявка №{updated_request.RequestID} на документ була {status_text}."
    #
    #         return True, user.ChatID, message
    #
    #     return False, None, "Заявка не знайдена"

    def process_document_request_with_scan(self, request_id, scan_link, approve=True):
        status = 'approved' if approve else 'rejected'
        student_id, request_id = self.document_request_repo.update_request_status(request_id, status)

        if student_id:
            student = self.student_repo.get_student_by_id(student_id)
            if not student:
                return False, None, "Студент не знайдений"

            # Отримуємо користувача за UserID студента
            user = self.user_repo.get_user_by_id(student.UserID)
            if not user:
                return False, None, "Користувач не знайдений"

            status_text = "опрацьована" if approve else "відхилена"
            message = f"{'✅' if approve else '❌'} Ваша заявка №{request_id} на документ була {status_text}."
            if scan_link:
                message += f"\nСкан документу доступний за посиланням: {scan_link}"

            return True, user.ChatID, message

        return False, None, "Заявка не знайдена"
# class DocumentService:
#     """Service for document request operations"""
#
#     def __init__(self, doc_repo, user_repo):
#         self.doc_repo = doc_repo
#         self.user_repo = user_repo
#
#     async def request_document(self, update, context):
#         """Handle document request command"""
#         user = update.message.from_user
#         telegram_tag = user.username
#
#         # Check if user is a student
#         student_data = self.doc_repo.get_student_by_telegram_tag(telegram_tag)
#         if not student_data:
#             await update.message.reply_text("❌ Ви не зареєстровані як студент.")
#             return
#
#         # Get document types
#         document_types = self.doc_repo.get_all_document_types()
#
#         if not document_types:
#             await update.message.reply_text("❌ Наразі немає доступних типів документів.")
#             return
#
#         # Create buttons for document selection
#         keyboard = []
#         for doc_type in document_types:
#             keyboard.append([InlineKeyboardButton(
#                 doc_type.TypeName,
#                 callback_data=f"doc_select_{doc_type.TypeID}"
#             )])
#
#         keyboard.append([InlineKeyboardButton("🚫 Скасувати", callback_data="cancel_doc")])
#         reply_markup = InlineKeyboardMarkup(keyboard)

        # await update.message.reply_text(
        #     "📝 Виберіть тип документу, який хочете замовити:",
        #     reply_markup=reply_markup
        # )

    # async def process_document_requests(self, update, context):
    #     """Show pending document requests for dean office staff"""
    #     user = update.message.from_user
    #     telegram_tag = user.username
    #
    #     # Check if user is dean office staff
    #     user_data = self.user_repo.get_by_telegram_tag(telegram_tag)
    #     if not user_data or user_data.Role != "dean_office":
    #         await update.message.reply_text("❌ У вас немає доступу до цієї функції.")
    #         return
    #
    #     # Get pending requests
    #     requests = self.doc_repo.get_pending_document_requests()
    #
    #     if not requests:
    #         await update.message.reply_text("🎉 Немає заявок, що очікують розгляду.")
    #         return
    #
    #     # Create message with requests
    #     message = "📋