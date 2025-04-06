from sqlalchemy.exc import SQLAlchemyError
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from sqlalchemy.orm import Session

from source.config import WAITING_FOR_USER_ROLE
from source.database import SessionLocal
from sqlalchemy import text
from typing import Any, Optional
from sqlalchemy.orm import Session
from source.models import User, Student, Teacher, StudentGroup, DeanOfficeStaff, Department, Specialty
import logging
logger = logging.getLogger(__name__)

from source.models import Student, StudentGroup, Department, Teacher, User

async def check_registration(update: Update, context: CallbackContext) -> Any | None:
    """Перевіряє, чи зареєстрований користувач, і повертає його роль"""
    with SessionLocal() as db:
        telegram_tag = update.message.from_user.username
        chat_id = update.effective_chat.id
        if telegram_tag:
            update_chat_id(db, telegram_tag, chat_id)
        role = get_user_role(db, telegram_tag)
        if role == "Невідомий":
            await update.message.reply_text("Ви не зареєстровані. "
                                            "Будь ласка, зверніться до працівника деканату.")
            return None
        return role

def get_user_role(session: Session, telegram_tag: str) -> str:
    """Отримує роль користувача за TelegramTag."""
    try:
        user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
        return user.Role if user else "Невідомий"
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при отриманні ролі користувача: {e}")
        return "Невідомий"

def update_chat_id(session: Session, telegram_tag: str, chat_id: int) -> bool:
    """Оновлює chat_id користувача."""
    try:
        user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
        if user:
            user.ChatID = chat_id
            session.commit()
            return True
        return False
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при оновленні chat_id користувача: {e}")
        session.rollback()
        return False



async def start(update: Update, context: CallbackContext):
    """Обробляє команду /start."""
    role = await check_registration(update, context)
    if role is None:
        return  # Виходимо, якщо користувач не зареєстрований

    if role == "dean_office":
        keyboard = [[KeyboardButton("Інструкції"), KeyboardButton("Додати користувача"),
                     KeyboardButton("Редагувати Q&A"), KeyboardButton("Оголошення")]]
    elif role == "student":
        keyboard = [[KeyboardButton("Q&A")]]  # Q&A на панельці для студентів
    else:
        keyboard = []

    if keyboard:
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text(
            f"Вітаю, {update.message.from_user.username}! Ви зареєстровані як {role}.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"Вітаю, {update.message.from_user.username}! Ви зареєстровані як {role}."
        )


def add_user(session: Session, username: str, telegram_tag: str, role: str, phone_number: str, chat_id: Optional[int] = None, group_name: Optional[str] = None, admission_year: Optional[int] = None, email: Optional[str] = None, department_id: Optional[int] = None, position: Optional[str] = None) -> Optional[User]:
    """
    Додає нового користувача і відповідний запис у відповідну таблицю на основі ролі.
    """
    existing_user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
    if existing_user:
        return None  # Користувач вже існує

    # Створюємо нового користувача
    user = User(
        UserName=username,
        TelegramTag=telegram_tag,
        Role=role,
        PhoneNumber=phone_number,
        ChatID=chat_id
    )

    session.add(user)
    session.flush()  # Отримуємо UserID не комітячи

    # Додаємо дані в залежності від ролі
    if role == "student" and group_name and admission_year:
        student_group = session.query(StudentGroup).filter_by(GroupName=group_name).first()
        if not student_group:
            session.rollback()
            raise ValueError(f"Група '{group_name}' не знайдена")

        student = Student(
            UserID=user.UserID,
            GroupID=student_group.GroupID,
            AdmissionYear=admission_year
        )
        session.add(student)

    elif role == "teacher" and email and department_id:
        teacher = Teacher(
            UserID=user.UserID,
            Email=email,
            DepartmentID=department_id
        )
        session.add(teacher)

    elif role == "dean_office" and position:
        staff = DeanOfficeStaff(
            UserID=user.UserID,
            Position=position
        )
        session.add(staff)

    session.commit()
    return user


def add_student(session: Session, user_id: int, group_name: str, admission_year: int, specialty_name: Optional[str] = None) -> bool:
    """
    Додає запис студента для існуючого користувача.
    Якщо вказана спеціальність і група не існує, створює нову групу з цією спеціальністю.
    """
    try:
        # Перевіряємо чи існує користувач
        user = session.query(User).filter_by(UserID=user_id).first()
        if not user:
            return False

        # Шукаємо групу
        student_group = session.query(StudentGroup).filter_by(GroupName=group_name).first()

        # Якщо групи немає і вказана спеціальність, створюємо нову групу
        if not student_group and specialty_name:
            # Шукаємо спеціальність
            specialty = session.query(Specialty).filter_by(Name=specialty_name).first()
            if not specialty:
                # Створюємо нову спеціальність, якщо не існує
                specialty = Specialty(Name=specialty_name)
                session.add(specialty)
                session.flush()

            # Створюємо нову групу
            student_group = StudentGroup(
                GroupName=group_name,
                SpecialtyID=specialty.SpecialtyID
            )
            session.add(student_group)
            session.flush()
        elif not student_group:
            return False  # Група не існує і не можемо створити нову без спеціальності

        # Створюємо запис студента
        new_student = Student(
            UserID=user_id,
            GroupID=student_group.GroupID,
            AdmissionYear=admission_year
        )

        session.add(new_student)
        session.commit()
        return True
    except Exception as e:
        logger.exception("Помилка при додаванні студента: %s", e)
        session.rollback()
        return False


def add_teacher(session: Session, user_id: int, email: str, department_id: int) -> bool:
    """
    Додає запис викладача для існуючого користувача.
    """
    try:
        # Перевіряємо чи існує користувач
        user = session.query(User).filter_by(UserID=user_id).first()
        if not user:
            return False

        # Перевіряємо чи існує департамент
        department = session.query(Department).filter_by(DepartmentID=department_id).first()
        if not department:
            return False

        # Створюємо запис викладача
        new_teacher = Teacher(
            UserID=user_id,
            Email=email,
            DepartmentID=department_id
        )

        session.add(new_teacher)
        session.commit()
        return True
    except Exception as e:
        logger.exception("Помилка при додаванні викладача: %s", e)
        session.rollback()
        return False


async def save_new_user(update: Update, context: CallbackContext):
    """Зберігає нового користувача в БД через ORM."""
    with SessionLocal() as db:
        user = add_user(db, context.user_data["new_user_name"], context.user_data["new_telegram_tag"],
                        context.user_data["new_role"], context.user_data["new_phone"])
        if user is None:
            await update.message.reply_text("❌ Користувач із таким TelegramTag вже існує.")
            return

        role = context.user_data["new_role"]
        success = False

        if role == "student":
            success = add_student(db, user.UserID, context.user_data["new_group"],
                                  context.user_data["new_admission_year"], context.user_data["new_specialty"])
        elif role == "teacher":
            success = add_teacher(db, user.UserID, context.user_data["new_email"], context.user_data["new_department"])

        if success:
            await update.message.reply_text(f"✅ Користувач {user.UserName} (@{user.TelegramTag}) успішно доданий як {role}!")
        else:
            await update.message.reply_text(f"❌ Помилка при додаванні {role}.")

    context.user_data.clear()

async def prompt_user_details(update: Update, context: CallbackContext):
    context.user_data["state"] = WAITING_FOR_USER_ROLE  # Перевірте, що цей рядок є у функції
    await update.message.reply_text("Виберіть роль нового користувача: student або teacher")