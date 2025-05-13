from telegram.ext import ApplicationBuilder

from source.config import DB_CONFIG, BOT_TOKEN
from source.controllers.AnnouncementController import AnnouncementController
from source.controllers.AuthController import AuthController
from source.controllers.CourseController import CourseController
from source.controllers.DocumentController import DocumentController
from source.controllers.FAQController import FAQController
from source.controllers.MenuController import MenuController
from source.controllers.PersonalQAController import PersonalQAController
from source.database import DatabaseManager
from source.repositories.AnnouncementRepository import AnnouncementRepository
from source.repositories.AuthRepository import AuthRepository
from source.repositories.CourseRepository import CourseRepository
from source.repositories.DocumentRequestRepository import DocumentRequestRepository
from source.repositories.DocumentTypeRepository import DocumentTypeRepository
from source.repositories.FAQRepository import FAQRepository
from source.repositories.PersonalQARepository import PersonalQARepository
from source.services.AnnouncementService import AnnouncementService
from source.services.AuthService import AuthService
from source.services.CourseService import CourseService
from source.services.DocumentService import DocumentService
from source.services.FAQService import FAQService
from source.services.PersonalQAService import PersonalQAService


def setup_document_service(db_manager):

    document_type_repo = DocumentTypeRepository(db_manager.get_session)
    document_request_repo = DocumentRequestRepository(db_manager.get_session)
    auth_repository = AuthRepository(db_manager.get_session)

    document_service = DocumentService(auth_repository, document_type_repo, document_request_repo)

    return document_service

def setup_faq_service(db_manager):
    """Налаштовує сервіс FAQ."""
    faq_repository = FAQRepository(db_manager.get_session)
    faq_service = FAQService(faq_repository)

    return faq_service

def setup_course_service(db_manager):
    """Налаштовує сервіс FAQ."""
    course_repository = CourseRepository(db_manager.get_session)
    announcement_repository = AnnouncementRepository(db_manager.get_session)
    course_service = CourseService(course_repository, announcement_repository)

    return course_service


def setup_auth_service(db_manager):
    auth_repository = AuthRepository(db_manager.get_session)
    auth_service=AuthService(auth_repository)
    return  auth_service

def setup_pqa_service(db_manager):
    pqa_repository = PersonalQARepository(db_manager.get_session)
    pqa_service=PersonalQAService(pqa_repository)
    return  pqa_service

def setup_announcement_service(db_manager):
    announcement_repository = AnnouncementRepository(db_manager.get_session)
    announcement_service = AnnouncementService(announcement_repository)
    return announcement_service


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    db_manager = DatabaseManager(DB_CONFIG)

    document_service = setup_document_service(db_manager)
    faq_service = setup_faq_service(db_manager)
    course_service = setup_course_service(db_manager)
    auth_service = setup_auth_service(db_manager)
    announcement_service=setup_announcement_service(db_manager)
    pqa_service = setup_pqa_service(db_manager)

    document_controller = DocumentController(application, document_service)
    faq_controller = FAQController(application, faq_service)
    course_controller = CourseController(application,course_service)
    auth_controller= AuthController(application,auth_service)
    announcement_controller = AnnouncementController(application,announcement_service)
    pqa_controller = PersonalQAController(application,pqa_service,auth_service)

    menu_controller = MenuController(application, document_controller, faq_controller, course_controller,auth_controller, announcement_controller,pqa_controller)
    menu_controller.register_handlers()

    application.run_polling()

if __name__ == "__main__":
    main()
