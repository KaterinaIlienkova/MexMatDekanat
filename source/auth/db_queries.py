from sqlalchemy.exc import SQLAlchemyError
import logging
logger = logging.getLogger(__name__)
from source.models import Student, User, StudentGroup
from sqlalchemy.orm import Session

def update_user_field(session: Session, telegram_tag: str, field: str, new_value: str) -> bool:
    """
    Оновлює вказане поле користувача у базі даних.

    Args:
        session: Сесія бази даних
        telegram_tag: TelegramTag користувача
        field: Поле, яке потрібно оновити
        new_value: Нове значення поля

    Returns:
        bool: True, якщо оновлення успішне, False в іншому випадку
    """
    try:
        user = session.query(User).filter_by(TelegramTag=telegram_tag).first()

        if not user:
            return False

        # Визначаємо, яке поле оновлювати
        if field == "edit_name":
            user.UserName = new_value
        elif field == "edit_phone":
            user.PhoneNumber = new_value
        elif field == "edit_group":
            # Перевіряємо, чи існує група
            group = session.query(StudentGroup).filter_by(GroupName=new_value).first()
            if not group:
                return False

            # Оновлюємо групу в таблиці студентів
            student = session.query(Student).filter_by(UserID=user.UserID).first()
            if student:
                student.GroupID = group.GroupID
            else:
                return False
        elif field == "edit_year":
            # Перевіряємо, чи є значення цілим числом
            try:
                year = int(new_value)
                student = session.query(Student).filter_by(UserID=user.UserID).first()
                if student:
                    student.AdmissionYear = year
                else:
                    return False
            except ValueError:
                return False

        session.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Помилка при оновленні поля користувача: {e}")
        session.rollback()
        return False