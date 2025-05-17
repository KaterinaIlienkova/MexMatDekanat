from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List

class TeacherRepository(BaseRepository):

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

