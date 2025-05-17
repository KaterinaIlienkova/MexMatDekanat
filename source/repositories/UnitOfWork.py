
from source.repositories.AnnouncementRepository import AnnouncementRepository
from source.repositories.AuthRepository import AuthRepository
from source.repositories.CourseRepository import CourseRepository
from source.repositories.DepartmentRepository import DepartmentRepository
from source.repositories.DocumentRequestRepository import DocumentRequestRepository
from source.repositories.DocumentTypeRepository import DocumentTypeRepository
from source.repositories.FAQRepository import FAQRepository
from source.repositories.PersonalQARepository import PersonalQARepository
from source.repositories.SpecialtyRepository import SpecialtyRepository
from source.repositories.StudentRepository import StudentRepository
from source.repositories.TeacherRepository import TeacherRepository
from source.repositories.StudentGroupRepository import StudentGroupRepository



class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session = None

        # Репозиторії (ініціалізуються як None)
        self.document_type_repository = None
        self.document_request_repository = None
        self.course_repository = None
        self.announcement_repository = None
        self.auth_repository = None
        self.faq_repository = None
        self.pqa_repository = None

        self.student_repository=None
        self.teacher_repository = None
        self.department_repository = None
        self.studentGroup_repository=None
        self.specialty_repository=None


    def __enter__(self):
        self._session = self.session_factory()

        # Ініціалізація репозиторіїв спільною сесією
        self.document_type_repository = DocumentTypeRepository(self._session)
        self.document_request_repository = DocumentRequestRepository(self._session)
        self.course_repository = CourseRepository(self._session)
        self.announcement_repository = AnnouncementRepository(self._session)
        self.auth_repository = AuthRepository(self._session)
        self.faq_repository= FAQRepository(self._session)
        self.pqa_repository= PersonalQARepository(self._session)

        self.student_repository=StudentRepository(self._session)
        self.teacher_repository = TeacherRepository(self._session)
        self.department_repository = DepartmentRepository(self._session)
        self.studentGroup_repository= StudentGroupRepository(self._session)
        self.specialty_repository=SpecialtyRepository(self._session)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Якщо виникла помилка - відкочуємо транзакцію
            self.rollback()
        else:
            # В разі успішного виконання - зберігаємо зміни
            self.commit()

        # В будь-якому випадку - закриваємо сесію
        self._session.close()

    def commit(self):
        """Зберігає всі зміни, зроблені в транзакції"""
        self._session.commit()

    def rollback(self):
        """Відкочує всі зміни, зроблені в транзакції"""
        self._session.rollback()