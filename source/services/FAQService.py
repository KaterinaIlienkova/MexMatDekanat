from source.repositories import FAQRepository

class FAQService:
    """Сервіс для роботи з FAQ."""
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    def get_faqs(self, with_id: bool = False):
        """
        Отримує всі FAQ.

        Args:
            with_id: Якщо True, поверне також ID записів.

        Returns:
            Список FAQ у форматі залежно від параметра with_id.
        """
        with self.uow_factory() as uow:
            return uow.faq_repository.get_faqs(with_id=with_id)

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

