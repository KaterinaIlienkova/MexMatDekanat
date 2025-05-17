from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List

class SpecialtyRepository(BaseRepository):
    def get_specialty_by_name(self, specialty_name: str) -> Optional[Specialty]:
        """Отримує спеціальність за назвою."""
        try:
            return self.session.query(Specialty).filter_by(Name=specialty_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting specialty by name: {e}")
            return None

    def add_specialty(self, specialty_name: str) -> Optional[Specialty]:
        """Додає нову спеціальність."""
        try:
            new_specialty = Specialty(Name=specialty_name)
            self.session.add(new_specialty)
            self.session.commit()
            return new_specialty
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding specialty: {e}")
            return None