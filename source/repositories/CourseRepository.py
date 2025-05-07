from sqlalchemy.exc import SQLAlchemyError
from source.config import logger
from source.models import Course, Teacher, User, CourseEnrollment, Student


class CourseRepository:
    """Репозиторій для роботи з курсами в базі даних."""

    def __init__(self, get_session):
        """
        Ініціалізує CourseRepository.

        Args:
            get_session: Функція, яка повертає сесію SQLAlchemy.
        """
        self.get_session = get_session

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
            with self.get_session() as session:
                # Знаходимо студента за telegram_tag
                student = session.query(Student).join(User, User.UserID == Student.UserID) \
                    .filter(User.TelegramTag == telegram_tag).first()

                if not student:
                    return []

                # Запит для отримання курсів через CourseEnrollment
                courses_query = session.query(
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

    def add_new_course(self, course_name: str, platform: str, link: str, teacher_id: int) -> bool:
        """
        Додає новий курс до бази даних.

        Args:
            course_name: Назва курсу
            platform: Платформа для навчання
            link: Посилання на зустріч
            teacher_id: ID викладача

        Returns:
            True, якщо курс успішно додано, інакше False
        """
        try:
            with self.get_session() as session:
                new_course = Course(
                    Name=course_name,
                    StudyPlatform=platform,
                    MeetingLink=link,
                    TeacherID=teacher_id,
                    IsActive=True
                )
                session.add(new_course)
                session.commit()
                return True
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при додаванні курсу: {e}")
            session.rollback()
            return False

    def deactivate_course(self, course_id: int) -> tuple[bool, str]:
        """
        Деактивує курс за його ID та повертає статус і назву.

        Args:
            course_id: ID курсу для деактивації

        Returns:
            (успішно, назва_курсу): Кортеж з булевим значенням успіху та назвою курсу
        """
        try:
            with self.get_session() as session:
                course = session.query(Course).filter(Course.CourseID == course_id).first()
                if course:
                    course.IsActive = False
                    session.commit()
                    return True, course.Name
                return False, ""
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при деактивації курсу: {e}")
            session.rollback()
            return False, ""

    def get_teacher_id_by_username(self, username: str) -> int:
        """
        Отримує ID викладача за телеграм-тегом.

        Args:
            username: Телеграм-тег викладача

        Returns:
            ID викладача або None, якщо викладача не знайдено
        """
        try:
            with self.get_session() as session:
                teacher = session.query(Teacher).join(User).filter(User.TelegramTag == username).first()
                return teacher.TeacherID if teacher else None
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні ID викладача: {e}")
            return None