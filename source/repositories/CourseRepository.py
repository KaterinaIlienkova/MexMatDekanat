from typing import List, Dict, Any

from sqlalchemy.exc import SQLAlchemyError
from source.config import logger
from source.models import Course, Teacher, User, CourseEnrollment, Student, StudentGroup, Specialty
from source.repositories.BaseRepository import BaseRepository


class CourseRepository(BaseRepository):
    """Репозиторій для роботи з курсами в базі даних."""


    def get_all_courses(self) -> List[Dict[str, Any]]:
        """Отримати список всіх курсів для вибору розсилки."""
        try:
            courses = self.session.query(
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

    def get_teacher_courses(self, telegram_tag: str, active_only: bool = True) -> list[dict]:
        """
        Отримує список курсів, які веде викладач за його Telegram тегом.

        Args:
            telegram_tag: Телеграм тег викладача
            active_only: Якщо True, повертає тільки активні курси

        Returns:
            Список курсів з їх деталями
        """
        try:
                # Знаходимо викладача за Telegram тегом
                teacher = self.session.query(Teacher).join(User, User.UserID == Teacher.UserID) \
                    .filter(User.TelegramTag == telegram_tag).first()

                if not teacher:
                    return []

                # Запит для отримання курсів викладача
                courses_query = self.session.query(
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

    from typing import List, Dict, Any

    def get_all_course_students(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Отримує повну інформацію про студентів, які записані на курс.

        Args:
            course_id: ID курсу

        Returns:
            Список словників з деталями студентів
        """
        try:
            students = self.session.query(
                Student.StudentID.label("student_id"),
                User.UserName.label("student_name"),
                User.PhoneNumber.label("student_phone"),
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
                    "student_phone": student.student_phone or "Не вказано",
                    "telegram_tag": student.telegram_tag,
                    "group_name": student.group_name
                }
                for student in students
            ]

        except Exception as e:
            logger.exception(f"Помилка при отриманні студентів курсу: {str(e)}")
            return []




    def add_student_to_course(self, student_id: int, course_id: int) -> bool:
        """
        Додає студента до курсу.

        Args:
            student_id: ID студента
            course_id: ID курсу

        Returns:
            True, якщо студент успішно доданий, інакше False
        """
        try:
                # Перевіряємо, чи існує вже такий запис
                existing_enrollment = self.session.query(CourseEnrollment).filter(
                    CourseEnrollment.StudentID == student_id,
                    CourseEnrollment.CourseID == course_id
                ).first()

                if existing_enrollment:
                    return False  # Студент вже зарахований на курс

                # Створюємо новий запис
                new_enrollment = CourseEnrollment(
                    StudentID=student_id,
                    CourseID=course_id
                )

                self.session.add(new_enrollment)
                self.session.commit()

                return True
        except Exception as e:
            logger.exception(f"Помилка при додаванні студента до курсу: {str(e)}")
            return False

    def remove_student_from_course(self, student_id: int, course_id: int) -> bool:
        """
        Видаляє студента з курсу.

        Args:
            student_id: ID студента
            course_id: ID курсу

        Returns:
            True, якщо студент успішно видалений, інакше False
        """
        try:
                # Знаходимо запис про зарахування
                enrollment = self.session.query(CourseEnrollment).filter(
                    CourseEnrollment.StudentID == student_id,
                    CourseEnrollment.CourseID == course_id
                ).first()

                if not enrollment:
                    return False  # Студент не зарахований на курс

                # Видаляємо запис
                self.session.delete(enrollment)
                self.session.commit()

                return True
        except Exception as e:
            logger.exception(f"Помилка при видаленні студента з курсу: {str(e)}")
            return False

    def create_course(self, teacher_id: int, name: str, study_platform: str = None, meeting_link: str = None) -> int:
            """
                Створює новий курс.

                Args:
                    teacher_id: ID викладача
                    name: Назва курсу
                    study_platform: Платформа для навчання (опціонально)
                    meeting_link: Посилання на зустріч (опціонально)

                Returns:
                    ID створеного курсу або None у випадку помилки
                """
            try:
                    new_course = Course(
                        Name=name,
                        StudyPlatform=study_platform,
                        MeetingLink=meeting_link,
                        TeacherID=teacher_id,
                        IsActive=True
                    )
                    self.session.add(new_course)
                    self.session.commit()
                    return new_course.CourseID
            except SQLAlchemyError as e:
                logger.exception(f"Помилка при створенні курсу: {e}")
                return None

    def archive_course(self, course_id: int) -> bool:
        """
        Архівує курс (встановлює IsActive = False).

        Args:
            course_id: ID курсу для архівації

        Returns:
            True якщо архівація пройшла успішно, інакше False
        """
        try:
                course = self.session.query(Course).filter(Course.CourseID == course_id).first()
                if course:
                    course.IsActive = False
                    self.session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при архівації курсу: {e}")
            return False