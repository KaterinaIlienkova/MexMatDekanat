from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List, Dict, Any


class TeacherRepository(BaseRepository):

    def get_all_teachers(self) -> List[Dict[str, Any]]:
        """Отримати всіх викладачів для розсилки оголошень."""
        try:
            teachers = self.session.query(
                User.UserID,
                User.UserName,
                User.TelegramTag,
                User.ChatID,
                Teacher.TeacherID,
                Department.Name.label('DepartmentName')
            ).join(
                Teacher, User.UserID == Teacher.UserID
            ).join(
                Department, Teacher.DepartmentID == Department.DepartmentID, isouter=True
            ).filter(
                User.Role == 'teacher',
                User.IsConfirmed == True,
                User.ChatID.isnot(None)
            ).all()

            return [
                {
                    'user_id': t.UserID,
                    'username': t.UserName,
                    'telegram_tag': t.TelegramTag,
                    'chat_id': t.ChatID,
                    'teacher_id': t.TeacherID,
                    'department': t.DepartmentName
                }
                for t in teachers
            ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting all teachers: {e}")
            return []

    def add_teacher(self, user_id: int, email: str, department_id: int) -> Optional[Teacher]:
        """Додає запис викладача для існуючого користувача."""
        try:
            # Перевіряємо чи існує користувач
            user = self.session.query(User).filter_by(UserID=user_id).first()
            if not user:
                logger.error(f"User with ID {user_id} not found")
                return None

            # Перевіряємо чи вже є запис викладача
            existing_teacher = self.session.query(Teacher).filter_by(UserID=user_id).first()
            if existing_teacher:
                logger.warning(f"Teacher record already exists for user ID {user_id}")
                return existing_teacher

            # Створюємо запис викладача
            new_teacher = Teacher(
                UserID=user_id,
                Email=email,
                DepartmentID=department_id
            )

            self.session.add(new_teacher)
            self.session.commit()
            return new_teacher
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding teacher: {e}")
            return None

    def get_teachers_by_department(self, department_name):
        """Отримує список викладачів із конкретної кафедри."""
        teachers = self.session.query(User.UserID, User.UserName, User.PhoneNumber, Teacher.Email) \
            .join(Teacher, User.UserID == Teacher.UserID) \
            .join(Department, Teacher.DepartmentID == Department.DepartmentID) \
            .filter(Department.Name == department_name) \
            .all()

        result = []
        for teacher in teachers:
            result.append({
                'user_id': teacher[0],
                'name': teacher[1],
                'phone': teacher[2],
                'email': teacher[3]
            })
        return result

    def get_teachers_by_departmentID(self, department_id: int) -> List[Dict[str, Any]]:
        """Отримати викладачів конкретної кафедри для розсилки оголошень."""
        try:
            teachers = self.session.query(
                User.UserID,
                User.UserName,
                User.TelegramTag,
                User.ChatID,
                Teacher.TeacherID
            ).join(
                Teacher, User.UserID == Teacher.UserID
            ).filter(
                User.Role == 'teacher',
                User.IsConfirmed == True,
                User.ChatID.isnot(None),
                Teacher.DepartmentID == department_id
            ).all()

            return [
                {
                    'user_id': t.UserID,
                    'username': t.UserName,
                    'telegram_tag': t.TelegramTag,
                    'chat_id': t.ChatID,
                    'teacher_id': t.TeacherID
                }
                for t in teachers
            ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting teachers by department: {e}")
            return []

    def get_teacher_id_by_username(self, username: str) -> int:
        """
        Отримує ID викладача за телеграм-тегом.

        Args:
            username: Телеграм-тег викладача

        Returns:
            ID викладача або None, якщо викладача не знайдено
        """
        try:
            teacher = self.session.query(Teacher).join(User).filter(User.TelegramTag == username).first()
            return teacher.TeacherID if teacher else None
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні ID викладача: {e}")
            return None

    def get_teachers_by_ids(self, teacher_ids: List[int]) -> List[Dict[str, Any]]:
        """Отримати викладачів за списком ID для розсилки оголошень."""
        try:
            teachers = self.session.query(
                User.UserID,
                User.UserName,
                User.TelegramTag,
                User.ChatID,
                Teacher.TeacherID
            ).join(
                Teacher, User.UserID == Teacher.UserID
            ).filter(
                User.Role == 'teacher',
                User.IsConfirmed == True,
                User.ChatID.isnot(None),
                Teacher.TeacherID.in_(teacher_ids)
            ).all()

            return [
                {
                    'user_id': t.UserID,
                    'username': t.UserName,
                    'telegram_tag': t.TelegramTag,
                    'chat_id': t.ChatID,
                    'teacher_id': t.TeacherID
                }
                for t in teachers
            ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting teachers by IDs: {e}")
            return []

