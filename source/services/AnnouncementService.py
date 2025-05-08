from typing import List, Dict, Any, Optional, Union, Tuple
import logging
from datetime import datetime

from source.repositories import AnnouncementRepository

logger = logging.getLogger(__name__)


class AnnouncementService:
    def __init__(self, announcement_repository: AnnouncementRepository):
        self.announcement_repository = announcement_repository

    async def send_announcement_to_recipients(self, message: str, chat_ids: List[int], bot) -> Tuple[int, int]:
        """
        Надсилає оголошення всім отримувачам з переліку chat_ids.

        Args:
            message (str): Текст оголошення для відправки
            chat_ids (List[int]): Список chat_id користувачів для розсилки
            bot: Екземпляр Telegram бота для розсилки

        Returns:
            Tuple[int, int]: (кількість успішних відправлень, кількість невдалих відправлень)
        """
        success_count = 0
        fail_count = 0
        logger.info(f"TYPE OF MESSAGE {message}")

        for chat_id in chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=message)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to chat_id {chat_id}: {e}")
                fail_count += 1

        return success_count, fail_count

    # Методи для роботи з викладачами

    async def send_to_all_teachers(self, message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення всім викладачам."""
        teachers = self.announcement_repository.get_all_teachers()
        chat_ids = [teacher['chat_id'] for teacher in teachers if teacher['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    async def send_to_department_teachers(self, department_id: int, message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення викладачам конкретної кафедри."""
        teachers = self.announcement_repository.get_teachers_by_department(department_id)
        chat_ids = [teacher['chat_id'] for teacher in teachers if teacher['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    async def send_to_specific_teachers(self, teacher_ids: List[int], message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення конкретним викладачам за їх ID."""
        teachers = self.announcement_repository.get_teachers_by_ids(teacher_ids)
        chat_ids = [teacher['chat_id'] for teacher in teachers if teacher['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    # Методи для роботи зі студентами

    async def send_to_all_students(self, message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення всім студентам."""
        students = self.announcement_repository.get_all_students()
        chat_ids = [student['chat_id'] for student in students if student['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    async def send_to_group_students(self, group_id: int, message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення студентам конкретної групи."""
        students = self.announcement_repository.get_students_by_group(group_id)
        chat_ids = [student['chat_id'] for student in students if student['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    async def send_to_specialty_students(self, specialty_id: int, message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення студентам конкретної спеціальності."""
        students = self.announcement_repository.get_students_by_specialty(specialty_id)
        chat_ids = [student['chat_id'] for student in students if student['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    async def send_to_course_year_students(self, course_year: int, message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення студентам конкретного курсу навчання."""
        students = self.announcement_repository.get_students_by_course_year(course_year)
        chat_ids = [student['chat_id'] for student in students if student['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    async def send_to_course_enrollment_students(self, course_id: int, message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення студентам, які записані на конкретний курс."""
        students = self.announcement_repository.get_students_by_course_enrollment(course_id)
        chat_ids = [student['chat_id'] for student in students if student['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    async def send_to_specific_students(self, student_ids: List[int], message: str, bot) -> Tuple[int, int]:
        """Надіслати оголошення конкретним студентам за їх ID."""
        students = self.announcement_repository.get_students_by_ids(student_ids)
        chat_ids = [student['chat_id'] for student in students if student['chat_id']]

        return await self.send_announcement_to_recipients(message, chat_ids, bot)

    # Допоміжні методи для отримання списків для вибору

    def get_departments_list(self) -> List[Dict[str, Any]]:
        """Отримати список кафедр для вибору розсилки."""
        return self.announcement_repository.get_all_departments()

    def get_student_groups_list(self) -> List[Dict[str, Any]]:
        """Отримати список студентських груп для вибору розсилки."""
        return self.announcement_repository.get_all_student_groups()

    def get_specialties_list(self) -> List[Dict[str, Any]]:
        """Отримати список спеціальностей для вибору розсилки."""
        return self.announcement_repository.get_all_specialties()

    def get_courses_list(self) -> List[Dict[str, Any]]:
        """Отримати список курсів для вибору розсилки."""
        return self.announcement_repository.get_all_courses()

    def get_teachers_list(self) -> List[Dict[str, Any]]:
        """Отримати список всіх викладачів для індивідуального вибору."""
        teachers = self.announcement_repository.get_all_teachers()
        return [{'teacher_id': t['teacher_id'], 'name': t['username'], 'department': t['department']} for t in teachers]

    def get_students_list(self) -> List[Dict[str, Any]]:
        """Отримати список всіх студентів для індивідуального вибору."""
        students = self.announcement_repository.get_all_students()
        return [{'student_id': s['student_id'], 'name': s['username'], 'group': s['group_name']} for s in students]

    def get_course_years_list(self) -> List[Dict[str, int]]:
        """Отримати список доступних курсів навчання (1-6)."""
        # Зазвичай в університеті є від 1 до 6 курсів (бакалаврат + магістратура)
        return [{'course_year': year, 'name': f"{year} курс"} for year in range(1, 7)]

    def get_recipients_count(self, recipient_type: str, target_id: Optional[int] = None, ids_list: Optional[List[int]] = None) -> int:
        """
        Отримати кількість отримувачів для обраного типу розсилки.

        Args:
            recipient_type (str): Тип отримувачів ('all_teachers', 'department_teachers', 'specific_teachers',
                                'all_students', 'group_students', 'specialty_students', 'course_year_students',
                                'course_enrollment_students', 'specific_students')
            target_id (Optional[int]): ID цільової групи (кафедри, групи, спеціальності тощо)
            ids_list (Optional[List[int]]): Список ID для конкретних отримувачів

        Returns:
            int: Кількість отримувачів
        """
        if recipient_type == 'all_teachers':
            return len(self.announcement_repository.get_all_teachers())
        elif recipient_type == 'department_teachers' and target_id:
            return len(self.announcement_repository.get_teachers_by_department(target_id))
        elif recipient_type == 'specific_teachers' and ids_list:
            return len(self.announcement_repository.get_teachers_by_ids(ids_list))
        elif recipient_type == 'all_students':
            return len(self.announcement_repository.get_all_students())
        elif recipient_type == 'group_students' and target_id:
            return len(self.announcement_repository.get_students_by_group(target_id))
        elif recipient_type == 'specialty_students' and target_id:
            return len(self.announcement_repository.get_students_by_specialty(target_id))
        elif recipient_type == 'course_year_students' and target_id:
            return len(self.announcement_repository.get_students_by_course_year(target_id))
        elif recipient_type == 'course_enrollment_students' and target_id:
            return len(self.announcement_repository.get_students_by_course_enrollment(target_id))
        elif recipient_type == 'specific_students' and ids_list:
            return len(self.announcement_repository.get_students_by_ids(ids_list))
        return 0

