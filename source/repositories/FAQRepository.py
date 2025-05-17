from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import FAQ
from source.repositories.BaseRepository import BaseRepository


class FAQRepository(BaseRepository):
    """Репозиторій для роботи з частими запитаннями в базі даних."""

    def get_faqs(self, with_id: bool = False) -> list[tuple]:
        """
        Отримує список частих запитань і відповідей з бази даних.

        Args:
            with_id: Якщо True, поверне також ID записів.

        Returns:
            Список кортежів (питання, відповідь) або (id, питання, відповідь).
        """
        try:
            if with_id:
                faqs = self.session.query(FAQ.FAQID, FAQ.Question, FAQ.Answer).all()
            else:
                faqs = self.session.query(FAQ.Question, FAQ.Answer).all()
            return faqs
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні списку FAQ: {e}")
            return []

    def add_faq(self, question: str, answer: str) -> bool:
        """Додає нове питання та відповідь до бази даних."""
        try:
                faq = FAQ(Question=question, Answer=answer)
                self.session.add(faq)
                self.session.commit()
                return True
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при додаванні FAQ: {e}")
            return False

    def update_faq(self, faq_id: int, answer: str) -> bool:
        """Оновлює відповідь у FAQ за ID."""
        try:
                result = self.session.query(FAQ).filter_by(FAQID=faq_id).update({"Answer": answer})
                self.session.commit()
                return result > 0
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при оновленні FAQ: {e}")
            return False

    def delete_faq(self, faq_id: int) -> bool:
        """Видаляє питання та відповідь з бази даних за ID."""
        try:
                result = self.session.query(FAQ).filter_by(FAQID=faq_id).delete()
                self.session.commit()
                return result > 0
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при видаленні FAQ: {e}")
            return False

    def get_faq_by_id(self, faq_id: int) -> tuple[str, str] or None:
        """Отримує питання та відповідь за ID."""
        try:
                result = self.session.query(FAQ.Question, FAQ.Answer).filter(FAQ.FAQID == faq_id).first()
                return result
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні FAQ за ID: {e}")
            return None