from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from datetime import datetime
import logging

from source.models import CourseEnrollment, StudentGroup, User, Student, Course, Teacher, Specialty, Department
from source.repositories.BaseRepository import BaseRepository

# Налаштування логера
logger = logging.getLogger(__name__)


class AnnouncementRepository(BaseRepository):


    def get_all_departments(self) -> List[Dict[str, Any]]:
        """Отримати список всіх кафедр для вибору розсилки."""
        try:
                departments = self.session.query(
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
                return self.session.query(Department).filter_by(Name=department_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting department by name: {e}")
            return None

    def get_all_student_groups(self) -> List[Dict[str, Any]]:
        """Отримати список всіх груп студентів для вибору розсилки."""
        try:
                groups = self.session.query(
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
                return self.session.query(StudentGroup).filter_by(GroupName=group_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting student group by name: {e}")
            return None

    def get_all_specialties(self) -> List[Dict[str, Any]]:
        """Отримати список всіх спеціальностей для вибору розсилки."""
        try:
                specialties = self.session.query(
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
                return self.session.query(Specialty).filter_by(Name=specialty_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting specialty by name: {e}")
            return None

    def get_students_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """Отримати студентів конкретної групи для розсилки оголошень."""
        try:
                students = self.session.query(
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
                students = self.session.query(
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

            students = self.session.query(
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
                students = self.session.query(
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
                students = self.session.query(
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



    def get_students_by_course_enrollment(self, course_id: int) -> List[Dict[str, Any]]:
        """Отримати студентів, записаних на конкретний курс, для розсилки оголошень."""
        try:
                students = self.session.query(
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



    def get_course_students(self, course_id: int) -> List[Dict[str, Any]]:
        try:
                students = self.session.query(
                    Student.StudentID.label("student_id"),
                    User.UserName.label("student_name"),
                    User.TelegramTag.label("telegram_tag"),
                    StudentGroup.GroupName.label("group_name")
                ).join(User, User.UserID == Student.UserID) \
                    .join(StudentGroup, StudentGroup.GroupID == Student.GroupID) \
                    .join(CourseEnrollment, CourseEnrollment.StudentID == Student.StudentID) \
                    .filter(CourseEnrollment.CourseID == course_id) \
                    .all()

                return [
                    {
                        "student_id": student.student_id,
                        "student_name": student.student_name,
                        "telegram_tag": student.telegram_tag,
                        "group_name": student.group_name
                    }
                    for student in students
                ]
        except Exception as e:
            logger.exception(f"Помилка при отриманні студентів курсу: {str(e)}")
            return []