from sqlalchemy.exc import SQLAlchemyError
from source.config import logger
from source.models import Course, Teacher, User, CourseEnrollment, Student, StudentGroup, Specialty
from source.repositories.BaseRepository import BaseRepository


class CourseRepository(BaseRepository):
    """Репозиторій для роботи з курсами в базі даних."""


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

    def get_course_students(self, course_id: int) -> list[dict]:
        """
        Отримує список студентів на конкретному курсі за його ID.

        Args:
            course_id: ID курсу

        Returns:
            Список студентів з їх деталями
        """
        try:
                # Запит для отримання студентів на курсі
                students_query = self.session.query(
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


    def get_all_student_groups(self) -> list[dict]:
        """
        Отримує список всіх груп студентів.

        Returns:
            Список груп студентів з їх деталями
        """
        try:
                groups = self.session.query(
                    StudentGroup.GroupID,
                    StudentGroup.GroupName,
                    Specialty.Name.label("specialty_name")
                ).join(
                    Specialty,
                    StudentGroup.SpecialtyID == Specialty.SpecialtyID,
                    isouter=True
                ).all()

                groups_list = []
                for group in groups:
                    group_dict = {
                        "group_id": group.GroupID,
                        "group_name": group.GroupName,
                        "specialty": group.specialty_name if group.specialty_name else "Не вказано"
                    }
                    groups_list.append(group_dict)

                return groups_list
        except Exception as e:
            logger.exception(f"Помилка при отриманні груп студентів: {str(e)}")
            return []

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