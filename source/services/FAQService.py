from source.repositories import FAQRepository

class FAQService:
    """Сервіс для роботи з FAQ."""

    def __init__(self, faq_repository: FAQRepository):
        """
        Ініціалізує FAQService.

        Args:
            faq_repository: Репозиторій для роботи з FAQ.
        """
        self.faq_repository = faq_repository

    def get_all_faqs(self):
        """Отримує всі FAQ."""
        return self.faq_repository.get_faqs()

    def get_all_faqs_with_id(self):
        """Отримує всі FAQ з їх ID."""
        return self.faq_repository.get_faqs_with_id()

    def add_new_faq(self, question: str, answer: str) -> bool:
        """Додає новий FAQ."""
        # Можна додати додаткову валідацію питання та відповіді
        if not question or not answer:
            return False

        return self.faq_repository.add_faq(question, answer)

    def update_faq_answer(self, faq_id: int, answer: str) -> bool:
        """Оновлює відповідь на питання."""
        if not answer:
            return False

        return self.faq_repository.update_faq(faq_id, answer)

    def remove_faq(self, faq_id: int) -> bool:
        """Видаляє FAQ."""
        return self.faq_repository.delete_faq(faq_id)

    def get_faq_details(self, faq_id: int) -> dict or None:
        """Отримує деталі FAQ за ID."""
        result = self.faq_repository.get_faq_by_id(faq_id)
        if result:
            question, answer = result
            return {
                "question": question,
                "answer": answer
            }
        return None
