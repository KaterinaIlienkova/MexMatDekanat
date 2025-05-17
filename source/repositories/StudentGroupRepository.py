from source.repositories.BaseRepository import BaseRepository

from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List

class StudentGroupRepository(BaseRepository):

    def add_student_group(self, group_name: str, specialty_id: int) -> Optional[int]:
        """Додає нову групу та повертає її ID."""
        try:
            new_group = StudentGroup(
                GroupName=group_name,
                SpecialtyID=specialty_id
            )
            self.session.add(new_group)
            self.session.commit()
            self.session.refresh(new_group)  # щоб отримати GroupID
            return new_group.GroupID
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding student group: {e}")
            return None

    def get_all_student_groups(self) -> list[dict]:
        """
        Отримує список всіх груп студентів.

        Returns:
            Список груп студентів з їх деталями
        """
        try:
            groups = self.session.query(
                StudentGroup.GroupID,
                StudentGroup.GroupName,
                Specialty.Name.label("specialty_name")
            ).join(
                Specialty,
                StudentGroup.SpecialtyID == Specialty.SpecialtyID,
                isouter=True
            ).all()

            groups_list = []
            for group in groups:
                group_dict = {
                    "group_id": group.GroupID,
                    "group_name": group.GroupName,
                    "specialty": group.specialty_name if group.specialty_name else "Не вказано"
                }
                groups_list.append(group_dict)

            return groups_list
        except Exception as e:
            logger.exception(f"Помилка при отриманні груп студентів: {str(e)}")
            return []


    def get_groups_by_admission_year(self, admission_year):
        """Отримує список груп студентів за роком вступу."""
        groups = self.session.query(StudentGroup.GroupName) \
            .join(Student, Student.GroupID == StudentGroup.GroupID) \
            .filter(Student.AdmissionYear == admission_year) \
            .distinct() \
            .all()
        return [group[0] for group in groups]

    def get_student_group_by_name(self, group_name: str) -> Optional[StudentGroup]:
        """Отримує групу за назвою."""
        try:
            return self.session.query(StudentGroup).filter_by(GroupName=group_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting student group by name: {e}")
            return None

