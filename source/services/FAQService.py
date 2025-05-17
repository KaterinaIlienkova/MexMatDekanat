from source.repositories import FAQRepository

class FAQService:
    """Сервіс для роботи з FAQ."""
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    def get_all_faqs(self):
        with self.uow_factory() as uow:
            """Отримує всі FAQ."""
            return uow.faq_repository.get_faqs()

    def get_all_faqs_with_id(self):
        """Отримує всі FAQ з їх ID."""
        with self.uow_factory() as uow:
            return uow.faq_repository.get_faqs_with_id()

    def add_new_faq(self, question: str, answer: str) -> bool:
        with self.uow_factory() as uow:
            """Додає новий FAQ."""
            # Можна додати додаткову валідацію питання та відповіді
            if not question or not answer:
                return False

            return uow.faq_repository.add_faq(question, answer)

    def update_faq_answer(self, faq_id: int, answer: str) -> bool:
        """Оновлює відповідь на питання."""
        with self.uow_factory() as uow:
            if not answer:
                return False

            return uow.faq_repository.update_faq(faq_id, answer)

    def remove_faq(self, faq_id: int) -> bool:
        with self.uow_factory() as uow:
            """Видаляє FAQ."""
            return uow.faq_repository.delete_faq(faq_id)

    def get_faq_details(self, faq_id: int) -> dict or None:
        with self.uow_factory() as uow:
            """Отримує деталі FAQ за ID."""
            result = uow.faq_repository.get_faq_by_id(faq_id)
            if result:
                question, answer = result
                return {
                    "question": question,
                    "answer": answer
                }
            return None
