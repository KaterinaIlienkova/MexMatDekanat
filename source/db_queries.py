from typing import Any, List, Tuple

from sqlalchemy.orm import Session, InstrumentedAttribute
from sqlalchemy import text, Row
import logging
from telegram import Update
from telegram.ext import CallbackContext
from source.models import User, Student, Teacher
from source.database import SessionLocal
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from source.models import Student, StudentGroup, Department, Teacher, User

def get_groups_by_admission_years(session: Session, admission_years: list[int]) -> list[Row[tuple[Any, Any, Any]]] | list[Any]:
    try:
        groups = (
            session.query(StudentGroup.GroupID, StudentGroup.GroupName, Student.AdmissionYear)
            .join(Student, StudentGroup.GroupID == Student.GroupID)
            .filter(Student.AdmissionYear.in_(admission_years))
            .distinct()
            .order_by(Student.AdmissionYear, StudentGroup.GroupName)
            .all()
        )
        return groups
    except Exception as e:
        logger.exception(f"Помилка при отриманні груп за роками вступу: {e}")
        return []


def get_all_departments(session: Session) -> list[Row[tuple[Any, Any]]] | list[Any]:
    """
    Отримує список всіх кафедр.
    """
    try:
        return session.query(Department.DepartmentID, Department.Name).order_by(Department.Name).all()
    except Exception as e:
        logger.exception(f"Помилка при отриманні списку кафедр: {e}")
        return []

def get_teachers_by_departments(session: Session, department_ids: list[int]) -> list[Row[tuple[Any, Any, Any, Any]]] | list[Any]:
    """
    Отримує список викладачів за кафедрами.
    """
    try:
        teachers = (
            session.query(Teacher.TeacherID, User.UserName, Department.DepartmentID, Department.Name)
            .join(User)
            .join(Department)
            .filter(Teacher.DepartmentID.in_(department_ids))
            .order_by(Department.Name, User.UserName)
            .all()
        )
        return teachers
    except Exception as e:
        logger.exception(f"Помилка при отриманні викладачів за кафедрами: {e}")
        return []

def get_chat_ids_by_groups(session: Session, group_ids: list[int]) -> list[InstrumentedAttribute] | list[Any]:
    """Отримує ChatID всіх студентів з вказаних груп."""
    try:
        return (
            session.query(User.ChatID)
            .join(Student)
            .filter(Student.GroupID.in_(group_ids), User.ChatID.isnot(None))
            .all()
        )
    except Exception as e:
        logger.exception(f"Помилка при отриманні ChatID за групами: {e}")
        return []

def get_chat_ids_by_admission_years(session: Session, admission_years: list[int]) -> list[InstrumentedAttribute] | list[Any]:
    """Отримує ChatID всіх студентів з вказаних років вступу."""
    try:
        return (
            session.query(User.ChatID)
            .join(Student)
            .filter(Student.AdmissionYear.in_(admission_years), User.ChatID.isnot(None))
            .all()
        )
    except Exception as e:
        logger.exception(f"Помилка при отриманні ChatID за роками вступу: {e}")
        return []

def get_chat_ids_by_teachers(session: Session, teacher_ids: list[int]) -> list[InstrumentedAttribute] | list[Any]:
    """Отримує ChatID вказаних викладачів."""
    try:
        return (
            session.query(User.ChatID)
            .join(Teacher)
            .filter(Teacher.TeacherID.in_(teacher_ids), User.ChatID.isnot(None))
            .all()
        )
    except Exception as e:
        logger.exception(f"Помилка при отриманні ChatID викладачів: {e}")
        return []

def get_chat_ids_by_departments(session: Session, department_ids: list[int]) -> list[InstrumentedAttribute] | list[Any]:
    """Отримує ChatID всіх викладачів з вказаних кафедр."""
    try:
        return (
            session.query(User.ChatID)
            .join(Teacher)
            .filter(Teacher.DepartmentID.in_(department_ids), User.ChatID.isnot(None))
            .all()
        )
    except Exception as e:
        logger.exception(f"Помилка при отриманні ChatID за кафедрами: {e}")
        return []

