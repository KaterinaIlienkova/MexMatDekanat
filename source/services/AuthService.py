from source.config import logger
from source.models import User, Student, Teacher
from source.repositories import AuthRepository
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from typing import Optional, List, Dict, Any, Tuple

class AuthService:
    def __init__(self, uow_factory):
        """
        Initialize with a UnitOfWork factory function.

        Args:
            uow_factory: A function that returns a UnitOfWork instance
        """
        self.uow_factory = uow_factory

    async def check_and_register_user(self, update, context, telegram_tag, chat_id):
        # Create a UnitOfWork instance using the factory
        with self.uow_factory() as uow:
            user = uow.auth_repository.get_user_by_telegram_tag(telegram_tag)

            if not user:
                context.user_data["state"] = "WAITING_FOR_STUDENT_DETAILS"
                context.user_data["new_telegram_tag"] = telegram_tag
                context.user_data["new_chat_id"] = chat_id
                context.user_data["new_role"] = "student"

                await update.message.reply_text(
                    "🔒 Ви не зареєстровані.\n"
                    "Будь ласка, надайте додаткові дані для завершення реєстрації.\n\n"
                    "✏️ Приклад:\n"
                    "Іван Петренко, +380961234567, ФІ-21, 2023, Комп'ютерні науки"
                )
                return None

            if not user.IsConfirmed:
                await update.message.reply_text("⏳ Ваша заявка на реєстрацію ще не підтверджена.")
                return None

            uow.auth_repository.update_chat_id(user, chat_id)
            return user.Role

    def create_user(self, username, telegram_tag, role, phone_number,
                    chat_id=None, is_confirmed=False):
        """Створює нового користувача в системі."""
        with self.uow_factory() as uow:
            user = uow.auth_repository.add_user(username, telegram_tag, role, phone_number, chat_id, is_confirmed)
            if user:
                return {
                    'UserID': user.UserID,
                    'UserName': user.UserName,
                    'TelegramTag': user.TelegramTag,
                    'Role': user.Role,
                    'PhoneNumber': user.PhoneNumber,
                    'ChatID': user.ChatID,
                    'IsConfirmed': user.IsConfirmed
                }
            return None

    def get_or_create_student_group(self, group_name, specialty_name=None):
        """
        Повертає ID існуючої групи або створює нову (разом із спеціальністю), якщо потрібно.
        """
        with self.uow_factory() as uow:
            student_group = uow.studentGroup_repository.get_student_group_by_name(group_name)
            if student_group:
                return student_group.GroupID

            if specialty_name:
                specialty = uow.specialty_repository.get_specialty_by_name(specialty_name)
                if not specialty:
                    specialty_id = uow.specialty_repository.add_specialty_and_get_id(specialty_name)
                    if not specialty_id:
                        return None
                else:
                    specialty_id = specialty.SpecialtyID

                group_id = uow.studentGroup_repository.add_student_group(group_name, specialty_id)
                return group_id

            return None

    def get_or_create_department(self, department_name):
        """Отримує існуючий департамент або створює новий. Повертає ID департаменту."""
        with self.uow_factory() as uow:
            department = uow.department_repository.get_department_by_name(department_name)
            if not department:
                department = uow.department_repository.add_department(department_name)

            return department.DepartmentID if department else None

    def create_student(self, user_data):
        """
        Створює нового студента з комплексними даними.

        Args:
            user_data: Словник з даними користувача і студента

        Returns:
            Словник з даними створеного студента або None у випадку помилки
        """
        with self.uow_factory() as uow:
            # 1. Створюємо базового користувача
            user_dict = self.create_user(
                username=user_data['username'],
                telegram_tag=user_data['telegram_tag'],
                role='student',
                phone_number=user_data['phone_number'],
                chat_id=user_data.get('chat_id'),
                is_confirmed=user_data.get('is_confirmed', False)
            )

            if not user_dict:
                logger.error("Failed to create user")
                return None

            # 2. Отримуємо або створюємо групу
            group_id = self.get_or_create_student_group(
                user_data['group_name'],
                user_data.get('specialty_name')
            )

            if not group_id:
                logger.error(f"Failed to get or create group {user_data['group_name']}")
                return None

            # 3. Створюємо запис студента
            student = uow.auth_repository.add_student(
                user_id=user_dict['UserID'],
                group_id=group_id,
                admission_year=user_data['admission_year']
            )

            if student:
                return {
                    'StudentID': student.StudentID,
                    'UserID': student.UserID,
                    'GroupID': student.GroupID,
                    'AdmissionYear': student.AdmissionYear
                }
            return None

    def create_teacher(self, user_data):
        """
        Створює нового викладача з комплексними даними.

        Args:
            user_data: Словник з даними користувача і викладача

        Returns:
            Словник з даними створеного викладача або None у випадку помилки
        """
        with self.uow_factory() as uow:
            # 1. Створюємо базового користувача
            user_dict = self.create_user(
                username=user_data['username'],
                telegram_tag=user_data['telegram_tag'],
                role='teacher',
                phone_number=user_data['phone_number'],
                chat_id=user_data.get('chat_id'),
                is_confirmed=user_data.get('is_confirmed', False)
            )

            if not user_dict:
                logger.error("Failed to create user")
                return None

            # 2. Отримуємо або створюємо департамент
            department_id = self.get_or_create_department(user_data['department_name'])

            if not department_id:
                logger.error(f"Failed to get or create department {user_data['department_name']}")
                return None

            # 3. Створюємо запис викладача
            teacher = uow.teacher_repository.add_teacher(
                user_id=user_dict['UserID'],
                email=user_data['email'],
                department_id=department_id
            )

            if teacher:
                return {
                    'TeacherID': teacher.TeacherID,
                    'UserID': teacher.UserID,
                    'Email': teacher.Email,
                    'DepartmentID': teacher.DepartmentID
                }
            return None

    async def save_new_user_telegram(self, update, context):
        """
        Зберігає нового користувача з даних Telegram бота.
        Ця функція обробляє дані, отримані під час діалогу з ботом.
        """
        user_data = context.user_data

        if not user_data or 'role' not in user_data:
            await update.message.reply_text("❌ Недостатньо даних для створення користувача.")
            return None

        # Базові дані користувача
        telegram_user = update.effective_user
        chat_id = update.effective_chat.id

        # Створюємо об'єкт з базовими даними
        base_user_data = {
            'username': user_data.get('username', telegram_user.full_name),
            'telegram_tag': user_data.get('telegram_tag', telegram_user.username),
            'phone_number': user_data.get('phone_number', ''),
            'chat_id': chat_id,
            'is_confirmed': True  # Автоматично підтверджуємо, оскільки додає працівник деканату
        }

        # Залежно від ролі, додаємо додаткові дані і викликаємо відповідний метод
        role = user_data['role']
        result = None

        if role == 'student':
            # Додаємо специфічні дані студента до словника
            student_data = {
                **base_user_data,
                'group_name': user_data.get('group_name', ''),
                'specialty_name': user_data.get('specialty_name', None),
                'admission_year': user_data.get('admission_year', 0)
            }

            result = self.create_student(student_data)
            if result:
                await update.message.reply_text("✅ Студента успішно додано до системи!")
            else:
                await update.message.reply_text("❌ Помилка при додаванні студента.")

        elif role == 'teacher':
            # Додаємо специфічні дані викладача до словника
            teacher_data = {
                **base_user_data,
                'email': user_data.get('email', ''),
                'department_name': user_data.get('department_name', '')
            }

            result = self.create_teacher(teacher_data)
            if result:
                await update.message.reply_text("✅ Викладача успішно додано до системи!")
            else:
                await update.message.reply_text("❌ Помилка при додаванні викладача.")
        else:
            await update.message.reply_text("❌ Непідтримувана роль користувача.")

        return result

    def get_unconfirmed_students(self):
        """Отримує список непідтверджених студентів з деталями."""
        with self.uow_factory() as uow:
            students_with_details = uow.auth_repository.get_unconfirmed_students_with_details()

            result = []
            for user, student, group in students_with_details:
                result.append({
                    'user_id': user.UserID,
                    'username': user.UserName,
                    'telegram_tag': user.TelegramTag,
                    'phone_number': user.PhoneNumber,
                    'student_id': student.StudentID,
                    'group_name': group.GroupName,
                    'admission_year': student.AdmissionYear
                })

            return result

    def confirm_user(self, user_id):
        """Підтверджує користувача."""
        with self.uow_factory() as uow:
            return uow.auth_repository.confirm_user(user_id)

    def delete_user(self, user_id):
        """Видаляє користувача."""
        with self.uow_factory() as uow:
            return uow.auth_repository.delete_user(user_id)

    def update_student_info(self, user_id, update_data):
        """Оновлює інформацію про студента."""
        with self.uow_factory() as uow:
            return uow.auth_repository.update_student_info(user_id, update_data)

    def get_student_groups(self):
        """Отримує список всіх груп студентів."""
        with self.uow_factory() as uow:
            groups = uow.auth_repository.get_student_groups()
            return [(group.GroupID, group.GroupName) for group in groups]

    async def get_admission_years(self):
        """Отримує список років вступу студентів."""
        with self.uow_factory() as uow:
            return uow.auth_repository.get_admission_years()

    async def get_groups_by_admission_year(self, admission_year):
        """Отримує список груп студентів за роком вступу."""
        with self.uow_factory() as uow:
            return uow.studentGroup_repository.get_groups_by_admission_year(admission_year)

    async def get_departments(self):
        """Отримує список всіх кафедр."""
        with self.uow_factory() as uow:
            return uow.department_repository.get_departments()

    async def get_teachers_by_department(self, department_name):
        """Отримує список викладачів із конкретної кафедри."""
        with self.uow_factory() as uow:
            return uow.teacher_repository.get_teachers_by_department(department_name)

    async def get_students_by_group_and_course(self, group_name, admission_year):
        """Отримує список студентів із конкретної групи та року вступу."""
        with self.uow_factory() as uow:
            return uow.auth_repository.get_students_by_group_and_course(group_name, admission_year)

    async def get_user_info(self, user_id):
        """Отримує детальну інформацію про користувача."""
        with self.uow_factory() as uow:
            return uow.auth_repository.get_user_info(user_id)

    async def get_user_by_chat_id(self, chat_id):
        """
        Отримує користувача за chat_id і повертає всі необхідні дані про користувача,
        а не сам об'єкт користувача.
        """
        with self.uow_factory() as uow:
            user = uow.auth_repository.get_user_by_chat_id(chat_id)
            # Якщо користувач існує, зберегти необхідні дані перед закриттям сесії
            if user:
                # Створюємо словник з даними користувача, які нам потрібні
                user_data = {
                    'UserID': user.UserID,
                    'Role': user.Role,
                    'TelegramTag': user.TelegramTag,
                    'ChatID': user.ChatID,
                    'IsConfirmed': user.IsConfirmed
                    # Додайте інші поля, які можуть знадобитися
                }
                return user_data
            return None