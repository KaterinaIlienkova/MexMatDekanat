from typing import List, Dict, Any, Optional, Union, Tuple
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


class AnnouncementService:
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    async def send_announcement_to_recipients(self, message: str, chat_ids: List[str], bot, media_type=None, media_content=None) -> Tuple[int, int]:
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

        if media_type:
            logger.info(f"З медиа типа {media_type}, ID: {media_content}")

        for chat_id in chat_ids:
            try:
                if media_type == 'photo' and media_content:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=media_content,
                        caption=message
                    )
                elif media_type == 'video' and media_content:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=media_content,
                        caption=message
                    )
                elif media_type == 'document' and media_content:
                    await bot.send_document(
                        chat_id=chat_id,
                        document=media_content,
                        caption=message
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message
                    )

                success_count += 1
            except Exception as e:
                logger.error(f"Помилка при надсиланні повідомлення до {chat_id}: {e}")
                fail_count += 1

        return success_count, fail_count

    # Методи для роботи з викладачами

    async def send_to_all_teachers(self, message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення всім викладачам."""
        with self.uow_factory() as uow:
            teachers = uow.teacher_repository.get_all_teachers()
            chat_ids = [teacher['chat_id'] for teacher in teachers if teacher['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    async def send_to_department_teachers(self, department_id: int, message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення викладачам конкретної кафедри."""
        with self.uow_factory() as uow:
            teachers =  uow.teacher_repository.get_teachers_by_departmentID(department_id)
            chat_ids = [teacher['chat_id'] for teacher in teachers if teacher['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    async def send_to_specific_teachers(self, teacher_ids: List[int], message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення конкретним викладачам за їх ID."""
        with self.uow_factory() as uow:
            teachers = uow.teacher_repository.get_teachers_by_ids(teacher_ids)
            chat_ids = [teacher['chat_id'] for teacher in teachers if teacher['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    # Методи для роботи зі студентами

    async def send_to_all_students(self, message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення всім студентам."""
        with self.uow_factory() as uow:
            students = uow.student_repository.get_all_students()
            chat_ids = [student['chat_id'] for student in students if student['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    async def send_to_group_students(self, group_id: int, message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення студентам конкретної групи."""
        with self.uow_factory() as uow:
            students = uow.student_repository.get_students_by_group_to_announce(group_id)
            chat_ids = [student['chat_id'] for student in students if student['chat_id']]

            return await uow.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    async def send_to_specialty_students(self, specialty_id: int, message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення студентам конкретної спеціальності."""
        with self.uow_factory() as uow:
            students = uow.student_repository.get_students_by_specialty(specialty_id)
            chat_ids = [student['chat_id'] for student in students if student['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    async def send_to_course_year_students(self, course_year: int, message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення студентам конкретного курсу навчання."""
        with self.uow_factory() as uow:
            students = uow.student_repository.get_students_by_course_year(course_year)
            chat_ids = [student['chat_id'] for student in students if student['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    async def send_to_course_enrollment_students(self, course_id: int, message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення студентам, які записані на конкретний курс."""
        with self.uow_factory() as uow:
            students = uow.student_repository.get_students_by_course_enrollment(course_id)
            chat_ids = [student['chat_id'] for student in students if student['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    async def send_to_specific_students(self, student_ids: List[int], message: str, bot, media_type=None, media_content=None) -> Tuple[int, int]:
        """Надіслати оголошення конкретним студентам за їх ID."""
        with self.uow_factory() as uow:
            students = uow.student_repository.get_students_by_ids(student_ids)
            chat_ids = [student['chat_id'] for student in students if student['chat_id']]

            return await self.send_announcement_to_recipients(message, chat_ids, bot, media_type=media_type, media_content=media_content)

    def get_teacher_students(self, teacher_telegram_tag: str) -> List[Dict[str, Any]]:
        """
        Отримати список всіх студентів, які записані хоча б на один курс викладача.

        Args:
            teacher_telegram_tag: Telegram тег викладача

        Returns:
            List[Dict[str, Any]]: Список студентів
        """
    # Отримуємо всі курси викладача
        with self.uow_factory() as uow:
            teacher_courses = uow.course_repository.get_teacher_courses(teacher_telegram_tag, active_only=True)

            # Збираємо унікальних студентів з усіх курсів
            all_students = {}
            for course in teacher_courses:
                course_id = course['course_id']
                students = uow.course_repository.get_all_course_students(course_id)

                for student in students:
                    if 'student_id' in student and student['student_id']:
                        student_id = student['student_id']
                        all_students[student_id] = {
                                'student_id': student_id,
                                'student_name': student.get('student_name', 'Без імені'),
                                'group_name': student.get('group_name', 'Невідома група')
                        }

            # Повертаємо список словників
            return list(all_students.values())

    def get_teacher_course_enrollments(self, teacher_telegram_tag: str) -> List[Dict[str, Any]]:
        """
        Отримати список курсів викладача для вибору в розсилці.

        Args:
            teacher_telegram_tag: Telegram тег викладача

        Returns:
            List[Dict[str, Any]]: Список курсів
        """
        with self.uow_factory() as uow:
            teacher_courses = uow.course_repository.get_teacher_courses(teacher_telegram_tag, active_only=True)
            courses_list = []

            for course in teacher_courses:
                courses_list.append({
                    'course_id': course['course_id'],
                    'name': course['course_name'],
                    'teacher': "Ви"  # оскільки це власні курси викладача
                })

            return courses_list
    # Допоміжні методи для отримання списків для вибору


    def get_student_groups_list(self) -> List[Dict[str, Any]]:
        """Отримати список студентських груп для вибору розсилки."""
        with self.uow_factory() as uow:
            return uow.studentGroup_repository_repository.get_all_student_groups()

    def get_specialties_list(self) -> List[Dict[str, Any]]:
        """Отримати список спеціальностей для вибору розсилки."""
        with self.uow_factory() as uow:
            return uow.specialty_repository.get_all_specialties()

    def get_courses_list(self) -> List[Dict[str, Any]]:
        """Отримати список курсів для вибору розсилки."""
        with self.uow_factory() as uow:
            return uow.course_repository.get_all_courses()

    def get_teachers_list(self) -> List[Dict[str, Any]]:
        """Отримати список всіх викладачів для індивідуального вибору."""
        with self.uow_factory() as uow:
            teachers = uow.teacher_repository.get_all_teachers()
            return [{'teacher_id': t['teacher_id'], 'name': t['username'], 'department': t['department']} for t in teachers]

    def get_students_list(self) -> List[Dict[str, Any]]:
        """Отримати список всіх студентів для індивідуального вибору."""
        with self.uow_factory() as uow:
            students = uow.student_repository.get_all_students()
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
        with self.uow_factory() as uow:
            if recipient_type == 'all_teachers':
                return len(uow.teacher_repository.get_all_teachers())
            elif recipient_type == 'department_teachers' and target_id:
                return len(uow.announcement_repository.get_teachers_by_departmentID(target_id))
            elif recipient_type == 'specific_teachers' and ids_list:
                return len(uow.teacher_repository.get_teachers_by_ids(ids_list))
            elif recipient_type == 'all_students':
                return len(uow.student_repository.get_all_students())
            elif recipient_type == 'group_students' and target_id:
                return len(uow.student_repository.get_students_by_group_to_announce(target_id))
            elif recipient_type == 'specialty_students' and target_id:
                return len(uow.student_repository.get_students_by_specialty(target_id))
            elif recipient_type == 'course_year_students' and target_id:
                return len(uow.student_repository.get_students_by_course_year(target_id))
            elif recipient_type == 'course_enrollment_students' and target_id:
                return len(uow.student_repository.get_students_by_course_enrollment(target_id))
            elif recipient_type == 'specific_students' and ids_list:
                return len(uow.student_repository.get_students_by_ids(ids_list))
            return 0
