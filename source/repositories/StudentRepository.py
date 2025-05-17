from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List

class StudentRepository(BaseRepository):


    def get_student_by_user_id(self, user_id: int) -> Optional[Student]:
        """Отримує запис студента за ID користувача."""
        try:
            return self.session.query(Student).filter_by(UserID=user_id).first()
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні студента: {e}")
            return None



    def add_student(self, user_id: int, group_id: int, admission_year: int) -> Optional[Student]:
        """Додає запис студента для існуючого користувача."""
        try:
            # Перевіряємо чи існує користувач
            user = self.session.query(User).filter_by(UserID=user_id).first()
            if not user:
                logger.error(f"User with ID {user_id} not found")
                return None

            # Перевіряємо чи вже є запис студента
            existing_student = self.session.query(Student).filter_by(UserID=user_id).first()
            if existing_student:
                logger.warning(f"Student record already exists for user ID {user_id}")
                return existing_student

            # Створюємо запис студента
            new_student = Student(
                UserID=user_id,
                GroupID=group_id,
                AdmissionYear=admission_year
            )

            self.session.add(new_student)
            self.session.commit()
            return new_student
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding student: {e}")
            return None

    def get_student_info(self, user_id):
            """Отримує інформацію про студента."""
            student = self.session.query(Student).filter_by(UserID=user_id).first()
            if student:
                group = self.session.query(StudentGroup).filter_by(GroupID=student.GroupID).first()
                group_name = group.GroupName if group else "Невідома"

                # Отримуємо спеціальність через зв'язок групи
                specialty_name = "Невідома"
                if group and group.specialty:
                    specialty_name = group.specialty.Name

                return {
                    'group_name': group_name,
                    'admission_year': student.AdmissionYear,
                    'specialty': specialty_name
                }
            return None

    def get_unconfirmed_students_with_details(self):
        """Отримує список непідтверджених студентів з детальною інформацією."""
        result = self.session.query(
            User,
            Student,
            StudentGroup
        ).join(
            Student, User.UserID == Student.UserID
        ).join(
            StudentGroup, Student.GroupID == StudentGroup.GroupID
        ).filter(
            User.IsConfirmed == False,
            User.Role == 'student'
        ).all()

        return result

    def update_student_info(self, user_id, update_data):
            """Оновлює інформацію про студента."""
            try:
                # Оновлюємо основну інформацію користувача
                user = self.session.query(User).filter(User.UserID == user_id).first()
                if not user or user.Role != 'student':
                    return False

                if 'username' in update_data:
                    user.UserName = update_data['username']
                if 'phone_number' in update_data:
                    user.PhoneNumber = update_data['phone_number']
                if 'telegram_tag' in update_data:
                    # Перевірка унікальності telegram_tag
                    existing_user = self.session.query(User).filter(
                        User.TelegramTag == update_data['telegram_tag'],
                        User.UserID != user_id
                    ).first()

                    if existing_user:
                        return False
                    user.TelegramTag = update_data['telegram_tag']

                # Оновлюємо інформацію студента
                student = self.session.query(Student).filter(Student.UserID == user_id).first()
                if student:
                    if 'group_id' in update_data:
                        student.GroupID = update_data['group_id']
                    if 'admission_year' in update_data:
                        student.AdmissionYear = update_data['admission_year']

                self.session.commit()
                return True
            except Exception as e:
                self.session.rollback()
                logger.error(f"Error updating student info: {e}")
                return False


    def get_admission_years(self):
        """Отримує список унікальних років вступу студентів."""
        years = self.session.query(Student.AdmissionYear).distinct().all()
        return [year[0] for year in years]



    def get_students_by_group_and_course(self, group_name, admission_year):
            """Отримує список студентів із конкретної групи та року вступу."""
            students = self.session.query(User.UserID, User.UserName, User.PhoneNumber) \
                .join(Student, User.UserID == Student.UserID) \
                .join(StudentGroup, Student.GroupID == StudentGroup.GroupID) \
                .filter(StudentGroup.GroupName == group_name, Student.AdmissionYear == admission_year) \
                .all()

            result = []
            for student in students:
                result.append({
                    'user_id': student[0],
                    'name': student[1],
                    'phone': student[2]
                })
            return result


