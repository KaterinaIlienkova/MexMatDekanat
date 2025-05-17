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
from source.repositories.UnitOfWork import UnitOfWork
from source.services.AnnouncementService import AnnouncementService
from source.services.AuthService import AuthService
from source.services.CourseService import CourseService
from source.services.DocumentService import DocumentService
from source.services.FAQService import FAQService
from source.services.PersonalQAService import PersonalQAService


def create_unit_of_work_factory(db_manager):
    """Створює фабрику для UnitOfWork."""
    def factory():
        return UnitOfWork(db_manager.get_session)
    return factory


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    db_manager = DatabaseManager(DB_CONFIG)
    uow_factory = create_unit_of_work_factory(db_manager)
    application.bot_data['uow_factory'] = uow_factory

    # Створюємо всі сервіси з використанням UnitOfWork
    document_service = DocumentService(uow_factory)
    faq_service = FAQService(uow_factory)
    course_service = CourseService(uow_factory)
    auth_service = AuthService(uow_factory)
    announcement_service = AnnouncementService(uow_factory)
    pqa_service = PersonalQAService(uow_factory)

    document_controller = DocumentController(application, document_service)
    faq_controller = FAQController(application, faq_service)
    course_controller = CourseController(application, course_service)
    auth_controller = AuthController(application, auth_service)
    announcement_controller = AnnouncementController(application, announcement_service, auth_controller)
    pqa_controller = PersonalQAController(application, pqa_service, auth_service)


    document_controller.register_handlers()
    faq_controller.register_handlers()
    course_controller.register_handlers()
    auth_controller.register_handlers()
    announcement_controller.register_handlers()
    pqa_controller.register_handlers()

    # Створюємо і реєструємо обробники меню
    menu_controller = MenuController(
        application,
        document_controller,
        faq_controller,
        course_controller,
        auth_controller,
        announcement_controller,
        pqa_controller
    )
    menu_controller.register_handlers()

    application.run_polling()


if __name__ == "__main__":
    main()
