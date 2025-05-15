from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from datetime import datetime
import logging

from source.models import CourseEnrollment, StudentGroup, User, Student, Course, Teacher, Specialty, Department

# Налаштування логера
logger = logging.getLogger(__name__)


class AnnouncementRepository:
    def __init__(self, get_session):
        self.get_session = get_session

    def get_all_teachers(self) -> List[Dict[str, Any]]:
        """Отримати всіх викладачів для розсилки оголошень."""
        try:
            with self.get_session() as session:
                teachers = session.query(
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

    def get_teachers_by_department(self, department_id: int) -> List[Dict[str, Any]]:
        """Отримати викладачів конкретної кафедри для розсилки оголошень."""
        try:
            with self.get_session() as session:
                teachers = session.query(
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

    def get_teachers_by_ids(self, teacher_ids: List[int]) -> List[Dict[str, Any]]:
        """Отримати викладачів за списком ID для розсилки оголошень."""
        try:
            with self.get_session() as session:
                teachers = session.query(
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

    def get_all_departments(self) -> List[Dict[str, Any]]:
        """Отримати список всіх кафедр для вибору розсилки."""
        try:
            with self.get_session() as session:
                departments = session.query(
                    Department.DepartmentID,
                    Department.Name
                ).all()

                return [
                    {
                        'department_id': d.DepartmentID,
                        'name': d.Name
                    }
                    for d in departments
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting all departments: {e}")
            return []

    def get_department_by_name(self, department_name: str) -> Optional[Department]:
        """Отримати кафедру за назвою."""
        try:
            with self.get_session() as session:
                return session.query(Department).filter_by(Name=department_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting department by name: {e}")
            return None

    def get_all_student_groups(self) -> List[Dict[str, Any]]:
        """Отримати список всіх груп студентів для вибору розсилки."""
        try:
            with self.get_session() as session:
                groups = session.query(
                    StudentGroup.GroupID,
                    StudentGroup.GroupName,
                    Specialty.Name.label('SpecialtyName')
                ).join(
                    Specialty, StudentGroup.SpecialtyID == Specialty.SpecialtyID, isouter=True
                ).all()

                return [
                    {
                        'group_id': g.GroupID,
                        'group_name': g.GroupName,
                        'specialty': g.SpecialtyName
                    }
                    for g in groups
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting all student groups: {e}")
            return []

    def get_student_group_by_name(self, group_name: str) -> Optional[StudentGroup]:
        """Отримує групу за назвою."""
        try:
            with self.get_session() as session:
                return session.query(StudentGroup).filter_by(GroupName=group_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting student group by name: {e}")
            return None

    def get_all_specialties(self) -> List[Dict[str, Any]]:
        """Отримати список всіх спеціальностей для вибору розсилки."""
        try:
            with self.get_session() as session:
                specialties = session.query(
                    Specialty.SpecialtyID,
                    Specialty.Name
                ).all()

                return [
                    {
                        'specialty_id': s.SpecialtyID,
                        'name': s.Name
                    }
                    for s in specialties
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting all specialties: {e}")
            return []

    def get_specialty_by_name(self, specialty_name: str) -> Optional[Specialty]:
        """Отримати спеціальність за назвою."""
        try:
            with self.get_session() as session:
                return session.query(Specialty).filter_by(Name=specialty_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting specialty by name: {e}")
            return None

    def get_students_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """Отримати студентів конкретної групи для розсилки оголошень."""
        try:
            with self.get_session() as session:
                students = session.query(
                    User.UserID,
                    User.UserName,
                    User.TelegramTag,
                    User.ChatID,
                    Student.StudentID,
                    StudentGroup.GroupName
                ).join(
                    Student, User.UserID == Student.UserID
                ).join(
                    StudentGroup, Student.GroupID == StudentGroup.GroupID
                ).filter(
                    User.Role == 'student',
                    User.IsConfirmed == True,
                    User.ChatID.isnot(None),
                    Student.GroupID == group_id
                ).all()

                return [
                    {
                        'user_id': s.UserID,
                        'username': s.UserName,
                        'telegram_tag': s.TelegramTag,
                        'chat_id': s.ChatID,
                        'student_id': s.StudentID,
                        'group_name': s.GroupName
                    }
                    for s in students
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting students by group: {e}")
            return []

    def get_students_by_specialty(self, specialty_id: int) -> List[Dict[str, Any]]:
        """Отримати студентів конкретної спеціальності для розсилки оголошень."""
        try:
            with self.get_session() as session:
                students = session.query(
                    User.UserID,
                    User.UserName,
                    User.TelegramTag,
                    User.ChatID,
                    Student.StudentID,
                    StudentGroup.GroupName
                ).join(
                    Student, User.UserID == Student.UserID
                ).join(
                    StudentGroup, Student.GroupID == StudentGroup.GroupID
                ).filter(
                    User.Role == 'student',
                    User.IsConfirmed == True,
                    User.ChatID.isnot(None),
                    StudentGroup.SpecialtyID == specialty_id
                ).all()

                return [
                    {
                        'user_id': s.UserID,
                        'username': s.UserName,
                        'telegram_tag': s.TelegramTag,
                        'chat_id': s.ChatID,
                        'student_id': s.StudentID,
                        'group_name': s.GroupName
                    }
                    for s in students
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting students by specialty: {e}")
            return []

    def get_students_by_course_year(self, course_year: int) -> List[Dict[str, Any]]:
        """
        Отримати студентів конкретного курсу навчання для розсилки оголошень.
        Курс визначається як поточний рік мінус рік вступу.
        """
        try:
            current_year = datetime.now().year
            current_month = datetime.now().month

            # Якщо поточний місяць менший за вересень (9), то курс рахується за попереднім роком
            if current_month < 9:
                academic_year_start = current_year - 1
            else:
                academic_year_start = current_year

            # Визначаємо рік вступу для потрібного курсу
            admission_year = academic_year_start - course_year + 1

            with self.get_session() as session:
                students = session.query(
                    User.UserID,
                    User.UserName,
                    User.TelegramTag,
                    User.ChatID,
                    Student.StudentID,
                    Student.AdmissionYear,
                    StudentGroup.GroupName
                ).join(
                    Student, User.UserID == Student.UserID
                ).join(
                    StudentGroup, Student.GroupID == StudentGroup.GroupID
                ).filter(
                    User.Role == 'student',
                    User.IsConfirmed == True,
                    User.ChatID.isnot(None),
                    Student.AdmissionYear == admission_year
                ).all()

                return [
                    {
                        'user_id': s.UserID,
                        'username': s.UserName,
                        'telegram_tag': s.TelegramTag,
                        'chat_id': s.ChatID,
                        'student_id': s.StudentID,
                        'group_name': s.GroupName,
                        'admission_year': s.AdmissionYear
                    }
                    for s in students
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting students by course year: {e}")
            return []
        except Exception as e:
            logger.error(f"Error calculating course year: {e}")
            return []

    def get_students_by_ids(self, student_ids: List[int]) -> List[Dict[str, Any]]:
        """Отримати студентів за списком ID для розсилки оголошень."""
        try:
            with self.get_session() as session:
                students = session.query(
                    User.UserID,
                    User.UserName,
                    User.TelegramTag,
                    User.ChatID,
                    Student.StudentID,
                    StudentGroup.GroupName
                ).join(
                    Student, User.UserID == Student.UserID
                ).join(
                    StudentGroup, Student.GroupID == StudentGroup.GroupID
                ).filter(
                    User.Role == 'student',
                    User.IsConfirmed == True,
                    User.ChatID.isnot(None),
                    Student.StudentID.in_(student_ids)
                ).all()

                return [
                    {
                        'user_id': s.UserID,
                        'username': s.UserName,
                        'telegram_tag': s.TelegramTag,
                        'chat_id': s.ChatID,
                        'student_id': s.StudentID,
                        'group_name': s.GroupName
                    }
                    for s in students
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting students by IDs: {e}")
            return []

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Отримати всіх студентів для розсилки оголошень."""
        try:
            with self.get_session() as session:
                students = session.query(
                    User.UserID,
                    User.UserName,
                    User.TelegramTag,
                    User.ChatID,
                    Student.StudentID,
                    Student.AdmissionYear,
                    StudentGroup.GroupName
                ).join(
                    Student, User.UserID == Student.UserID
                ).join(
                    StudentGroup, Student.GroupID == StudentGroup.GroupID
                ).filter(
                    User.Role == 'student',
                    User.IsConfirmed == True,
                    User.ChatID.isnot(None)
                ).all()

                return [
                    {
                        'user_id': s.UserID,
                        'username': s.UserName,
                        'telegram_tag': s.TelegramTag,
                        'chat_id': s.ChatID,
                        'student_id': s.StudentID,
                        'group_name': s.GroupName,
                        'admission_year': s.AdmissionYear
                    }
                    for s in students
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting all students: {e}")
            return []

    def get_all_courses(self) -> List[Dict[str, Any]]:
        """Отримати список всіх курсів для вибору розсилки."""
        try:
            with self.get_session() as session:
                courses = session.query(
                    Course.CourseID,
                    Course.Name,
                    User.UserName.label('TeacherName')
                ).join(
                    Teacher, Course.TeacherID == Teacher.TeacherID
                ).join(
                    User, Teacher.UserID == User.UserID
                ).filter(
                    Course.IsActive == True
                ).all()

                return [
                    {
                        'course_id': c.CourseID,
                        'name': c.Name,
                        'teacher': c.TeacherName
                    }
                    for c in courses
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting all courses: {e}")
            return []

    def get_course_by_name(self, course_name: str) -> Optional[Course]:
        """Отримати курс за назвою."""
        try:
            with self.get_session() as session:
                return session.query(Course).filter_by(Name=course_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting course by name: {e}")
            return None

    def get_students_by_course_enrollment(self, course_id: int) -> List[Dict[str, Any]]:
        """Отримати студентів, записаних на конкретний курс, для розсилки оголошень."""
        try:
            with self.get_session() as session:
                students = session.query(
                    User.UserID,
                    User.UserName,
                    User.TelegramTag,
                    User.ChatID,
                    Student.StudentID,
                    StudentGroup.GroupName,
                    Course.Name.label('CourseName')
                ).join(
                    Student, User.UserID == Student.UserID
                ).join(
                    CourseEnrollment, Student.StudentID == CourseEnrollment.StudentID
                ).join(
                    Course, CourseEnrollment.CourseID == Course.CourseID
                ).join(
                    StudentGroup, Student.GroupID == StudentGroup.GroupID
                ).filter(
                    User.Role == 'student',
                    User.IsConfirmed == True,
                    User.ChatID.isnot(None),
                    CourseEnrollment.CourseID == course_id
                ).all()

                return [
                    {
                        'user_id': s.UserID,
                        'username': s.UserName,
                        'telegram_tag': s.TelegramTag,
                        'chat_id': s.ChatID,
                        'student_id': s.StudentID,
                        'group_name': s.GroupName,
                        'course_name': s.CourseName
                    }
                    for s in students
                ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting students by course enrollment: {e}")
            return []

    def get_teacher_courses(self, telegram_tag: str, active_only: bool = True) -> list[dict]:

        try:
            with self.get_session() as session:
                # Знаходимо викладача за Telegram тегом
                teacher = session.query(Teacher).join(User, User.UserID == Teacher.UserID) \
                    .filter(User.TelegramTag == telegram_tag).first()

                if not teacher:
                    return []

                    # Запит для отримання курсів викладача
                courses_query = session.query(
                    Course.CourseID,
                    Course.Name.label("course_name"),
                    Course.StudyPlatform,
                    Course.MeetingLink,
                    Course.IsActive
                ) \
                    .filter(Course.TeacherID == teacher.TeacherID)

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
                        "is_active": course.IsActive
                    }
                    courses_list.append(course_dict)

                return courses_list

        except Exception as e:
            logger.exception(f"Помилка при отриманні курсів викладача: {str(e)}")
            return []



    def get_course_students(self, course_id: int) -> list[dict]:
        """
        Отримує список студентів на конкретному курсі за його ID.

        Args:
            course_id: ID курсу

        Returns:
            Список студентів з їх деталями
        """
        try:
            with self.get_session() as session:
                # Запит для отримання студентів на курсі
                students_query = session.query(
                    User.UserName.label("student_name"),
                    User.PhoneNumber.label("student_phone"),
                    User.TelegramTag.label("telegram_tag")
                ).join(
                    Student, Student.UserID == User.UserID
                ).join(
                    CourseEnrollment, CourseEnrollment.StudentID == Student.StudentID
                ).filter(
                    CourseEnrollment.CourseID == course_id
                )

                students = students_query.all()

                students_list = []
                for student in students:
                    student_dict = {
                        "student_name": student.student_name,
                        "student_phone": student.student_phone or "Не вказано",
                        "telegram_tag": student.telegram_tag
                    }
                    students_list.append(student_dict)

                return students_list

        except Exception as e:
            logger.exception(f"Помилка при отриманні студентів на курсі: {str(e)}")
            return []