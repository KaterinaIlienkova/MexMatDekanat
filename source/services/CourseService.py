from typing import List, Dict, Any


class CourseService:
    """Сервіс для роботи з курсами."""
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    def get_student_courses(self, telegram_tag: str, active_only: bool = True) -> list[dict]:
        """
        Отримує список курсів для студента.

        Args:
            telegram_tag: Телеграм тег студента
            active_only: Фільтрувати тільки активні курси

        Returns:
            Список курсів з інформацією про викладачів
        """
        with self.uow_factory() as uow:
            return uow.student_repository.get_student_courses(telegram_tag, active_only)

    def get_teacher_courses(self, telegram_tag: str, active_only: bool = True) -> list[dict]:
        """
        Отримує список курсів, які веде викладач.

        Args:
            telegram_tag: Телеграм тег викладача
            active_only: Фільтрувати тільки активні курси

        Returns:
            Список курсів викладача
        """
        with self.uow_factory() as uow:
            return uow.course_repository.get_teacher_courses(telegram_tag, active_only)

    def get_course_students(self, course_id: int) -> list[dict]:
        """
        Отримує список студентів на курсі.

        Args:
            course_id: ID курсу

        Returns:
            Список студентів на курсі
        """
        with self.uow_factory() as uow:
            return uow.course_repository.get_course_students(course_id)

    def is_teacher(self, telegram_tag: str) -> bool:
        """
        Перевіряє, чи є користувач викладачем.

        Args:
            telegram_tag: Телеграм тег користувача

        Returns:
            True якщо користувач є викладачем, інакше False
        """
        with self.uow_factory() as uow:
            return uow.teacher_repository.get_teacher_id_by_username(telegram_tag) is not None

    def is_student(self, telegram_tag: str) -> bool:
        """
        Перевіряє, чи є користувач викладачем.

        Args:
            telegram_tag: Телеграм тег користувача

        Returns:
            True якщо користувач є викладачем, інакше False
        """
        with self.uow_factory() as uow:
            return uow.student_repository.get_student_id_by_username(telegram_tag) is not None


    def get_all_student_groups(self) -> list[dict]:
        """
        Отримує список всіх груп студентів.

        Returns:
            Список груп студентів з їх деталями
        """
        with self.uow_factory() as uow:
            return uow.student_repository.get_all_student_groups()

    def get_available_students_for_course(self, group_id: int, course_id: int) -> list[dict]:
        """
        Отримує список студентів з вказаної групи, які ще не зараховані на курс.

        Args:
            group_id: ID групи
            course_id: ID курсу

        Returns:
            Список студентів з їх деталями
        """
        with self.uow_factory() as uow:
            return uow.course_repository.get_available_students_for_course(group_id, course_id)

    def add_student_to_course(self, student_id: int, course_id: int) -> bool:
        """
        Додає студента до курсу.

        Args:
            student_id: ID студента
            course_id: ID курсу

        Returns:
            True, якщо студент успішно доданий, інакше False
        """
        with self.uow_factory() as uow:
            return uow.course_repository.add_student_to_course(student_id, course_id)

    def remove_student_from_course(self, student_id: int, course_id: int) -> bool:
        """
        Видаляє студента з курсу.

        Args:
            student_id: ID студента
            course_id: ID курсу

        Returns:
            True, якщо студент успішно видалений, інакше False
        """
        with self.uow_factory() as uow:
            return uow.course_repository.remove_student_from_course(student_id, course_id)

    def get_student_id_by_telegram(self, telegram_tag: str) -> int:
        """
        Отримує ID студента за його Telegram тегом.

        Args:
            telegram_tag: Telegram тег студента

        Returns:
            ID студента або None, якщо студента не знайдено
        """
        with self.uow_factory() as uow:
            return uow.student_repository.get_student_id_by_telegram(telegram_tag)

    def get_all_students_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """
        Отримує всіх студентів конкретної групи незалежно від зарахування на курс.

        Args:
            group_id: ID групи студентів

        Returns:
            Список студентів групи з їх деталями
        """
        with self.uow_factory() as uow:
            return uow.student_repository.get_all_students_by_group(group_id)  # ПРАВИЛЬНА НАЗВА МЕТОДУ



    def create_course(self, telegram_tag: str, name: str, study_platform: str = None, meeting_link: str = None) -> bool:
        """
        Створює новий курс для викладача.

        Args:
            telegram_tag: Телеграм тег викладача
            name: Назва курсу
            study_platform: Платформа для навчання (опціонально)
            meeting_link: Посилання на зустріч (опціонально)

        Returns:
            True якщо курс створено успішно, інакше False
        """
        with self.uow_factory() as uow:
            teacher_id = uow.teacher_repository.get_teacher_id_by_username(telegram_tag)
            if not teacher_id:
                return False

            return uow.course_repository.create_course(teacher_id, name, study_platform, meeting_link) is not None

    def archive_course(self, course_id: int) -> bool:
        """
        Архівує курс.

        Args:
            course_id: ID курсу для архівації

        Returns:
            True якщо архівація пройшла успішно, інакше False
        """
        with self.uow_factory() as uow:
            return uow.course_repository.archive_course(course_id)