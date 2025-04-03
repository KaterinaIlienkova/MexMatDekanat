import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from source.models import FAQ

logger = logging.getLogger(__name__)


def get_faqs(session: Session) -> list[tuple[str, str]]:
    """Отримує список частих запитань і відповідей з бази даних."""
    try:
        faqs = session.query(FAQ.Question, FAQ.Answer).all()
        return faqs
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при отриманні списку FAQ: {e}")
        return []

def get_faqs_with_id(session: Session) -> list[tuple[int, str, str]]:
    """Отримує список частих запитань і відповідей з ID з бази даних."""
    try:
        faqs = session.query(FAQ.FAQID, FAQ.Question, FAQ.Answer).all()
        return faqs
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при отриманні списку FAQ з ID: {e}")
        return []

def add_faq(session: Session, question: str, answer: str) -> bool:
    """Додає нове питання та відповідь до бази даних."""
    try:
        faq = FAQ(Question=question, Answer=answer)
        session.add(faq)
        session.commit()
        return True
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при додаванні FAQ: {e}")
        session.rollback()
        return False

def update_faq(session: Session, faq_id: int, answer: str) -> bool:
    """Оновлює відповідь у FAQ за ID."""
    try:
        result = session.query(FAQ).filter_by(FAQID=faq_id).update({"Answer": answer})
        session.commit()
        return result > 0
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при оновленні FAQ: {e}")
        session.rollback()
        return False

def delete_faq(session: Session, faq_id: int) -> bool:
    """Видаляє питання та відповідь з бази даних за ID."""
    try:
        result = session.query(FAQ).filter_by(FAQID=faq_id).delete()
        session.commit()
        return result > 0
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при видаленні FAQ: {e}")
        session.rollback()
        return False
