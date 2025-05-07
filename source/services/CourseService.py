class CourseService:
    """Сервіс для роботи з курсами."""

    def __init__(self, course_repository):
        """
        Ініціалізує CourseService.

        Args:
            course_repository: Репозиторій для роботи з курсами.
        """
        self.course_repository = course_repository

    def get_student_courses(self, telegram_tag: str, active_only: bool = True) -> list[dict]:
        """
        Отримує список курсів для студента.

        Args:
            telegram_tag: Телеграм тег студента
            active_only: Фільтрувати тільки активні курси

        Returns:
            Список курсів з інформацією про викладачів
        """
        return self.course_repository.get_student_courses(telegram_tag, active_only)

    def get_teacher_courses(self, telegram_tag: str, active_only: bool = True) -> list[dict]:
        """
        Отримує список курсів, які веде викладач.

        Args:
            telegram_tag: Телеграм тег викладача
            active_only: Фільтрувати тільки активні курси

        Returns:
            Список курсів викладача
        """
        return self.course_repository.get_teacher_courses(telegram_tag, active_only)

    def get_course_students(self, course_id: int) -> list[dict]:
        """
        Отримує список студентів на курсі.

        Args:
            course_id: ID курсу

        Returns:
            Список студентів на курсі
        """
        return self.course_repository.get_course_students(course_id)

    def add_course(self, course_name: str, platform: str, link: str, telegram_tag: str) -> bool:
        """
        Додає новий курс.

        Args:
            course_name: Назва курсу
            platform: Платформа навчання
            link: Посилання на зустріч
            telegram_tag: Телеграм тег викладача

        Returns:
            True якщо курс успішно додано, інакше False
        """
        # Знаходимо ID викладача за телеграм-тегом
        teacher_id = self.course_repository.get_teacher_id_by_username(telegram_tag)
        if not teacher_id:
            return False

        # Додаємо курс
        return self.course_repository.add_new_course(course_name, platform, link, teacher_id)

    def deactivate_course(self, course_id: int) -> tuple[bool, str]:
        """
        Деактивує курс за ID.

        Args:
            course_id: ID курсу для деактивації

        Returns:
            (успішно, назва_курсу): Кортеж з булевим значенням успіху та назвою курсу
        """
        return self.course_repository.deactivate_course(course_id)

    def is_teacher(self, telegram_tag: str) -> bool:
        """
        Перевіряє, чи є користувач викладачем.

        Args:
            telegram_tag: Телеграм тег користувача

        Returns:
            True якщо користувач є викладачем, інакше False
        """
        return self.course_repository.get_teacher_id_by_username(telegram_tag) is not None