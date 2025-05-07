from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import FAQ

class FAQRepository:
    """Репозиторій для роботи з частими запитаннями в базі даних."""

    def __init__(self, get_session):
        """
        Ініціалізує FAQRepository.

        Args:
            get_session: Функція, яка повертає сесію SQLAlchemy.
        """
        self.get_session = get_session

    def get_faqs(self) -> list[tuple[str, str]]:
        """Отримує список частих запитань і відповідей з бази даних."""
        try:
            with self.get_session() as session:
                faqs = session.query(FAQ.Question, FAQ.Answer).all()
                return faqs
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні списку FAQ: {e}")
            return []

    def get_faqs_with_id(self) -> list[tuple[int, str, str]]:
        """Отримує список частих запитань і відповідей з ID з бази даних."""
        try:
            with self.get_session() as session:
                faqs = session.query(FAQ.FAQID, FAQ.Question, FAQ.Answer).all()
                return faqs
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні списку FAQ з ID: {e}")
            return []

    def add_faq(self, question: str, answer: str) -> bool:
        """Додає нове питання та відповідь до бази даних."""
        try:
            with self.get_session() as session:
                faq = FAQ(Question=question, Answer=answer)
                session.add(faq)
                session.commit()
                return True
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при додаванні FAQ: {e}")
            return False

    def update_faq(self, faq_id: int, answer: str) -> bool:
        """Оновлює відповідь у FAQ за ID."""
        try:
            with self.get_session() as session:
                result = session.query(FAQ).filter_by(FAQID=faq_id).update({"Answer": answer})
                session.commit()
                return result > 0
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при оновленні FAQ: {e}")
            return False

    def delete_faq(self, faq_id: int) -> bool:
        """Видаляє питання та відповідь з бази даних за ID."""
        try:
            with self.get_session() as session:
                result = session.query(FAQ).filter_by(FAQID=faq_id).delete()
                session.commit()
                return result > 0
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при видаленні FAQ: {e}")
            return False

    def get_faq_by_id(self, faq_id: int) -> tuple[str, str] or None:
        """Отримує питання та відповідь за ID."""
        try:
            with self.get_session() as session:
                result = session.query(FAQ.Question, FAQ.Answer).filter(FAQ.FAQID == faq_id).first()
                return result
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні FAQ за ID: {e}")
            return None