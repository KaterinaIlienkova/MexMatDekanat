from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List

class DepartmentRepository(BaseRepository):

    def get_departments(self):
        """Отримує список всіх кафедр."""
        departments = self.session.query(Department.Name).all()
        return [dept[0] for dept in departments]
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