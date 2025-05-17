from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, \
    CourseEnrollment, Course
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

    def get_student_id_by_username(self, username: str) -> int:
        """
        Отримує ID викладача за телеграм-тегом.

        Args:
            username: Телеграм-тег викладача

        Returns:
            ID викладача або None, якщо викладача не знайдено
        """
        try:
            student = self.session.query(Student).join(User).filter(User.TelegramTag == username).first()
            return student.StudentID if student else None
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні ID викладача: {e}")
            return None

    def get_student_id_by_telegram(self, telegram_tag: str) -> int:
        """
        Отримує ID студента за його Telegram тегом.

        Args:
            telegram_tag: Telegram тег студента

        Returns:
            ID студента або None, якщо студента не знайдено
        """
        try:
            student = self.session.query(Student).join(
                User, Student.UserID == User.UserID
            ).filter(
                User.TelegramTag == telegram_tag
            ).first()

            return student.StudentID if student else None
        except Exception as e:
            logger.exception(f"Помилка при отриманні ID студента: {str(e)}")
            return None


    def get_all_students_by_group(self, group_id: int) -> list[dict]:
        """
        Отримує список всіх студентів з вказаної групи незалежно від їх зарахування на курси.

        Args:
            group_id: ID групи

        Returns:
            Список студентів з їх деталями
        """
        try:
            # Запит для отримання всіх студентів з вказаної групи
            students = self.session.query(
                Student.StudentID,
                User.UserName,
                User.TelegramTag,
                User.PhoneNumber
            ).join(
                User, Student.UserID == User.UserID
            ).filter(
                Student.GroupID == group_id
            ).all()

            students_list = []
            for student in students:
                student_dict = {
                    "student_id": student.StudentID,
                    "student_name": student.UserName,
                    "telegram_tag": student.TelegramTag,
                    "phone_number": student.PhoneNumber or "Не вказано"
                }
                students_list.append(student_dict)

            return students_list
        except Exception as e:
            logger.exception(f"Помилка при отриманні студентів групи: {str(e)}")
            return []

    def get_student_courses(self, telegram_tag: str, active_only: bool = True) -> list[dict]:
        """
        Отримує список курсів для студента за його Telegram тегом.

        Args:
            telegram_tag: Телеграм тег користувача
            active_only: Якщо True, повертає тільки активні курси (поточний семестр)

        Returns:
            Список курсів з інформацією про викладача та деталями курсу
        """
        try:
            # Знаходимо студента за telegram_tag
            student = self.session.query(Student).join(User, User.UserID == Student.UserID) \
                .filter(User.TelegramTag == telegram_tag).first()

            if not student:
                return []

            # Запит для отримання курсів через CourseEnrollment
            courses_query = self.session.query(
                Course.CourseID,
                Course.Name.label("course_name"),
                Course.StudyPlatform,
                Course.MeetingLink,
                Course.IsActive,
                User.UserName.label("teacher_name"),
                Teacher.Email.label("teacher_email"),
                User.PhoneNumber.label("teacher_phone")
            ) \
                .join(CourseEnrollment, CourseEnrollment.CourseID == Course.CourseID) \
                .filter(CourseEnrollment.StudentID == student.StudentID) \
                .join(Teacher, Teacher.TeacherID == Course.TeacherID) \
                .join(User, User.UserID == Teacher.UserID)

            # Фільтрація тільки активних курсів
            if active_only:
                courses_query = courses_query.filter(Course.IsActive == True)

            courses = courses_query.all()

            # Формування результату
            courses_list = []
            for course in courses:
                course_dict = {
                    "course_id": course.CourseID,
                    "course_name": course.course_name,
                    "study_platform": course.StudyPlatform or "Не вказано",
                    "meeting_link": course.MeetingLink or "Не вказано",
                    "is_active": course.IsActive,
                    "teacher": {
                        "name": course.teacher_name,
                        "email": course.teacher_email,
                        "phone": course.teacher_phone or "Не вказано"
                    }
                }
                courses_list.append(course_dict)

            return courses_list

        except Exception as e:
            logger.exception(f"Помилка при отриманні курсів: {str(e)}")
            return []