from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List, Dict, Any


class DepartmentRepository(BaseRepository):


    def get_all_departments(self) -> List[Dict[str, Any]]:
        """Отримати список всіх кафедр для вибору розсилки."""
        try:
            departments = self.session.query(
                Department.DepartmentID,
                Department.Name
            ).all()

            return [
                {
                    'department_id': d.DepartmentID,
                    'name': d.Name
                }
                for d in departments
            ]
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting all departments: {e}")
            return []


    def get_department_by_name(self, department_name: str) -> Optional[Department]:
        """Отримує департамент за назвою."""
        try:
            return self.session.query(Department).filter_by(Name=department_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting department by name: {e}")
            return None

    def add_department(self, department_name: str) -> Optional[Department]:
        """Додає новий департамент."""
        try:
            new_department = Department(Name=department_name)
            self.session.add(new_department)
            self.session.commit()
            return new_department
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding department: {e}")
            return None