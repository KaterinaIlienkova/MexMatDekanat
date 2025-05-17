from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class DocumentService:
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory


    def can_request_document(self, chat_id):
        with self.uow_factory() as uow:
            user = uow.auth_repository.get_user_by_chat_id(chat_id)
            if not user or user.Role != 'student':
                return False, "Замовлення документів доступне тільки для студентів."

            student = uow.auth_repository.get_student_by_user_id(user.UserID)
            if not student:
                return False, "Не вдалося знайти дані студента. Зверніться до деканату."

            return True, student

    def get_available_document_types(self):
        with self.uow_factory() as uow:
            document_types = uow.document_type_repository.get_all_document_types()
            if not document_types:
                return None, "На даний момент немає доступних типів документів для замовлення."
            return document_types, None

    def create_document_request(self, document_type_id, student_id):
        with self.uow_factory() as uow:
            try:
                document_type = uow.document_type_repository.get_document_type_by_id(document_type_id)
                if not document_type:
                    return None, "Помилка: обраний тип документа не знайдено."

                new_request = uow.document_request_repository.create_request(student_id, document_type_id)
                return new_request, document_type
            except Exception as e:
                print(f"❌ Помилка при створенні заявки: {e}")
                return None, "❌ Сталася помилка при створенні заявки. Спробуйте пізніше або зверніться до деканату."


#Репозоторії яких не існує

    def get_pending_document_requests(self):
        with self.uow_factory() as uow:
            requests = uow.document_request_repository.get_pending_requests()
            if not requests:
                return None, "Немає заявок на документи для опрацювання."

            request_details = []
            for req in requests:
                # Використовуємо StudentID з запиту для отримання об'єкта студента
                student = uow.student_repo.get_student_by_id(req.StudentID)
                if not student:
                    continue  # Пропускаємо цей запит, якщо студент не знайдений

                # Отримуємо користувача за UserID студента
                user = uow.user_repo.get_user_by_id(student.UserID)
                if not user:
                    continue  # Пропускаємо, якщо користувач не знайдений

                doc_type = uow.document_type_repository.get_document_type_by_id(req.TypeID)
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


    def process_document_request_with_scan(self, request_id, scan_link, approve=True):
        with self.uow_factory() as uow:
            status = 'approved' if approve else 'rejected'
            student_id, request_id = uow.document_request_repository.update_request_status(request_id, status)

            if student_id:
                student = uow.student_repo.get_student_by_id(student_id)
                if not student:
                    return False, None, "Студент не знайдений"

                # Отримуємо користувача за UserID студента
                user = uow.user_repo.get_user_by_id(student.UserID)
                if not user:
                    return False, None, "Користувач не знайдений"

                status_text = "опрацьована" if approve else "відхилена"
                message = f"{'✅' if approve else '❌'} Ваша заявка №{request_id} на документ була {status_text}."
                if scan_link:
                    message += f"\nСкан документу доступний за посиланням: {scan_link}"

                return True, user.ChatID, message

            return False, None, "Заявка не знайдена"
